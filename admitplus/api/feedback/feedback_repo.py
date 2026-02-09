import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class FeedbackRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.feedbacks_collection = settings.FEEDBACKS_COLLECTION

    async def find_feedbacks(
        self, user_id: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List feedbacks with optional user_id filter.
        If user_id is provided, returns feedbacks for that user only.
        If user_id is None, returns all feedbacks.
        """
        try:
            if user_id:
                logging.info(
                    f"[FeedbackRepo] [FindFeedbacks] Starting - user_id={user_id}, page={page}, page_size={page_size}"
                )
            else:
                logging.info(
                    f"[FeedbackRepo] [FindFeedbacks] Starting - all feedbacks, page={page}, page_size={page_size}"
                )

            query_filter: Dict[str, Any] = {}
            if user_id:
                query_filter["user_id"] = user_id

            logging.debug(
                f"[FeedbackRepo] [FindFeedbacks] Query filter: {query_filter}, collection: {self.feedbacks_collection}"
            )

            feedbacks, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=page,
                page_size=page_size,
                sort={"created_at": -1},  # Most recent first
                collection_name=self.feedbacks_collection,
            )

            if user_id:
                logging.info(
                    f"[FeedbackRepo] [FindFeedbacks] Successfully retrieved {len(feedbacks)}/{total} feedbacks (user_id={user_id})"
                )
            else:
                logging.info(
                    f"[FeedbackRepo] [FindFeedbacks] Successfully retrieved {len(feedbacks)}/{total} feedbacks"
                )

            return feedbacks, total
        except Exception as e:
            logging.error(
                f"[FeedbackRepo] [FindFeedbacks] Error retrieving feedbacks - user_id={user_id}, error: {str(e)}"
            )
            logging.error(
                f"[FeedbackRepo] [FindFeedbacks] Traceback: {traceback.format_exc()}"
            )
            raise

    async def create_feedback(
        self, feedback_id: str, feedback_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new feedback
        """
        try:
            logging.info(
                f"[FeedbackRepo] [CreateFeedback] Starting - feedback_id={feedback_id}"
            )
            logging.debug(
                f"[FeedbackRepo] [CreateFeedback] Feedback data: user_id={feedback_data.get('user_id')}"
            )

            inserted_id = await self.mongo_repo.insert_one(
                document=feedback_data, collection_name=self.feedbacks_collection
            )

            if inserted_id:
                logging.info(
                    f"[FeedbackRepo] [CreateFeedback] Successfully created feedback: {feedback_id} (inserted_id: {inserted_id})"
                )
                feedback_data["_id"] = inserted_id
                return feedback_data
            else:
                logging.error(
                    f"[FeedbackRepo] [CreateFeedback] Failed to create feedback: {feedback_id}"
                )
                return None
        except Exception as e:
            logging.error(
                f"[FeedbackRepo] [CreateFeedback] Error creating feedback: {str(e)}"
            )
            logging.error(
                f"[FeedbackRepo] [CreateFeedback] Traceback: {traceback.format_exc()}"
            )
            raise
