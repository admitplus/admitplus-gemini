import logging
import traceback

from fastapi import APIRouter, HTTPException, Depends, Path

from admitplus.dependencies.role_check import get_current_user
from .exam_evaluation_schema import (
    FeedbackResponse,
    FeedbackListResponse,
    ModelEssayInfo,
)
from admitplus.common.response_schema import Response
from .exam_evaluation_service import ExamFeedbackService


feedback_service = ExamFeedbackService()
router = APIRouter(prefix="/exams", tags=["Exam Feedbacks"])


@router.post("/attempts/{attempt_id}/feedbacks/ai")
async def generate_ai_feedback_handler(
    attempt_id: str = Path(..., description="Attempt ID"),
    _: dict = Depends(get_current_user),
):
    """
    Generate AI feedback for an exam attempt
    Returns detailed evaluation including scores and comments for each criterion.
    """
    logging.info(
        f"""[Router] [GenerateAIFeedback] Request received - attempt_id={attempt_id}"""
    )
    try:
        result = await feedback_service.generate_feedback_v2(
            attempt_id=attempt_id,
        )
        # AI feedback always has a score
        overall_score = result["score"]["overall"] if result["score"] else None
        logging.info(
            f"""[Router] [GenerateAIFeedback] Successfully generated feedback for attempt: {attempt_id}, overall_score={overall_score}"""
        )
        result["attempt_id"] = attempt_id
        await feedback_service.feedback_repo.create_feedback(result)
        return Response(
            code=200, message="Feedback generated successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [GenerateAIFeedback] Validation error - attempt_id={attempt_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GenerateAIFeedback] Unexpected error - attempt_id={attempt_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/attempts/{attempt_id}/feedbacks", response_model=Response[FeedbackListResponse]
)
async def list_feedbacks_handler(
    attempt_id: str = Path(..., description="Attempt ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of feedbacks for a specific attempt
    Returns all feedbacks (both AI and manual) for the attempt, ordered by creation time (most recent first).

    Authorization:
    - Users can only access feedbacks for their own attempts
    """
    student_id = current_user.get("user_id")

    if not student_id:
        logging.error(
            f"""[Router] [ListFeedbacks] Missing student_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [ListFeedbacks] Request received - attempt_id={attempt_id}, student_id={student_id}"""
    )
    try:
        result = await feedback_service.list_feedbacks(
            attempt_id=attempt_id, student_id=student_id
        )
        logging.info(
            f"""[Router] [ListFeedbacks] Successfully retrieved {len(result.items)}/{result.total} feedbacks (attempt_id={attempt_id})"""
        )
        return Response(
            code=200, message="Feedbacks retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"""[Router] [ListFeedbacks] Unexpected error - attempt_id={attempt_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/attempts/{attempt_id}/feedbacks/{feedback_id}/model-essay",
    response_model=Response[ModelEssayInfo],
)
async def generate_model_essay_handler(
    attempt_id: str = Path(..., description="Attempt ID"),
    feedback_id: str = Path(..., description="Feedback ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate or retrieve model essay for a specific feedback and attempt.
    If a model essay already exists, it will be returned. Otherwise, a new one will be generated.
    Model essays are only generated when user clicks "Generate Model Essay" button.

    Authorization:
    - Users can only access model essays for their own attempts
    """
    student_id = current_user.get("user_id")

    if not student_id:
        logging.error(
            f"""[Router] [GenerateModelEssay] Missing student_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GenerateModelEssay] Request received - attempt_id={attempt_id}, feedback_id={feedback_id}, student_id={student_id}"""
    )
    try:
        result = await feedback_service.generate_model_essay(
            attempt_id=attempt_id, feedback_id=feedback_id, student_id=student_id
        )

        if result is None:
            logging.info(
                f"""[Router] [GenerateModelEssay] Model essay not found - attempt_id={attempt_id}, feedback_id={feedback_id}"""
            )
            raise HTTPException(
                status_code=404, detail="Model essay not found for this feedback"
            )

        logging.info(
            f"""[Router] [GenerateModelEssay] Successfully generated/retrieved model essay - attempt_id={attempt_id}, feedback_id={feedback_id}, model_essay_id={result.model_essay_id}"""
        )
        return Response(
            code=200, message="Model essay generated successfully", data=result
        )
    except HTTPException:
        raise
    except ValueError as e:
        logging.error(
            f"""[Router] [GenerateModelEssay] Validation error - attempt_id={attempt_id}, feedback_id={feedback_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GenerateModelEssay] Unexpected error - attempt_id={attempt_id}, feedback_id={feedback_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/attempts/{attempt_id}/model-essay",
    response_model=Response[ModelEssayInfo],
    status_code=200,
)
async def get_model_essay_by_attempt_handler(
    attempt_id: str = Path(..., description="Attempt ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get model essay for a specific attempt.
    This endpoint retrieves an existing model essay without generating a new one.

    Authorization:
    - Users can only access model essays for their own attempts
    """
    student_id = current_user.get("user_id")

    if not student_id:
        logging.error(
            f"""[Router] [GetModelEssayByAttempt] Missing student_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GetModelEssayByAttempt] Request received - attempt_id={attempt_id}, student_id={student_id}"""
    )
    try:
        result = await feedback_service.get_model_essay_by_attempt(
            attempt_id=attempt_id, student_id=student_id
        )
        if result is None:
            logging.info(
                f"""[Router] [GetModelEssayByAttempt] Model essay not found - attempt_id={attempt_id}"""
            )
            return Response(code=200, message="Model essay not found", data=None)
        logging.info(
            f"""[Router] [GetModelEssayByAttempt] Successfully retrieved model essay - attempt_id={attempt_id}, model_essay_id={result.model_essay_id}"""
        )
        return Response(
            code=200, message="Model essay retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except ValueError as e:
        logging.error(
            f"""[Router] [GetModelEssayByAttempt] Validation error - attempt_id={attempt_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetModelEssayByAttempt] Unexpected error - attempt_id={attempt_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")
