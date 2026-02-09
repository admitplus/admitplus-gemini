"""
Feedback-related schemas for exam system.

"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    """
    Detailed score information with reasoning.
    """

    score: float = Field(..., description="Score (0-9, in increments of 0.5)")
    prompt: Optional[str] = Field(None, description="Prompt used for evaluation")
    llm_model_name: Optional[str] = Field(None, description="LLM model name used")
    reason: str = Field(..., description="Detailed reason for the score")


class RevisionSuggestion(BaseModel):
    """
    Revision suggestion for improving the student's writing.
    """

    original_text: str = Field(..., description="Original text segment")
    suggested_text: str = Field(..., description="Suggested revision")
    category: str = Field(..., description="Category of the issue (e.g., Grammar)")
    explanation: str = Field(..., description="Explanation for the suggestion")


class OverallScore(BaseModel):
    """
    Overall score information.
    """

    overall: float = Field(..., description="Overall score (0-9, in increments of 0.5)")


class ScoreSubscoresDetail(BaseModel):
    """
    Detailed subscores for different evaluation criteria.
    """

    task_response: ScoreDetail = Field(..., description="Task response evaluation")
    coherence_cohesion: ScoreDetail = Field(
        ..., description="Coherence and cohesion evaluation"
    )
    lexical_resource: ScoreDetail = Field(
        ..., description="Lexical resource evaluation"
    )
    grammar: ScoreDetail = Field(..., description="Grammar evaluation")


class ScoreWithSubscoresDetail(BaseModel):
    """
    Complete score information with overall score and detailed subscores.
    """

    overall: float = Field(..., description="Overall score")
    subscores: ScoreSubscoresDetail = Field(..., description="Subscores with details")
    scale: Optional[str] = Field(
        None, description="Score scale (e.g., ielts_writing_band_0_9_v1)"
    )


class ModelEssayInfo(BaseModel):
    """
    Information about a model essay.
    """

    model_essay_id: str = Field(..., description="Model essay ID")
    essay_content: str = Field(..., description="Content of the model essay")
    analysis: str = Field(..., description="Analysis of the model essay")
    band_score: float = Field(..., description="Band score of the model essay")
    created_at: datetime = Field(..., description="Creation timestamp")


class FeedbackResponse(BaseModel):
    """
    Response model for detailed feedback.
    """

    feedback_id: str = Field(..., description="Feedback ID")
    attempt_id: str = Field(..., description="Attempt ID")
    feedback_type: str = Field(..., description="Feedback type (ai/manual)")
    model_version: Optional[str] = Field(None, description="AI model version used")
    score: Optional[ScoreWithSubscoresDetail] = Field(
        None, description="Score details (AI feedback always has score)"
    )
    summary: Optional[str] = Field(None, description="Overall summary")
    ai_comment: Optional[str] = Field(None, description="Detailed AI comments")
    suggestions: Optional[List[RevisionSuggestion]] = Field(
        None, description="Revision suggestions"
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class FeedbackListResponse(BaseModel):
    """
    Response model for list of feedbacks.
    """

    items: List[FeedbackResponse] = Field(..., description="List of feedbacks")
    total: int = Field(..., description="Total number of feedbacks")


__all__ = [
    "FeedbackListResponse",
    "FeedbackResponse",
    "ModelEssayInfo",
    "OverallScore",
    "RevisionSuggestion",
    "ScoreDetail",
    "ScoreSubscoresDetail",
    "ScoreWithSubscoresDetail",
]
