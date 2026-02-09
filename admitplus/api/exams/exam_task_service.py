import logging
import traceback
from typing import Optional
from datetime import datetime
from fastapi import HTTPException

from .exam_task_repo import ExamTaskRepo, ExamTaskVectorRepo
from .exam_task_schema import (
    TaskListResponse,
    TaskPrompt,
    TaskDetailResponse,
    TaskBaseResponse,
    InputAssets,
    TaskCreateResponse,
)
from admitplus.llm.providers.openai.openai_client import extract_text_from_image
from admitplus.utils.crypto_utils import generate_uuid
from admitplus.api.files.file_service import FileService

# from ...llm.providers.google.gemini_client import embedding
from ...llm.providers.openai.openai_client import embedding


class TaskService:
    def __init__(self):
        self.task_repo = ExamTaskRepo()
        self.tasks_vector_repo = ExamTaskVectorRepo()

    def _build_task_response(
        self,
        task_doc: dict,
        default_exam: Optional[str] = None,
        default_section: Optional[str] = None,
    ) -> TaskBaseResponse:
        """
        Helper method to build TaskBaseResponse from database document.
        """
        prompt_data = task_doc.get("prompt", {}) or {}
        if not isinstance(prompt_data, dict):
            prompt_data = {}

        # Extract input_assets
        input_assets = None
        input_assets_data = prompt_data.get("input_assets")
        if isinstance(input_assets_data, dict) and input_assets_data.get("image_url"):
            input_assets = InputAssets(
                image_url=input_assets_data["image_url"],
                image_description=input_assets_data.get("image_description"),
            )

        return TaskBaseResponse(
            task_id=task_doc.get("task_id"),
            source=task_doc.get("source", "").lower(),
            series=task_doc.get("series", "").lower(),
            exam=(task_doc.get("exam") or default_exam or "").lower(),
            section=(task_doc.get("section") or default_section or "").lower(),
            task_type=task_doc.get("task_type", "").lower(),
            prompt=TaskPrompt(
                description=prompt_data.get("description", ""),
                input_assets=input_assets,
            ),
            created_at=task_doc.get("created_at"),
        )

    async def list_tasks(
        self,
        exam: str,
        section: str,
        task_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TaskListResponse:
        tasks_data, total = await self.task_repo.list_tasks(
            exam=exam,
            section=section,
            task_type=task_type,
            page=page,
            page_size=page_size,
        )

        task_items = []
        for task_doc in tasks_data:
            try:
                task_items.append(self._build_task_response(task_doc, exam, section))
            except Exception as e:
                logging.warning(
                    f"""[TaskService] [GetTasksList] Skipping invalid task document: {str(e)}"""
                )
                continue

        logging.info(
            f"""[TaskService] [GetTasksList] Retrieved {len(task_items)}/{total} tasks (exam={exam}, section={section}, task_type={task_type}, page={page})"""
        )

        return TaskListResponse(
            items=task_items, page=page, page_size=page_size, total=total
        )

    async def get_task(self, task_id: str) -> TaskDetailResponse:
        try:
            logging.info(f"""[TaskService] [GetTask] Starting - task_id={task_id}""")

            task_doc = await self.task_repo.get_task_by_id(task_id=task_id)

            if not task_doc:
                logging.warning(
                    f"""[TaskService] [GetTask] Task not found: {task_id}"""
                )
                raise HTTPException(status_code=404, detail="Task not found")

            logging.debug(
                f"""[TaskService] [GetTask] Retrieved task document from repository: {task_id}"""
            )

            task_base = self._build_task_response(task_doc)
            task_detail = TaskDetailResponse(**task_base.model_dump())

            logging.info(
                f"""[TaskService] [GetTask] Successfully processed task: {task_id} (exam={task_detail.exam}, section={task_detail.section}, task_type={task_detail.task_type})"""
            )

            return task_detail
        except ValueError:
            # Re-raise ValueError (task not found) without additional logging
            raise
        except Exception as e:
            logging.error(
                f"""[TaskService] [GetTask] Error processing task {task_id}: {str(e)}"""
            )
            logging.error(
                f"""[TaskService] [GetTask] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def create_task(
        self,
        source: str,
        series: str,
        exam: str,
        section: str,
        task_type: str,
        essay_prompt: str,
        image: Optional[str] = None,
    ) -> TaskCreateResponse:
        try:
            task_id = generate_uuid()
            logging.info(
                f"""[TaskService] [CreateTask] Starting exam={exam}, section={section}"""
            )
            if image:
                content = await image.read()
                _FileService = FileService()
                bucket = _FileService._storage_client.bucket(_FileService.bucket_name)
                blob = bucket.blob(f"files/{task_id}")
                blob.content_type = image.content_type
                _FileService._upload_with_retry(blob, content, image.content_type)
                logging.info(
                    f"[File Service] [File Upload] Successfully uploaded to GCS"
                )

            prompt_data = {"description": essay_prompt or ""}
            if image:
                prompt_data["input_assets"] = {"image_url": blob.public_url}
                prompt_data["input_assets"][
                    "image_description"
                ] = await extract_text_from_image(blob.public_url)

            now = datetime.now()
            vector_task_doc = {
                "section": section.lower(),
                "task_type": task_type,
                "vector": await embedding(essay_prompt),
                "task_id": task_id,
                "metadata": {
                    "source": source,
                    "series": series,
                    "exam": exam.lower(),
                    "essay_prompt": essay_prompt,
                    "created_at": now,
                },
            }
            if image:
                vector_task_doc["metadata"]["image_description"] = prompt_data[
                    "input_assets"
                ]["image_description"]
            await self.tasks_vector_repo.insert_ielts_writing_prompt(vector_task_doc)

            task_doc = {
                "task_id": task_id,
                "source": source,
                "series": series,
                "exam": exam.lower(),
                "section": section.lower(),
                "task_type": task_type,
                "task_prompt": prompt_data,
                "created_at": now,
            }

            inserted_id = await self.task_repo.create_task(task_doc)
            if not inserted_id:
                raise ValueError(f"Failed to create task: {task_id}")

            task_response = TaskCreateResponse(
                task_id=task_id,
                exam=exam.lower(),
                section=section.lower(),
                source=source,
                series=series,
                task_type=task_type,
                prompt=TaskPrompt(
                    description=prompt_data["description"],
                    input_assets=InputAssets(
                        image_url=prompt_data["input_assets"]["image_url"],
                        image_description=prompt_data["input_assets"][
                            "image_description"
                        ],
                    )
                    if "input_assets" in prompt_data
                    else None,
                ),
                created_at=now,
            )

            logging.info(
                f"""[TaskService] [CreateTask] Successfully created task: {task_id}"""
            )
            return task_response
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"""[TaskService] [CreateTask] Error creating task: {str(e)}"""
            )
            logging.error(
                f"""[TaskService] [CreateTask] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def delete_task(self, task_id: str):
        await self.tasks_vector_repo.delete_ielts_writing_prompt(task_id)
        return await self.task_repo.delete_task(task_id=task_id)
