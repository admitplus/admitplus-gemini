import logging
import traceback

from fastapi import APIRouter, HTTPException, Query, Depends

from admitplus.dependencies.role_check import get_current_user
from .survey_schema import (
    ShouldShowQuestionsResponse,
    SurveySubmissionResponse,
    SurveySubmissionRequest,
)
from .survey_service import SurveyService

survey_service = SurveyService()
router = APIRouter(prefix="/survey", tags=["Surveys"])


def _get_user_id(current_user: dict) -> str:
    """Extract and validate user_id from current_user."""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user information")
    return user_id


@router.get("/should_show", response_model=ShouldShowQuestionsResponse)
async def should_show_questions_handler(
    feature_key: str = Query(
        ..., description="Feature key identifier (e.g., essay_generate)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Check if survey questions should be shown for a given feature key.

    Conditions checked:
    1. Is there an active survey for the current feature?
    2. Has the user answered this survey (same feature_key and version)?
    """
    try:
        user_id = _get_user_id(current_user)
        result = await survey_service.should_show_questions(
            feature_key=feature_key, user_id=user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[SurveyRouter] [ShouldShowQuestions] Error: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=SurveySubmissionResponse)
async def submit_survey_answers_handler(
    request: SurveySubmissionRequest, current_user: dict = Depends(get_current_user)
):
    """
    Submit survey answers or dismiss survey.

    For submitting answers:
    - Requires answers field with question IDs mapped to answers
    - Validates that submitted version matches active survey version

    For dismissing:
    - Sets status to "dismissed"
    """
    try:
        user_id = _get_user_id(current_user)
        result = await survey_service.submit_survey_answers(
            question_data=request.model_dump(), user_id=user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[SurveyRouter] [SubmitSurveyAnswers] Error: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")
