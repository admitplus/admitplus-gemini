import os
import logging
from datetime import datetime
from typing import Optional

from admitplus.llm.prompts.gpt_prompts.essay_prompt.generate_essay_prompt import (
    build_generate_essay_prompt,
)
from admitplus.llm.prompts.gpt_prompts.essay_prompt.generate_essay_question_prompt import (
    build_generate_essay_question_prompt,
)
from admitplus.llm.providers.openai.openai_client import generate_text
from admitplus.llm.llm_utils import parse_llm_json_response
from .essay_repo import EssayRepo
from admitplus.api.student.application.application_repo import ApplicationRepo
from admitplus.api.universities.information_repo import InformationRepo
from .essay_draft_schema import (
    EssayDraftListResponse,
    EssayDraftResponse,
    EssayDraftCreateRequest,
)
from .essay_schema import (
    EssayDetailResponse,
    EssayCreateRequest,
    EssayConfig,
    EssayListResponse,
    EssayUpdateRequest,
    EssayQuestionListResponse,
    EssayQuestionResponse,
)
from .essay_record_schema import (
    EssayGenerateRequest,
    EssayRecordDetailResponse,
    EssayRecordListResponse,
)
from admitplus.api.analysis.analysis_schema import EssayStatus
from admitplus.utils.crypto_utils import generate_uuid


class EssayService:
    def __init__(self):
        self.db_name = os.environ.get("MONGO_APPLICATION_WAREHOUSE_DB_NAME")

        self.essay_repo = EssayRepo()
        self.application_repo = ApplicationRepo()
        self.information_repo = InformationRepo()
        logging.info(f"[EssayService] Initialized with db_name={self.db_name}")

    # ============================================================================
    # Essay CRUD Operations
    # ============================================================================

    async def _get_university_logo(self, application_id: str) -> Optional[str]:
        """
        Helper method to fetch university logo URL from application_id
        """
        try:
            application_data = await self.application_repo.find_application_by_id(
                application_id
            )
            if not application_data:
                return None

            university_id = application_data.get("university_id")
            if not university_id:
                return None

            university_profile = await self.information_repo.find_university_by_id(
                university_id
            )
            if not university_profile:
                return None

            # Try common logo field names
            university_logo = university_profile.get("logo_url")

            return university_logo
        except Exception as e:
            logging.warning(
                f"[EssayService] [_GetUniversityLogo] Failed to get university logo for application_id={application_id}: {e}"
            )
            return None

    async def create_essay(
        self, request: EssayCreateRequest, application_id: str, user_id: str
    ) -> EssayDetailResponse:
        """
        Create a new essay for an application
        """
        now = datetime.utcnow()
        essay_id = generate_uuid()
        student_id = request.student_id  # Get student_id from request

        logging.info(
            f"[EssayService] [CreateEssay] Creating essay for application_id={application_id}, student_id={student_id}, user_id={user_id}"
        )

        try:
            # Build essay document
            essay_document = {
                "essay_id": essay_id,
                "student_id": student_id,
                "application_id": application_id,
                "essay_type": request.essay_type,
                "prompt_text": request.prompt_text,
                "config": request.config.model_dump() if request.config else {},
                "status": "draft",
                "final_draft_id": None,
                "created_by_member_id": user_id,  # user_id can be teacher or student
                "created_at": now,
                "updated_at": now,
            }

            insert_id = await self.essay_repo.create_essay(essay_document)
            logging.info(
                f"[EssayService] [CreateEssay] Successfully created essay with id={insert_id}"
            )

            logging.info(
                f"[EssayService] [CreateEssay] Essay created successfully for student_id={student_id}, essay_id={essay_id}"
            )

            # Fetch university logo
            university_logo = await self._get_university_logo(application_id)

            # Return EssayDetailResponse
            return EssayDetailResponse(
                essay_id=essay_id,
                student_id=student_id,
                application_id=application_id,
                essay_type=request.essay_type,
                prompt_text=request.prompt_text,
                config=request.config if request.config else EssayConfig(),
                status="draft",
                final_draft_id=None,
                created_by_member_id=user_id,  # user_id can be teacher or student
                university_logo=university_logo,
                created_at=now,
                updated_at=now,
            )

        except Exception as e:
            logging.error(
                f"[EssayService] [CreateEssay] Failed to create essay for student_id={student_id}, essay_id={essay_id}: {e}"
            )
            raise

    async def get_application_essays(self, application_id: str) -> EssayListResponse:
        """
        Get all essays for a given application_id
        """
        logging.info(
            f"[EssayService] [GetApplicationEssays] Fetching essays for application_id={application_id}"
        )

        try:
            essay_documents = await self.essay_repo.find_many_application_essays(
                application_id
            )

            # Fetch university logo (shared across all essays for this application)
            university_logo = await self._get_university_logo(application_id)

            essay_items = []
            for doc in essay_documents:
                # Handle config field - ensure it's a dict (could be None in old data)
                config_data = doc.get("config") or {}
                config = EssayConfig(**config_data)

                essay_item = EssayDetailResponse(
                    essay_id=doc.get("essay_id"),
                    student_id=doc.get("student_id"),
                    application_id=doc.get("application_id"),
                    essay_type=doc.get("essay_type"),
                    prompt_text=doc.get("prompt_text", ""),
                    config=config,
                    status=doc.get("status", "draft"),
                    final_draft_id=doc.get("final_draft_id"),
                    created_by_member_id=doc.get("created_by_member_id"),
                    university_logo=university_logo,
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                )
                essay_items.append(essay_item)
            logging.info(
                f"[EssayService] [GetApplicationEssays] Successfully retrieved {len(essay_items)} essay(s) for application_id={application_id}"
            )
            return EssayListResponse(items=essay_items)
        except Exception as e:
            logging.error(
                f"[EssayService] [GetApplicationEssays] Failed to get essays for application_id={application_id}: {e}"
            )
            raise

    async def get_essay_detail(self, essay_id: str) -> EssayDetailResponse:
        """
        Get specific essay by ID
        """
        logging.info(
            f"[EssayService] [GetEssayDetail] Fetching essay for essay_id={essay_id}"
        )

        try:
            essay_document = await self.essay_repo.get_essay_by_id(essay_id)

            if not essay_document:
                logging.warning(
                    f"[EssayService] [GetEssayDetail] Essay not found for essay_id={essay_id}"
                )
                raise ValueError(f"Essay not found for essay_id={essay_id}")

            # Handle config field - ensure it's a dict (could be None in old data)
            config_data = essay_document.get("config") or {}
            config = EssayConfig(**config_data)

            # Fetch university logo
            application_id = essay_document.get("application_id")
            university_logo = (
                await self._get_university_logo(application_id)
                if application_id
                else None
            )

            essay_detail = EssayDetailResponse(
                essay_id=essay_document.get("essay_id"),
                student_id=essay_document.get("student_id"),
                application_id=essay_document.get("application_id"),
                essay_type=essay_document.get("essay_type"),
                prompt_text=essay_document.get("prompt_text", ""),
                config=config,
                status=essay_document.get("status", "draft"),
                final_draft_id=essay_document.get("final_draft_id"),
                created_by_member_id=essay_document.get("created_by_member_id"),
                university_logo=university_logo,
                created_at=essay_document.get("created_at"),
                updated_at=essay_document.get("updated_at"),
            )

            logging.info(
                f"[EssayService] [GetEssayDetail] Successfully retrieved essay for essay_id={essay_id}"
            )
            return essay_detail

        except Exception as e:
            logging.error(
                f"[EssayService] [GetEssayDetail] Failed to get essay by id for essay_id={essay_id}: {e}"
            )
            raise

    async def update_essay_by_id(
        self, essay_id: str, essay_data: EssayUpdateRequest
    ) -> EssayDetailResponse:
        """
        Update essay by essay_id
        """
        logging.info(
            f"[EssayService] [UpdateEssayById] Updating essay for essay_id={essay_id}"
        )

        try:
            # Build update data dictionary from request
            update_data = {}

            if essay_data.essay_type is not None:
                update_data["essay_type"] = essay_data.essay_type
            if essay_data.prompt_text is not None:
                update_data["prompt_text"] = essay_data.prompt_text
            if essay_data.config is not None:
                update_data["config"] = essay_data.config.model_dump()
            if essay_data.status is not None:
                update_data["status"] = essay_data.status
            if essay_data.final_draft_id is not None:
                update_data["final_draft_id"] = essay_data.final_draft_id

            if not update_data:
                logging.warning(
                    f"[EssayService] [UpdateEssayById] No fields to update for essay_id={essay_id}"
                )
                # Return existing essay if no updates
                return await self.get_essay_detail(essay_id)

            # Update essay in database
            modified_count = await self.essay_repo.update_essay(essay_id, update_data)

            if modified_count == 0:
                logging.warning(
                    f"[EssayService] [UpdateEssayById] No essay found to update for essay_id={essay_id}"
                )
                raise ValueError(f"Essay not found for essay_id={essay_id}")

            # Return updated essay
            updated_essay = await self.get_essay_detail(essay_id)
            logging.info(
                f"[EssayService] [UpdateEssayById] Successfully updated essay for essay_id={essay_id}"
            )
            return updated_essay

        except Exception as e:
            logging.error(
                f"[EssayService] [UpdateEssayById] Failed to update essay for essay_id={essay_id}: {e}"
            )
            raise

    async def finalize_essay(
        self, essay_id: str, final_draft_id: str
    ) -> EssayDetailResponse:
        """
        Finalize essay by setting final_draft_id and status
        """
        logging.info(
            f"[EssayService] [FinalizeEssay] Finalizing essay for essay_id={essay_id}"
        )

        try:
            # Update essay with final_draft_id and status
            modified_count = await self.essay_repo.update_essay(
                essay_id,
                {"final_draft_id": final_draft_id, "status": EssayStatus.FINALIZED},
            )

            if modified_count == 0:
                logging.warning(
                    f"[EssayService] [FinalizeEssay] No essay found to finalize for essay_id={essay_id}"
                )
                raise ValueError(f"Essay not found for essay_id={essay_id}")

            # Return updated essay
            updated_essay = await self.get_essay_detail(essay_id)
            logging.info(
                f"[EssayService] [FinalizeEssay] Successfully finalized essay for essay_id={essay_id}"
            )
            return updated_essay

        except Exception as e:
            logging.error(
                f"[EssayService] [FinalizeEssay] Failed to finalize essay for essay_id={essay_id}: {e}"
            )
            raise

    async def generate_essay_question_list(self, essay_id, request, student_id):
        """
        Generate essay questions based on university, degree, title, and description
        """
        logging.info(
            f"[EssayService] [GenerateEssayQuestionList] Generating questions for essay_id={essay_id}, student_id={student_id}"
        )

        try:
            # Access request as Pydantic model attributes
            university_name = request.university_name
            degree = request.degree
            title = request.title
            description = request.description

            # Build prompt and call LLM
            prompt = build_generate_essay_question_prompt(
                university_name, degree, title, description
            )
            llm_response = await generate_text(prompt)

            # Parse JSON response
            parsed_response = parse_llm_json_response(
                llm_response, context="[EssayService] [GenerateEssayQuestionList]"
            )

            # Extract question list - handle different response formats
            if isinstance(parsed_response, dict):
                # Try common keys for question list
                if "questions" in parsed_response:
                    question_list = parsed_response["questions"]
                elif "question_list" in parsed_response:
                    question_list = parsed_response["question_list"]
                elif "items" in parsed_response:
                    question_list = parsed_response["items"]
                else:
                    # If the dict itself contains question fields, wrap it
                    question_list = [parsed_response]
            elif isinstance(parsed_response, list):
                question_list = parsed_response
            else:
                logging.warning(
                    f"[EssayService] [GenerateEssayQuestionList] Unexpected response format: {type(parsed_response)}"
                )
                question_list = []

            # Create questions in database
            created_questions = []
            now = datetime.utcnow()

            for question_data in question_list:
                # Generate question_id if not present
                question_id = question_data.get("question_id") or generate_uuid()

                # Extract question text - handle different formats
                if isinstance(question_data, dict):
                    question_text = (
                        question_data.get("question")
                        or question_data.get("text")
                        or str(question_data)
                    )
                else:
                    question_text = str(question_data)

                doc = {
                    "question_id": question_id,
                    "student_id": student_id,
                    "essay_id": essay_id,
                    "question": question_text,
                    "answer": "",
                    "created_at": now,
                    "updated_at": now,
                }

                insert_id = await self.essay_repo.create_essay_question(doc)
                logging.info(
                    f"[EssayService] [GenerateEssayQuestionList] Created question with id={insert_id}, question_id={question_id}"
                )

                # Build response item
                question_response = EssayQuestionResponse(
                    question_id=question_id,
                    student_id=student_id,
                    essay_id=essay_id,
                    question=question_text,
                    answer="",
                    created_at=now,
                    updated_at=now,
                )
                created_questions.append(question_response)

            logging.info(
                f"[EssayService] [GenerateEssayQuestionList] Successfully created {len(created_questions)} question(s) for essay_id={essay_id}"
            )
            return EssayQuestionListResponse(items=created_questions)

        except Exception as e:
            logging.error(
                f"[EssayService] [GenerateEssayQuestionList] Failed to generate questions for essay_id={essay_id}: {e}"
            )
            raise

    async def update_essay_question(
        self, question_id: str, question_text: str
    ) -> EssayQuestionResponse:
        """
        Update essay question by question_id
        """
        logging.info(
            f"[EssayService] [UpdateEssayQuestion] Updating question for question_id={question_id}"
        )

        try:
            update_data = {"question": question_text}

            modified_count = await self.essay_repo.update_essay_question(
                question_id, update_data
            )

            if modified_count == 0:
                logging.warning(
                    f"[EssayService] [UpdateEssayQuestion] No question found to update for question_id={question_id}"
                )
                raise ValueError(
                    f"Essay question not found for question_id={question_id}"
                )

            # Get updated question
            updated_question = await self.get_essay_question_by_id(question_id)
            logging.info(
                f"[EssayService] [UpdateEssayQuestion] Successfully updated question for question_id={question_id}"
            )
            return updated_question

        except Exception as e:
            logging.error(
                f"[EssayService] [UpdateEssayQuestion] Failed to update question for question_id={question_id}: {e}"
            )
            raise

    async def get_essay_question_by_id(self, question_id: str) -> EssayQuestionResponse:
        """
        Get specific essay question by question_id
        """
        logging.info(
            f"[EssayService] [GetEssayQuestionById] Fetching question for question_id={question_id}"
        )

        try:
            question_doc = await self.essay_repo.get_essay_question_by_id(question_id)

            if not question_doc:
                logging.warning(
                    f"[EssayService] [GetEssayQuestionById] Question not found for question_id={question_id}"
                )
                raise ValueError(
                    f"Essay question not found for question_id={question_id}"
                )

            question_response = EssayQuestionResponse(
                question_id=question_doc.get("question_id"),
                student_id=question_doc.get("student_id"),
                essay_id=question_doc.get("essay_id"),
                question=question_doc.get("question", ""),
                answer=question_doc.get("answer", ""),
                created_at=question_doc.get("created_at"),
                updated_at=question_doc.get("updated_at"),
            )

            logging.info(
                f"[EssayService] [GetEssayQuestionById] Successfully retrieved question for question_id={question_id}"
            )
            return question_response

        except Exception as e:
            logging.error(
                f"[EssayService] [GetEssayQuestionById] Failed to get question by id for question_id={question_id}: {e}"
            )
            raise

    async def get_essay_questions_by_essay_id(
        self, essay_id: str
    ) -> EssayQuestionListResponse:
        """
        Get all essay questions for a given essay_id
        """
        logging.info(
            f"[EssayService] [GetEssayQuestionsByEssayId] Fetching questions for essay_id={essay_id}"
        )

        try:
            question_documents = await self.essay_repo.get_essay_question_by_essay_id(
                essay_id
            )

            question_items = []
            for doc in question_documents:
                question_item = EssayQuestionResponse(
                    question_id=doc.get("question_id"),
                    student_id=doc.get("student_id"),
                    essay_id=doc.get("essay_id"),
                    question=doc.get("question", ""),
                    answer=doc.get("answer", ""),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                )
                question_items.append(question_item)

            logging.info(
                f"[EssayService] [GetEssayQuestionsByEssayId] Successfully retrieved {len(question_items)} question(s) for essay_id={essay_id}"
            )
            return EssayQuestionListResponse(items=question_items)
        except Exception as e:
            logging.error(
                f"[EssayService] [GetEssayQuestionsByEssayId] Failed to get questions for essay_id={essay_id}: {e}"
            )
            raise

    # ============================================================================
    # Essay Draft Operations
    # ============================================================================

    async def list_essay_drafts(
        self, essay_id: str, page: int = 1, page_size: int = 10
    ) -> EssayDraftListResponse:
        """
        List all essay drafts for a given essay_id with pagination
        """
        logging.info(
            f"[EssayService] [ListEssayDrafts] Fetching drafts for essay_id={essay_id}, page={page}, page_size={page_size}"
        )

        try:
            drafts, total = await self.essay_repo.list_essay_drafts(
                essay_id, page=page, page_size=page_size
            )

            draft_items = []
            for doc in drafts:
                draft_item = EssayDraftResponse(
                    draft_id=doc.get("draft_id"),
                    essay_id=doc.get("essay_id"),
                    version=doc.get("version", 1),
                    text=doc.get("text", ""),
                    generated_by=doc.get("generated_by"),
                    model=doc.get("model"),
                    author_member_id=doc.get("author_member_id"),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                )
                draft_items.append(draft_item)

            has_next = (page * page_size) < total
            has_prev = page > 1

            logging.info(
                f"[EssayService] [ListEssayDrafts] Successfully retrieved {len(draft_items)} draft(s) for essay_id={essay_id}"
            )
            return EssayDraftListResponse(
                items=draft_items,
                total=total,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_prev=has_prev,
            )
        except Exception as e:
            logging.error(
                f"[EssayService] [ListEssayDrafts] Failed to get drafts for essay_id={essay_id}: {e}"
            )
            raise

    async def create_essay_draft(
        self, essay_id: str, request: EssayDraftCreateRequest, user_id: str
    ) -> EssayDraftResponse:
        """
        Create a new essay draft for a given essay_id
        Version will auto-increment based on existing drafts for the same essay_id
        """
        logging.info(
            f"[EssayService] [CreateEssayDraft] Creating draft for essay_id={essay_id}, user_id={user_id}"
        )

        try:
            # Get the maximum version number for this essay_id to auto-increment
            max_version = await self.essay_repo.get_max_version_for_essay(essay_id)
            next_version = max_version + 1

            logging.info(
                f"[EssayService] [CreateEssayDraft] Current max version: {max_version}, next version: {next_version} for essay_id={essay_id}"
            )

            now = datetime.utcnow()
            draft_id = generate_uuid()

            # Build draft document
            draft_document = {
                "draft_id": draft_id,
                "essay_id": essay_id,
                "version": next_version,
                "text": request.text,
                "generated_by": request.generated_by,
                "model": request.model,
                "author_member_id": user_id,
                "created_at": now,
                "updated_at": now,
            }

            insert_id = await self.essay_repo.insert_essay_draft(draft_document)
            logging.info(
                f"[EssayService] [CreateEssayDraft] Successfully created draft with id={insert_id}, draft_id={draft_id}, version={next_version}"
            )

            # Return EssayDraftResponse
            return EssayDraftResponse(
                draft_id=draft_id,
                essay_id=essay_id,
                version=next_version,
                text=request.text,
                generated_by=request.generated_by,
                model=request.model,
                author_member_id=user_id,
                created_at=now,
                updated_at=now,
            )

        except Exception as e:
            logging.error(
                f"[EssayService] [CreateEssayDraft] Failed to create draft for essay_id={essay_id}: {e}"
            )
            raise

    async def get_draft_detail(self, draft_id: str) -> EssayDraftResponse:
        """
        Get specific essay draft by draft_id
        """
        logging.info(
            f"[EssayService] [GetDraftDetail] Fetching draft for draft_id={draft_id}"
        )

        try:
            draft_document = await self.essay_repo.get_draft_by_id(draft_id)

            if not draft_document:
                logging.warning(
                    f"[EssayService] [GetDraftDetail] Draft not found for draft_id={draft_id}"
                )
                raise ValueError(f"Draft not found for draft_id={draft_id}")

            draft_detail = EssayDraftResponse(
                draft_id=draft_document.get("draft_id"),
                essay_id=draft_document.get("essay_id"),
                version=draft_document.get("version", 1),
                text=draft_document.get("text", ""),
                generated_by=draft_document.get("generated_by"),
                model=draft_document.get("model"),
                author_member_id=draft_document.get("author_member_id"),
                created_at=draft_document.get("created_at"),
                updated_at=draft_document.get("updated_at"),
            )

            logging.info(
                f"[EssayService] [GetDraftDetail] Successfully retrieved draft for draft_id={draft_id}"
            )
            return draft_detail

        except Exception as e:
            logging.error(
                f"[EssayService] [GetDraftDetail] Failed to get draft by id for draft_id={draft_id}: {e}"
            )
            raise

    # ============================================================================
    # Essay Record Operations
    # ============================================================================

    async def generate_essay_draft(
        self, essay_id: str, request: EssayGenerateRequest, user_id: str
    ) -> EssayRecordDetailResponse:
        """
        Generate a new essay draft for a given essay_id
        Creates a draft in essay_drafts collection and saves request/response in essay_records collection
        """
        logging.info(
            f"[EssayService] [GenerateEssayDraft] Generating draft for essay_id={essay_id}, user_id={user_id}"
        )

        try:
            # Get essay details first
            essay_detail = await self.get_essay_detail(essay_id)
            if not essay_detail:
                raise ValueError(f"Essay not found for essay_id={essay_id}")

            # Get the maximum version number for this essay_id to auto-increment
            max_version = await self.essay_repo.get_max_version_for_essay(essay_id)
            next_version = max_version + 1

            now = datetime.utcnow()
            draft_id = generate_uuid()
            record_id = generate_uuid()

            # Get application details to populate target_university, target_major, target_degree_level
            application_data = None
            if essay_detail.application_id:
                application_data = await self.application_repo.find_application_by_id(
                    essay_detail.application_id
                )

            # Convert essay_detail to dict and add required fields for build_generate_essay_prompt
            # The function expects: essay_type, target_university, target_major, target_degree_level
            essay_record = {
                "target_university": application_data.get("university_name", "")
                if application_data
                else "",
                "target_degree_level": application_data.get("degree_level", "")
                if application_data
                else "",
                "target_major": application_data.get("program_name", "")
                if application_data
                else "",
                "essay_type": essay_detail.essay_type,
                "prompt_text": essay_detail.prompt_text,
            }

            # Memory is a list of conversation memories - empty for now if not available
            questions = await self.essay_repo.get_essay_question_by_essay_id(essay_id)

            generate_essay_prompt = build_generate_essay_prompt(essay_record, questions)
            generated_text = await generate_text(generate_essay_prompt)

            # Build draft document
            draft_document = {
                "draft_id": draft_id,
                "essay_id": essay_id,
                "version": next_version,
                "text": generated_text,
                "generated_by": "llm",  # or "teacher" / "student"
                "model": None,  # Set model name if using LLM
                "author_member_id": user_id,
                "created_at": now,
                "updated_at": now,
            }

            # Insert draft into essay_drafts collection
            insert_id = await self.essay_repo.insert_essay_draft(draft_document)
            logging.info(
                f"[EssayService] [GenerateEssayDraft] Successfully created draft with id={insert_id}, draft_id={draft_id}, version={next_version}"
            )

            # Build record document to save request/response
            record_document = {
                "record_id": record_id,
                "essay_id": essay_id,
                "draft_id": draft_id,
                "action": "generate",
                "request_payload": request.model_dump() if request else {},
                "response_payload": {
                    "draft_id": draft_id,
                    "version": next_version,
                    "text": generated_text,
                },
                "created_by_member_id": user_id,
                "created_at": now,
                "updated_at": now,
            }

            # Insert record into essay_records collection
            record_insert_id = await self.essay_repo.insert_essay_record(
                record_document
            )
            logging.info(
                f"[EssayService] [GenerateEssayDraft] Successfully created record with id={record_insert_id}, record_id={record_id}"
            )

            # Return EssayRecordDetailResponse
            return EssayRecordDetailResponse(
                record_id=record_id,
                essay_id=essay_id,
                draft_id=draft_id,
                action="generate",
                request_payload=request.model_dump() if request else {},
                response_payload={
                    "draft_id": draft_id,
                    "version": next_version,
                    "text": generated_text,
                },
                created_by_member_id=user_id,
                created_at=now,
                updated_at=now,
            )

        except Exception as e:
            logging.error(
                f"[EssayService] [GenerateEssayDraft] Failed to generate draft for essay_id={essay_id}: {e}"
            )
            raise

    async def list_essay_records(self, essay_id: str) -> EssayRecordListResponse:
        """
        List all essay records for a given essay_id
        """
        logging.info(
            f"[EssayService] [ListEssayRecords] Fetching records for essay_id={essay_id}"
        )

        try:
            records = await self.essay_repo.find_many_essay_records(essay_id)

            record_items = []
            for doc in records:
                record_item = EssayRecordDetailResponse(
                    record_id=doc.get("record_id"),
                    essay_id=doc.get("essay_id"),
                    draft_id=doc.get("draft_id"),
                    action=doc.get("action", "generate"),
                    request_payload=doc.get("request_payload", {}),
                    response_payload=doc.get("response_payload", {}),
                    created_by_member_id=doc.get("created_by_member_id"),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                )
                record_items.append(record_item)

            logging.info(
                f"[EssayService] [ListEssayRecords] Successfully retrieved {len(record_items)} record(s) for essay_id={essay_id}"
            )
            return EssayRecordListResponse(items=record_items)
        except Exception as e:
            logging.error(
                f"[EssayService] [ListEssayRecords] Failed to get records for essay_id={essay_id}: {e}"
            )
            raise

    async def get_essay_record_detail(
        self, record_id: str
    ) -> EssayRecordDetailResponse:
        """
        Get specific essay record by record_id
        """
        logging.info(
            f"[EssayService] [GetEssayRecordDetail] Fetching record for record_id={record_id}"
        )

        try:
            record_document = await self.essay_repo.get_essay_record_by_id(record_id)

            if not record_document:
                logging.warning(
                    f"[EssayService] [GetEssayRecordDetail] Record not found for record_id={record_id}"
                )
                raise ValueError(f"Essay record not found for record_id={record_id}")

            record_detail = EssayRecordDetailResponse(
                record_id=record_document.get("record_id"),
                essay_id=record_document.get("essay_id"),
                draft_id=record_document.get("draft_id"),
                action=record_document.get("action", "generate"),
                request_payload=record_document.get("request_payload", {}),
                response_payload=record_document.get("response_payload", {}),
                created_by_member_id=record_document.get("created_by_member_id"),
                created_at=record_document.get("created_at"),
                updated_at=record_document.get("updated_at"),
            )

            logging.info(
                f"[EssayService] [GetEssayRecordDetail] Successfully retrieved record for record_id={record_id}"
            )
            return record_detail

        except Exception as e:
            logging.error(
                f"[EssayService] [GetEssayRecordDetail] Failed to get record by id for record_id={record_id}: {e}"
            )
            raise
