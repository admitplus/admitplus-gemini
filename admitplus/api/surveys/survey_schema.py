from typing import List, Optional, Dict, Union, Literal
from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    """
    Option for a survey question
    """

    value: str = Field(..., description="Option value")
    label: str = Field(..., description="Option label")


class Question(BaseModel):
    """
    Survey question model
    """

    id: str = Field(..., description="Question ID")
    type: str = Field(..., description="Question type: 'single' or 'multi'")
    text: str = Field(..., description="Question text")
    options: List[QuestionOption] = Field(
        ..., description="List of options for the question"
    )


class Survey(BaseModel):
    """
    Survey model containing feature key, version, and questions
    """

    featureKey: str = Field(..., description="Feature key identifier")
    version: int = Field(..., description="Survey version number")
    questions: List[Question] = Field(..., description="List of survey questions")


class ShouldShowQuestionsResponse(BaseModel):
    """
    Response model for checking if survey questions should be shown.

    When not showing questionnaire:
    {
        "show": false
    }

    When showing questionnaire:
    {
        "show": true,
        "survey": {
            "featureKey": "essay_generate",
            "version": 1,
            "questions": [...]
        }
    }
    """

    show: bool = Field(..., description="Whether to show the survey")
    survey: Optional[Survey] = Field(
        None, description="Survey data (only present when show is true)"
    )


class SurveySubmissionRequest(BaseModel):
    """
    Request model for submitting survey answers or dismissing survey.

    For submitting answers:
    {
        "survey_question_id": 1234556,
        "featureKey": "essay_generate",
        "surveyVersion": 1,
        "status": "completed",
        "answers": {
            "q1": "5",
            "q2": ["logic", "language"]
        }
    }

    For dismissing (关闭不回答):
    {
        "featureKey": "essay_generate",
        "surveyVersion": 1,
        "status": "dismissed"
    }
    """

    survey_question_id: Optional[int] = Field(
        None,
        description="Survey question ID (optional, only for completed submissions)",
    )
    featureKey: str = Field(
        ..., description="Feature key identifier (e.g., essay_generate)"
    )
    surveyVersion: int = Field(..., description="Survey version number")
    status: Literal["completed", "dismissed"] = Field(
        ...,
        description="Status: 'completed' for submitting answers, 'dismissed' for dismissing",
    )
    answers: Optional[Dict[str, Union[str, List[str]]]] = Field(
        None,
        description="Answers dictionary mapping question IDs to answers (required when status is 'completed')",
    )


class ErrorDetail(BaseModel):
    """
    Error detail model for failed responses
    """

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class SurveySubmissionResponse(BaseModel):
    """
    Response model for submitting survey answers or dismissing survey.

    Success:
    {
        "success": true
    }

    Error:
    {
        "success": false,
        "error": {
            "code": "INVALID_SURVEY_VERSION",
            "message": "Submitted version does not match active survey version."
        }
    }
    """

    success: bool = Field(..., description="Whether the operation was successful")
    error: Optional[ErrorDetail] = Field(
        None, description="Error details (only present when success is false)"
    )
