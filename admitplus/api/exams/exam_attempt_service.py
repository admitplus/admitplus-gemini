import logging
import traceback
from datetime import datetime

from .exam_attempt_repo import ExamAttemptRepo
from .exam_attempt_schema import (
    StudentAnswer,
    AttemptMetadata,
    AttemptCreateRequest,
    AttemptItem,
    AttemptResponse,
    AttemptListResponse,
)
from .exam_task_schema import TaskPrompt
from .exam_model import AttemptModeEnum
from admitplus.api.exams.exam_task_service import TaskService
from admitplus.llm.providers.openai.openai_client import extract_text_from_image
from admitplus.utils.crypto_utils import generate_uuid


class AttemptService:
    def __init__(self):
        self.attempt_repo = ExamAttemptRepo()

    async def create_attempt(
        self, student_id: str, request: AttemptCreateRequest
    ) -> AttemptResponse:
        try:
            attempt_id = generate_uuid()
            task_id = request.task_id
            _task = await TaskService().get_task(task_id=task_id)
            logging.info(
                f"""[AttemptService] [CreateAttempt] Starting - attempt_id={attempt_id}, student_id={student_id}, task_id={task_id}, mode={request.mode}"""
            )

            # Prepare student_answer data - exclude None values
            student_answer_data = request.student_answer.model_dump(exclude_none=True)

            # Prepare metadata data - only include if time_spent_seconds is provided
            metadata_data = (
                {"time_spent_seconds": request.metadata.time_spent_seconds}
                if request.metadata and request.metadata.time_spent_seconds is not None
                else None
            )

            now = datetime.utcnow()
            attempt_doc = {
                "attempt_id": attempt_id,
                "task_id": task_id,
                "student_id": student_id,
                "exam": _task.exam,
                "section": _task.section,
                "task_prompt": _task.prompt.model_dump(),
                "task_type": _task.task_type,
                "mode": request.mode.lower(),
                "student_answer": student_answer_data,
                "metadata": metadata_data,
                "created_at": now,
                "updated_at": now,
            }

            # Create attempt in repository
            created_attempt_doc = await self.attempt_repo.create_attempt(attempt_doc)
            if not created_attempt_doc:
                raise ValueError(f"Failed to create attempt: {attempt_id}")

            # Build response from created document
            metadata_doc = created_attempt_doc.get("metadata")
            task_prompt_doc = created_attempt_doc.get(
                "task_prompt", _task.prompt.model_dump()
            )

            # Extract datetime fields from created document (ensured to exist by attempt_doc and repo)
            created_at_value = created_attempt_doc.get("created_at", now)
            updated_at_value = created_attempt_doc.get("updated_at", now)

            attempt_response = AttemptResponse(
                task_id=task_id,
                attempt_id=created_attempt_doc.get("attempt_id", attempt_id),
                exam=created_attempt_doc.get("exam", _task.exam).lower(),
                section=created_attempt_doc.get("section", _task.section).lower(),
                task_type=created_attempt_doc.get("task_type", _task.task_type).lower(),
                task_prompt=TaskPrompt(**task_prompt_doc),
                mode=created_attempt_doc.get("mode", request.mode.lower()),
                student_id=created_attempt_doc.get("student_id", student_id),
                student_answer=StudentAnswer(**student_answer_data),
                metadata=AttemptMetadata(
                    time_spent_seconds=metadata_doc["time_spent_seconds"]
                )
                if metadata_doc
                else None,
                created_at=created_at_value,
                updated_at=updated_at_value,
            )

            logging.info(
                f"""[AttemptService] [CreateAttempt] Successfully created attempt: {attempt_id} (exam={_task.exam}, section={_task.section})"""
            )
            return attempt_response
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"""[AttemptService] [CreateAttempt] Error creating attempt: {str(e)}"""
            )
            logging.error(
                f"""[AttemptService] [CreateAttempt] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_attempt(self, attempt_id: str) -> AttemptResponse:
        try:
            logging.info(
                f"""[AttemptService] [GetAttempt] Starting - attempt_id={attempt_id}"""
            )

            attempt_doc = await self.attempt_repo.get_attempt_by_id(
                attempt_id=attempt_id
            )

            if not attempt_doc:
                logging.warning(
                    f"""[AttemptService] [GetAttempt] Attempt not found: {attempt_id}"""
                )
                raise ValueError(f"Attempt not found: {attempt_id}")

            logging.debug(
                f"""[AttemptService] [GetAttempt] Retrieved attempt document from repository: {attempt_id}"""
            )

            # Extract student_answer data
            student_answer_data = attempt_doc.get("student_answer", {})
            if not isinstance(student_answer_data, dict):
                logging.warning(
                    f"""[AttemptService] [GetAttempt] Invalid student_answer data type for attempt {attempt_id}, expected dict, got {type(student_answer_data)}"""
                )
                student_answer_data = {}

            # Extract task_prompt data
            task_prompt_data = attempt_doc.get("task_prompt", {})
            if not isinstance(task_prompt_data, dict):
                logging.warning(
                    f"""[AttemptService] [GetAttempt] Invalid task_prompt data type for attempt {attempt_id}, expected dict, got {type(task_prompt_data)}"""
                )
                task_prompt_data = {}

            # Extract metadata data
            metadata_data = attempt_doc.get("metadata")

            # Extract datetime fields from database document
            created_at_value = attempt_doc.get("created_at")
            updated_at_value = attempt_doc.get("updated_at", created_at_value)

            if not isinstance(created_at_value, datetime):
                logging.error(
                    f"""[AttemptService] [GetAttempt] Invalid created_at type: {type(created_at_value)} for attempt {attempt_id}"""
                )
                raise ValueError(f"Invalid created_at field in attempt document")

            if updated_at_value and not isinstance(updated_at_value, datetime):
                logging.error(
                    f"""[AttemptService] [GetAttempt] Invalid updated_at type: {type(updated_at_value)} for attempt {attempt_id}"""
                )
                raise ValueError(f"Invalid updated_at field in attempt document")

            logging.debug(
                f"""[AttemptService] [GetAttempt] Extracted data - text: {bool(student_answer_data.get("text"))}, audio_url: {bool(student_answer_data.get("audio_url"))}, selected_options: {bool(student_answer_data.get("selected_options"))}"""
            )

            attempt_response = AttemptResponse(
                attempt_id=attempt_doc.get("attempt_id", attempt_id),
                exam=attempt_doc.get("exam", "").lower(),
                section=attempt_doc.get("section", "").lower(),
                task_type=attempt_doc.get("task_type", "").lower(),
                task_prompt=TaskPrompt(**task_prompt_data),
                mode=attempt_doc.get("mode", AttemptModeEnum.PRACTICE.value),
                student_id=attempt_doc.get("student_id", ""),
                student_answer=StudentAnswer(
                    text=student_answer_data.get("text"),
                    audio_url=student_answer_data.get("audio_url"),
                    selected_options=student_answer_data.get("selected_options"),
                ),
                metadata=AttemptMetadata(
                    time_spent_seconds=metadata_data.get("time_spent_seconds")
                    if metadata_data
                    else None
                )
                if metadata_data
                else None,
                created_at=created_at_value,
                updated_at=updated_at_value,
            )

            logging.info(
                f"""[AttemptService] [GetAttempt] Successfully processed attempt: {attempt_id} (exam={attempt_response.exam}, section={attempt_response.section})"""
            )

            return attempt_response
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"""[AttemptService] [GetAttempt] Error processing attempt {attempt_id}: {str(e)}"""
            )
            logging.error(
                f"""[AttemptService] [GetAttempt] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def list_attempts(
        self, student_id: str, task_id: str, page: int = 1, page_size: int = 20
    ) -> AttemptListResponse:
        try:
            logging.info(
                f"""[AttemptService] [ListAttempts] Starting - student_id={student_id}, task_id={task_id}, page={page}, page_size={page_size}"""
            )

            attempts_data, total = await self.attempt_repo.list_attempts(
                student_id=student_id, task_id=task_id, page=page, page_size=page_size
            )

            attempt_items = []
            for attempt_doc in attempts_data:
                try:
                    attempt_id = attempt_doc.get("attempt_id")

                    # Extract created_at from database document
                    created_at_value = attempt_doc.get("created_at")
                    if not isinstance(created_at_value, datetime):
                        logging.warning(
                            f"""[AttemptService] [ListAttempts] Invalid created_at type: {type(created_at_value)} for attempt {attempt_id}, skipping"""
                        )
                        continue

                    # Extract student_answer data
                    student_answer_data = attempt_doc.get("student_answer", {})
                    if not isinstance(student_answer_data, dict):
                        student_answer_data = {}

                    # Extract task_prompt data
                    task_prompt_data = attempt_doc.get("task_prompt", {})
                    if not isinstance(task_prompt_data, dict):
                        task_prompt_data = {}

                    attempt_items.append(
                        AttemptItem(
                            attempt_id=attempt_doc.get("attempt_id", attempt_id),
                            exam=attempt_doc.get("exam", "").lower(),
                            section=attempt_doc.get("section", "").lower(),
                            task_type=attempt_doc.get("task_type", "").lower(),
                            task_prompt=TaskPrompt(**task_prompt_data),
                            mode=attempt_doc.get(
                                "mode", AttemptModeEnum.PRACTICE.value
                            ),
                            student_id=attempt_doc.get("student_id", student_id),
                            student_answer=StudentAnswer(
                                text=student_answer_data.get("text"),
                                audio_url=student_answer_data.get("audio_url"),
                                selected_options=student_answer_data.get(
                                    "selected_options"
                                ),
                            ),
                            created_at=created_at_value,
                        )
                    )
                except Exception as e:
                    logging.warning(
                        f"""[AttemptService] [ListAttempts] Skipping invalid attempt document: {str(e)}"""
                    )
                    continue

            logging.info(
                f"""[AttemptService] [ListAttempts] Retrieved {len(attempt_items)}/{total} attempts (student_id={student_id}, task_id={task_id}, page={page})"""
            )

            return AttemptListResponse(
                items=attempt_items, page=page, page_size=page_size, total=total
            )
        except Exception as e:
            logging.error(
                f"""[AttemptService] [ListAttempts] Error retrieving attempts - student_id={student_id}, task_id={task_id}, page={page}, page_size={page_size}, error: {str(e)}"""
            )
            logging.error(
                f"""[AttemptService] [ListAttempts] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def list_student_attempts(
        self, student_id: str, page: int = 1, page_size: int = 20
    ) -> AttemptListResponse:
        try:
            logging.info(
                f"""[AttemptService] [ListStudentAttempts] Starting - student_id={student_id}, page={page}, page_size={page_size}"""
            )

            attempts_data, total = await self.attempt_repo.list_attempts_by_student(
                student_id=student_id, page=page, page_size=page_size
            )

            attempt_items = []
            for attempt_doc in attempts_data:
                try:
                    attempt_id = attempt_doc.get("attempt_id")

                    # Extract created_at from database document
                    created_at_value = attempt_doc.get("created_at")
                    if not isinstance(created_at_value, datetime):
                        logging.warning(
                            f"""[AttemptService] [ListStudentAttempts] Invalid created_at type: {type(created_at_value)} for attempt {attempt_id}, skipping"""
                        )
                        continue

                    # Extract student_answer data
                    student_answer_data = attempt_doc.get("student_answer", {})
                    if not isinstance(student_answer_data, dict):
                        student_answer_data = {}

                    # Extract task_prompt data
                    task_prompt_data = attempt_doc.get("task_prompt", {})
                    if not isinstance(task_prompt_data, dict):
                        task_prompt_data = {}

                    attempt_items.append(
                        AttemptItem(
                            task_id=attempt_doc.get("task_id", "").lower(),
                            attempt_id=attempt_doc.get("attempt_id", attempt_id),
                            exam=attempt_doc.get("exam", "").lower(),
                            section=attempt_doc.get("section", "").lower(),
                            task_type=attempt_doc.get("task_type", "").lower(),
                            task_prompt=TaskPrompt(**task_prompt_data),
                            mode=attempt_doc.get(
                                "mode", AttemptModeEnum.PRACTICE.value
                            ),
                            student_id=attempt_doc.get("student_id", student_id),
                            student_answer=StudentAnswer(
                                text=student_answer_data.get("text"),
                                audio_url=student_answer_data.get("audio_url"),
                                selected_options=student_answer_data.get(
                                    "selected_options"
                                ),
                            ),
                            created_at=created_at_value,
                        )
                    )
                except Exception as e:
                    logging.warning(
                        f"""[AttemptService] [ListStudentAttempts] Skipping invalid attempt document: {str(e)}"""
                    )
                    continue

            logging.info(
                f"""[AttemptService] [ListStudentAttempts] Retrieved {len(attempt_items)}/{total} attempts (student_id={student_id}, page={page})"""
            )

            return AttemptListResponse(
                items=attempt_items, page=page, page_size=page_size, total=total
            )
        except Exception as e:
            logging.error(
                f"""[AttemptService] [ListStudentAttempts] Error retrieving attempts - student_id={student_id}, page={page}, page_size={page_size}, error: {str(e)}"""
            )
            logging.error(
                f"""[AttemptService] [ListStudentAttempts] Traceback: {traceback.format_exc()}"""
            )
            raise
