import logging
import traceback

from fastapi import APIRouter, HTTPException, Body, Depends, Path, Query

from admitplus.dependencies.role_check import get_current_user
from .feedback_schema import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackListResponse,
)
from admitplus.common.response_schema import Response
from .feedback_service import FeedbackService

feedback_service = FeedbackService()
router = APIRouter(prefix="/feedbacks", tags=["Feedback"])


@router.post("/", response_model=Response[FeedbackResponse], status_code=201)
async def create_feedback_handler(
    request: FeedbackRequest = Body(..., description="Feedback creation request"),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new feedback
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"[Router] [CreateFeedback] Missing user_id in current_user")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"[Router] [CreateFeedback] Request received - user_id={user_id}, page_path={request.page_path}, feedback_type={request.feedback_type}"
    )
    try:
        result = await feedback_service.create_feedback(
            user_id=user_id, request=request
        )
        logging.info(
            f"[Router] [CreateFeedback] Successfully created feedback: {result.feedback_id} (user_id={user_id})"
        )
        return Response(code=201, message="Feedback created successfully", data=result)
    except ValueError as e:
        logging.error(
            f"[Router] [CreateFeedback] Validation error - user_id={user_id}, error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [CreateFeedback] Unexpected error - user_id={user_id}, error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


def _build_list_response(
    result: FeedbackListResponse, user_id: str = None
) -> Response[FeedbackListResponse]:
    """Helper function to build list response"""
    if user_id:
        logging.info(
            f"[Router] [ListFeedbacks] Successfully retrieved {len(result.items)}/{result.total} feedbacks for user_id={user_id}"
        )
    else:
        logging.info(
            f"[Router] [ListFeedbacks] Successfully retrieved {len(result.items)}/{result.total} feedbacks"
        )
    return Response(code=200, message="Feedbacks retrieved successfully", data=result)


@router.get(
    "/user/{user_id}", response_model=Response[FeedbackListResponse], status_code=200
)
async def list_feedbacks_by_user_handler(
    user_id: str = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all feedbacks for a specific user
    """
    try:
        # Check if user is accessing their own feedbacks or is admin
        current_user_id = current_user.get("user_id")
        if current_user_id != user_id:
            # TODO: Add admin role check here if needed
            logging.warning(
                f"[Router] [ListFeedbacksByUser] User {current_user_id} attempted to access feedbacks for user {user_id}"
            )
            raise HTTPException(status_code=403, detail="Access denied")

        result = await feedback_service.list_feedbacks(
            user_id=user_id, page=page, page_size=page_size
        )
        return _build_list_response(result, user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Router] [ListFeedbacksByUser] Unexpected error - user_id={user_id}, error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=Response[FeedbackListResponse], status_code=200)
async def list_all_feedbacks_handler(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all feedbacks (admin only)
    """
    try:
        # TODO: Add admin role check here
        result = await feedback_service.list_feedbacks(
            user_id=None, page=page, page_size=page_size
        )
        return _build_list_response(result)
    except Exception as e:
        logging.error(
            f"[Router] [ListAllFeedbacks] Unexpected error - error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
