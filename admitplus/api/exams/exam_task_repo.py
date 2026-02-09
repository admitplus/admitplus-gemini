import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple

from admitplus.config import settings
from admitplus.database.milvus import BaseMilvusCRUD
from admitplus.database.mongo import BaseMongoCRUD


class ExamTaskRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.exam_tasks_collection = settings.EXAM_TASKS_COLLECTION

    async def list_tasks(
        self,
        exam: str,
        section: str,
        task_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            logging.info(
                f"""[ExamTaskRepo] [ListTasks] Starting - exam={exam}, section={section}, task_type={task_type}, page={page}, page_size={page_size}"""
            )

            query_filter: Dict[str, Any] = {
                "exam": exam.lower(),
                "section": section.lower(),
            }

            if task_type is not None:
                query_filter["task_type"] = task_type.lower()

            logging.debug(
                f"""[ExamTaskRepo] [ListTasks] Query filter: {query_filter}, collection: {self.exam_tasks_collection}"""
            )

            tasks, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=page,
                page_size=page_size,
                sort={"created_at": -1},
                collection_name=self.exam_tasks_collection,
            )

            logging.info(
                f"""[ExamTaskRepo] [ListTasks] Successfully retrieved {len(tasks)}/{total} tasks (exam={exam}, section={section}, task_type={task_type}, page={page}, page_size={page_size})"""
            )

            return tasks, total
        except Exception as e:
            logging.error(
                f"""[ExamTaskRepo] [ListTasks] Error retrieving tasks - exam={exam}, section={section}, task_type={task_type}, page={page}, page_size={page_size}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamTaskRepo] [ListTasks] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            logging.info(
                f"""[ExamTaskRepo] [GetTaskById] Starting - task_id={task_id}"""
            )

            query_filter: Dict[str, Any] = {"task_id": task_id}

            logging.debug(
                f"""[ExamTaskRepo] [GetTaskById] Query filter: {query_filter}, collection: {self.exam_tasks_collection}"""
            )

            task = await self.mongo_repo.find_one(
                query=query_filter, collection_name=self.exam_tasks_collection
            )

            if task:
                logging.info(
                    f"""[ExamTaskRepo] [GetTaskById] Successfully found task: {task_id}"""
                )
            else:
                logging.warning(
                    f"""[ExamTaskRepo] [GetTaskById] Task not found: {task_id}"""
                )

            return task
        except Exception as e:
            logging.error(
                f"""[ExamTaskRepo] [GetTaskById] Error retrieving task {task_id}: {str(e)}"""
            )
            logging.error(
                f"""[ExamTaskRepo] [GetTaskById] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def create_task(self, task_data: Dict[str, Any]) -> str | None:
        try:
            task_id = task_data.get("task_id")
            logging.info(
                f"""[ExamTaskRepo] [CreateTask] Starting - task_id={task_id}"""
            )
            logging.debug(
                f"""[ExamTaskRepo] [CreateTask] Task data: exam={task_data.get("exam")}, section={task_data.get("section")}, task_type={task_data.get("task_type")}"""
            )

            inserted_id = await self.mongo_repo.insert_one(
                document=task_data, collection_name=self.exam_tasks_collection
            )

            logging.info(
                f"""[ExamTaskRepo] [CreateTask] Successfully created task: {task_id} (inserted_id: {inserted_id})"""
            )
            return inserted_id
        except Exception as e:
            logging.error(
                f"""[ExamTaskRepo] [CreateTask] Error creating task: {str(e)}"""
            )
            logging.error(
                f"""[ExamTaskRepo] [CreateTask] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def delete_task(self, task_id: str) -> bool:
        try:
            logging.info(
                f"""[ExamTaskRepo] [DeleteTask] Starting - task_id={task_id}"""
            )
            query_filter: Dict[str, Any] = {"task_id": task_id}
            logging.debug(
                f"""[ExamTaskRepo] [DeleteTask] Query filter: {query_filter}, collection: {self.exam_tasks_collection}"""
            )
            result = await self.mongo_repo.delete_one(
                query=query_filter, collection_name=self.exam_tasks_collection
            )
            logging.info(
                f"""[ExamTaskRepo] [DeleteTask] Successfully deleted task: {task_id})"""
            )
            return result
        except Exception as e:
            logging.error(
                f"""[ExamTaskRepo] [DeleteTask] Error deleting task: {str(e)}"""
            )
            logging.error(
                f"""[ExamTaskRepo] [DeleteTask] Traceback: {traceback.format_exc()}"""
            )
            raise


class ExamTaskVectorRepo:
    def __init__(self):
        self.milvus_repo = BaseMilvusCRUD()

        self.exam_tasks_vector_collection = (
            settings.MILVUS_IELTS_WRITING_PROMPTS_COLLECTION
        )

    async def insert_ielts_writing_prompt(self, data: Dict[str, Any]) -> Any:
        """
        Thin wrapper: insert a single vector document into the IELTS writing
        prompts collection in Milvus.

        This method only:
        - wraps `data` in a list
        - attaches the collection name
        and delegates the rest to `BaseMilvusCRUD.insert`.
        """
        logging.info(
            "[ExamTaskVectorRepo] [InsertIELTSWritingPrompt] Inserting into Milvus"
        )

        if not self.exam_tasks_vector_collection:
            raise ValueError(
                "MILVUS_IELTS_WRITING_PROMPTS_COLLECTION is not configured"
            )

        # BaseMilvusCRUD 已经负责连接、异常处理等，这里只做最薄的一层封装
        return await self.milvus_repo.insert(
            data=[data],
            collection_name=self.exam_tasks_vector_collection,
        )

    async def search_exam(self, query: Dict[str, Any]) -> Any:
        """
        Thin wrapper for searching IELTS writing prompts in Milvus.

        - `query["vector"]`: required List[float] query embedding
        - all other keys are passed through to `BaseMilvusCRUD.search`
          (e.g. `limit`, `filter`, `output_fields`, `params`, etc.),
          except `collection_name` and `data` which are managed here.
        """
        logging.info("[ExamTaskVectorRepo] [SearchExam] Searching in Milvus")

        if not self.exam_tasks_vector_collection:
            raise ValueError(
                "MILVUS_IELTS_WRITING_PROMPTS_COLLECTION is not configured"
            )

        if not isinstance(query, dict):
            raise ValueError("query must be a dict")

        if "vector" not in query:
            raise ValueError("query['vector'] is required")

        vector = query["vector"]
        if not isinstance(vector, list):
            raise ValueError("query['vector'] must be a List[float]")

        # 其余参数（limit / filter / output_fields / params 等）全部透传
        extra_kwargs = {k: v for k, v in query.items() if k != "vector"}

        return await self.milvus_repo.search(
            query_vectors=[vector],
            collection_name=self.exam_tasks_vector_collection,
            **extra_kwargs,
        )

    async def delete_ielts_writing_prompt(self, task_id: str) -> Any:
        """
        Thin wrapper for deleting IELTS writing prompt vectors from Milvus.

        `data` supports:
        - `filter`: Milvus boolean expression string
        - `ids`: list of primary key IDs to delete

        Both values are passed directly to `BaseMilvusCRUD.delete`.
        """
        logging.info(
            "[ExamTaskVectorRepo] [DeleteIELTSWritingPrompt] Deleting from Milvus"
        )

        if not self.exam_tasks_vector_collection:
            raise ValueError(
                "MILVUS_IELTS_WRITING_PROMPTS_COLLECTION is not configured"
            )

        return await self.milvus_repo.delete(
            collection_name=self.exam_tasks_vector_collection,
            filter=f"task_id == '{task_id}'",
        )
