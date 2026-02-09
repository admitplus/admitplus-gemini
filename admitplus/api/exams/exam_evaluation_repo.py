import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class ExamFeedbackRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.exam_feedbacks_collection = settings.EXAM_FEEDBACKS_COLLECTION
        self.exam_model_essays_collection = settings.EXAM_MODEL_ESSAYS_COLLECTION

    async def create_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new feedback
        """
        try:
            feedback_id = feedback_data.get("feedback_id")
            logging.info(
                f"""[ExamFeedbackRepo] [CreateFeedback] Starting - feedback_id={feedback_id}"""
            )

            logging.debug(
                f"""[ExamFeedbackRepo] [CreateFeedback] Feedback data: attempt_id={feedback_data.get("attempt_id")}, feedback_type={feedback_data.get("feedback_type")}"""
            )

            inserted_id = await self.mongo_repo.insert_one(
                document=feedback_data, collection_name=self.exam_feedbacks_collection
            )

            if inserted_id:
                logging.info(
                    f"""[ExamFeedbackRepo] [CreateFeedback] Successfully created feedback: {feedback_id} (inserted_id: {inserted_id})"""
                )
                # Return the feedback data with inserted_id (MongoDB _id)
                # No need to query again since we already have all the data
                feedback_data["_id"] = inserted_id
                return feedback_data
            else:
                logging.error(
                    f"""[ExamFeedbackRepo] [CreateFeedback] Failed to create feedback: {feedback_id}"""
                )
                return None
        except Exception as e:
            logging.error(
                f"""[ExamFeedbackRepo] [CreateFeedback] Error creating feedback: {str(e)}"""
            )
            logging.error(
                f"""[ExamFeedbackRepo] [CreateFeedback] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def list_feedbacks(self, attempt_id: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        List all feedbacks for a specific attempt
        """
        try:
            logging.info(
                f"""[ExamFeedbackRepo] [ListFeedbacks] Starting - attempt_id={attempt_id}"""
            )

            query_filter: Dict[str, Any] = {"attempt_id": attempt_id}

            logging.debug(
                f"""[ExamFeedbackRepo] [ListFeedbacks] Query filter: {query_filter}, collection: {self.exam_feedbacks_collection}"""
            )

            feedbacks, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=1,
                page_size=1000,  # Get all feedbacks for an attempt
                sort={"created_at": -1},  # Most recent first
                collection_name=self.exam_feedbacks_collection,
            )

            logging.info(
                f"""[ExamFeedbackRepo] [ListFeedbacks] Successfully retrieved {len(feedbacks)}/{total} feedbacks (attempt_id={attempt_id})"""
            )

            return feedbacks, total
        except Exception as e:
            logging.error(
                f"""[ExamFeedbackRepo] [ListFeedbacks] Error retrieving feedbacks - attempt_id={attempt_id}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamFeedbackRepo] [ListFeedbacks] Traceback: {traceback.format_exc()}"""
            )
            raise

    # ============================================================================
    # Model Essay Operations
    # ============================================================================

    async def create_model_essay(
        self, model_essay_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new model essay
        """
        try:
            model_essay_id = model_essay_data.get("model_essay_id")
            logging.info(
                f"""[ExamFeedbackRepo] [CreateModelEssay] Starting - model_essay_id={model_essay_id}"""
            )

            logging.debug(
                f"""[ExamFeedbackRepo] [CreateModelEssay] Model essay data: attempt_id={model_essay_data.get("attempt_id")}, target_score={model_essay_data.get("target_score")}"""
            )

            inserted_id = await self.mongo_repo.insert_one(
                document=model_essay_data,
                collection_name=self.exam_model_essays_collection,
            )

            if inserted_id:
                logging.info(
                    f"""[ExamFeedbackRepo] [CreateModelEssay] Successfully created model essay: {model_essay_id} (inserted_id: {inserted_id})"""
                )
                model_essay_data["_id"] = inserted_id
                return model_essay_data
            else:
                logging.error(
                    f"""[ExamFeedbackRepo] [CreateModelEssay] Failed to create model essay: {model_essay_id}"""
                )
                return None
        except Exception as e:
            logging.error(
                f"""[ExamFeedbackRepo] [CreateModelEssay] Error creating model essay: {str(e)}"""
            )
            logging.error(
                f"""[ExamFeedbackRepo] [CreateModelEssay] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_model_essay_by_id(
        self, model_essay_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single model essay by ID
        """
        try:
            logging.info(
                f"""[ExamFeedbackRepo] [GetModelEssayById] Starting - model_essay_id={model_essay_id}"""
            )

            query_filter: Dict[str, Any] = {"model_essay_id": model_essay_id}

            logging.debug(
                f"""[ExamFeedbackRepo] [GetModelEssayById] Query filter: {query_filter}, collection: {self.exam_model_essays_collection}"""
            )

            model_essay = await self.mongo_repo.find_one(
                query=query_filter, collection_name=self.exam_model_essays_collection
            )

            if model_essay:
                logging.info(
                    f"""[ExamFeedbackRepo] [GetModelEssayById] Successfully found model essay: {model_essay_id}"""
                )
            else:
                logging.warning(
                    f"""[ExamFeedbackRepo] [GetModelEssayById] Model essay not found: {model_essay_id}"""
                )

            return model_essay
        except Exception as e:
            logging.error(
                f"""[ExamFeedbackRepo] [GetModelEssayById] Error retrieving model essay {model_essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[ExamFeedbackRepo] [GetModelEssayById] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_model_essay_by_attempt(
        self,
        attempt_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get model essay by attempt_id
        This retrieves the model essay associated with a specific attempt
        """
        try:
            logging.info(
                f"""[ExamFeedbackRepo] [GetModelEssayByAttempt] Starting - attempt_id={attempt_id}"""
            )

            query_filter: Dict[str, Any] = {
                "attempt_id": attempt_id,
            }

            logging.debug(
                f"""[ExamFeedbackRepo] [GetModelEssayByAttempt] Query filter: {query_filter}, collection: {self.exam_model_essays_collection}"""
            )

            model_essay = await self.mongo_repo.find_one(
                query=query_filter, collection_name=self.exam_model_essays_collection
            )

            if model_essay:
                logging.info(
                    f"""[ExamFeedbackRepo] [GetModelEssayByAttempt] Successfully found model essay for attempt_id={attempt_id}"""
                )
            else:
                logging.warning(
                    f"""[ExamFeedbackRepo] [GetModelEssayByAttempt] Model essay not found for attempt_id={attempt_id}"""
                )

            return model_essay
        except Exception as e:
            logging.error(
                f"""[ExamFeedbackRepo] [GetModelEssayByAttempt] Error retrieving model essay - attempt_id={attempt_id}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamFeedbackRepo] [GetModelEssayByAttempt] Traceback: {traceback.format_exc()}"""
            )
            raise
