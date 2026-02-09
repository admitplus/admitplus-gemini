import logging
import traceback
from typing import List, Optional
from datetime import datetime

from .feedback_repo import FeedbackRepo
from .feedback_schema import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackListResponse,
)
from admitplus.utils.crypto_utils import generate_uuid
from admitplus.utils.feishu_utils import notify_feishu


class FeedbackService:
    def __init__(self):
        self.feedback_repo = FeedbackRepo()
        logging.info(f"[FeedbackService] Initialized")

    async def create_feedback(
        self, user_id: str, request: FeedbackRequest
    ) -> FeedbackResponse:
        try:
            feedback_id = generate_uuid()
            logging.info(
                f"[FeedbackService] [CreateFeedback] Starting - feedback_id={feedback_id}, user_id={user_id}"
            )

            now = datetime.utcnow()
            feedback_doc = {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "page_path": request.page_path,
                "feedback_type": request.feedback_type,
                "content": request.content,
                "platform": request.platform or "web",
                "created_at": now,
            }

            created_feedback_doc = await self.feedback_repo.create_feedback(
                feedback_id=feedback_id, feedback_data=feedback_doc
            )

            if not created_feedback_doc:
                raise ValueError(f"Failed to create feedback: {feedback_id}")

            feedback_response = FeedbackResponse(
                feedback_id=feedback_id,
                user_id=user_id,
                page_path=request.page_path,
                feedback_type=request.feedback_type,
                content=request.content,
                platform=request.platform or "web",
                created_at=now,
            )

            logging.info(
                f"[FeedbackService] [CreateFeedback] Successfully created feedback: {feedback_id} (user_id={user_id})"
            )

            await notify_feishu(feedback_doc)

            return feedback_response
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"[FeedbackService] [CreateFeedback] Error creating feedback: {str(e)}"
            )
            logging.error(
                f"[FeedbackService] [CreateFeedback] Traceback: {traceback.format_exc()}"
            )
            raise

    def _convert_docs_to_responses(
        self, feedback_docs: List[dict], method_name: str
    ) -> List[FeedbackResponse]:
        feedback_items = []
        for feedback_doc in feedback_docs:
            try:
                feedback_items.append(
                    FeedbackResponse(
                        feedback_id=feedback_doc.get("feedback_id", ""),
                        user_id=feedback_doc.get("user_id", ""),
                        page_path=feedback_doc.get("page_path", ""),
                        feedback_type=feedback_doc.get("feedback_type", ""),
                        content=feedback_doc.get("content", ""),
                        platform=feedback_doc.get("platform", "web"),
                        created_at=feedback_doc.get("created_at", datetime.utcnow()),
                    )
                )
            except Exception as e:
                logging.warning(
                    f"[FeedbackService] [{method_name}] Skipping invalid feedback document: {str(e)}"
                )
                continue
        return feedback_items

    async def list_feedbacks(
        self, user_id: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> FeedbackListResponse:
        try:
            if user_id:
                logging.info(
                    f"[FeedbackService] [ListFeedbacks] Starting - user_id={user_id}, page={page}, page_size={page_size}"
                )
            else:
                logging.info(
                    f"[FeedbackService] [ListFeedbacks] Starting - all feedbacks, page={page}, page_size={page_size}"
                )

            feedbacks, total = await self.feedback_repo.find_feedbacks(
                user_id=user_id, page=page, page_size=page_size
            )

            method_name = "ListFeedbacksByUserId" if user_id else "ListAllFeedbacks"
            feedback_items = self._convert_docs_to_responses(feedbacks, method_name)

            if user_id:
                logging.info(
                    f"[FeedbackService] [ListFeedbacks] Successfully retrieved {len(feedback_items)}/{total} feedbacks (user_id={user_id})"
                )
            else:
                logging.info(
                    f"[FeedbackService] [ListFeedbacks] Successfully retrieved {len(feedback_items)}/{total} feedbacks"
                )

            return FeedbackListResponse(
                items=feedback_items, page=page, page_size=page_size, total=total
            )
        except Exception as e:
            logging.error(
                f"[FeedbackService] [ListFeedbacks] Error retrieving feedbacks - user_id={user_id}, error: {str(e)}"
            )
            logging.error(
                f"[FeedbackService] [ListFeedbacks] Traceback: {traceback.format_exc()}"
            )
            raise
