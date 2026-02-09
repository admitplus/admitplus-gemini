import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class ExamAttemptRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.exams_attempts_collection = settings.EXAM_ATTEMPTS_COLLECTION

    async def create_attempt(
        self, attempt_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new exam attempt
        """
        try:
            attempt_id = attempt_data.get("attempt_id")
            logging.info(
                f"""[ExamAttemptRepo] [CreateAttempt] Starting - attempt_id={attempt_id}"""
            )
            logging.debug(
                f"""[ExamAttemptRepo] [CreateAttempt] Attempt data: student_id={attempt_data.get("student_id")}, exam={attempt_data.get("exam")}, section={attempt_data.get("section")}, task_type={attempt_data.get("task_type")}"""
            )

            inserted_id = await self.mongo_repo.insert_one(
                document=attempt_data, collection_name=self.exams_attempts_collection
            )

            if inserted_id:
                logging.info(
                    f"""[ExamAttemptRepo] [CreateAttempt] Successfully created attempt: {attempt_id} (inserted_id: {inserted_id})"""
                )
                # Return the attempt data with inserted_id (MongoDB _id)
                # No need to query again since we already have all the data
                attempt_data["_id"] = inserted_id
                return attempt_data
            else:
                logging.error(
                    f"""[ExamAttemptRepo] [CreateAttempt] Failed to create attempt: {attempt_id}"""
                )
                return None
        except Exception as e:
            logging.error(
                f"""[ExamAttemptRepo] [CreateAttempt] Error creating attempt: {str(e)}"""
            )
            logging.error(
                f"""[ExamAttemptRepo] [CreateAttempt] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_attempt_by_id(self, attempt_id: str) -> Optional[Dict[str, Any]]:
        try:
            logging.info(
                f"""[ExamAttemptRepo] [GetAttemptById] Starting - attempt_id={attempt_id}"""
            )

            query_filter: Dict[str, Any] = {"attempt_id": attempt_id}

            logging.debug(
                f"""[ExamAttemptRepo] [GetAttemptById] Query filter: {query_filter}, collection: {self.exams_attempts_collection}"""
            )

            attempt = await self.mongo_repo.find_one(
                query=query_filter, collection_name=self.exams_attempts_collection
            )

            if attempt:
                logging.info(
                    f"""[ExamAttemptRepo] [GetAttemptById] Successfully found attempt: {attempt_id}"""
                )
            else:
                logging.warning(
                    f"""[ExamAttemptRepo] [GetAttemptById] Attempt not found: {attempt_id}"""
                )

            return attempt
        except Exception as e:
            logging.error(
                f"""[ExamAttemptRepo] [GetAttemptById] Error retrieving attempt {attempt_id}: {str(e)}"""
            )
            logging.error(
                f"""[ExamAttemptRepo] [GetAttemptById] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def list_attempts(
        self, student_id: str, task_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            logging.info(
                f"""[ExamAttemptRepo] [ListAttempts] Starting - student_id={student_id}, task_id={task_id}, page={page}, page_size={page_size}"""
            )

            query_filter: Dict[str, Any] = {
                "student_id": student_id,
                "task_id": task_id,
            }

            logging.debug(
                f"""[ExamAttemptRepo] [ListAttempts] Query filter: {query_filter}, collection: {self.exams_attempts_collection}"""
            )

            attempts, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=page,
                page_size=page_size,
                sort={"created_at": -1},
                collection_name=self.exams_attempts_collection,
            )

            logging.info(
                f"""[ExamAttemptRepo] [ListAttempts] Successfully retrieved {len(attempts)}/{total} attempts (student_id={student_id}, task_id={task_id}, page={page}, page_size={page_size})"""
            )

            return attempts, total
        except Exception as e:
            logging.error(
                f"""[ExamAttemptRepo] [ListAttempts] Error retrieving attempts - student_id={student_id}, task_id={task_id}, page={page}, page_size={page_size}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamAttemptRepo] [ListAttempts] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def list_attempts_by_student(
        self, student_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List all attempts for a specific student (without filtering by task_id).
        Returns paginated list of attempts.
        """
        try:
            logging.info(
                f"""[ExamAttemptRepo] [ListAttemptsByStudent] Starting - student_id={student_id}, page={page}, page_size={page_size}"""
            )

            query_filter: Dict[str, Any] = {"student_id": student_id}

            logging.debug(
                f"""[ExamAttemptRepo] [ListAttemptsByStudent] Query filter: {query_filter}, collection: {self.exams_attempts_collection}"""
            )

            attempts, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=page,
                page_size=page_size,
                sort={"created_at": -1},
                collection_name=self.exams_attempts_collection,
            )

            logging.info(
                f"""[ExamAttemptRepo] [ListAttemptsByStudent] Successfully retrieved {len(attempts)}/{total} attempts (student_id={student_id}, page={page}, page_size={page_size})"""
            )

            return attempts, total
        except Exception as e:
            logging.error(
                f"""[ExamAttemptRepo] [ListAttemptsByStudent] Error retrieving attempts - student_id={student_id}, page={page}, page_size={page_size}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamAttemptRepo] [ListAttemptsByStudent] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_last_attempt_by_student(
        self, student_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent exam attempt for a student.
        Returns the attempt document if found, None otherwise.
        """
        try:
            logging.info(
                f"""[ExamAttemptRepo] [GetLastAttemptByStudent] Starting - student_id={student_id}"""
            )

            query_filter: Dict[str, Any] = {"student_id": student_id}

            attempts = await self.mongo_repo.find_many(
                query=query_filter,
                sort={"created_at": -1},  # Most recent first
                collection_name=self.exams_attempts_collection,
            )

            if attempts and len(attempts) > 0:
                logging.info(
                    f"""[ExamAttemptRepo] [GetLastAttemptByStudent] Found last attempt for student_id={student_id}"""
                )
                return attempts[0]
            else:
                logging.info(
                    f"""[ExamAttemptRepo] [GetLastAttemptByStudent] No attempts found for student_id={student_id}"""
                )
                return None

        except Exception as e:
            logging.error(
                f"""[ExamAttemptRepo] [GetLastAttemptByStudent] Error retrieving last attempt - student_id={student_id}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamAttemptRepo] [GetLastAttemptByStudent] Traceback: {traceback.format_exc()}"""
            )
            raise
