"""
Feedback-related schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """
    Request model for creating a new feedback.
    """

    page_path: str = Field(..., description="Page path where feedback was submitted")
    feedback_type: str = Field(
        ..., description="Type of feedback: suggestion, bug, or other"
    )
    content: str = Field(..., description="Feedback content")
    platform: Optional[str] = Field(
        default="web", description="Platform where feedback was submitted"
    )


class FeedbackResponse(BaseModel):
    """
    Response model for feedback information.
    """

    feedback_id: str = Field(..., description="Feedback ID")
    user_id: str = Field(..., description="User ID who submitted the feedback")
    page_path: str = Field(..., description="Page path where feedback was submitted")
    feedback_type: str = Field(
        ..., description="Type of feedback: suggestion, bug, or other"
    )
    content: str = Field(..., description="Feedback content")
    platform: str = Field(..., description="Platform where feedback was submitted")
    created_at: datetime = Field(..., description="Creation timestamp")


class FeedbackListResponse(BaseModel):
    """
    Response model for paginated feedback list.
    """

    items: List[FeedbackResponse] = Field(..., description="List of feedbacks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of feedbacks")


__all__ = [
    "FeedbackRequest",
    "FeedbackResponse",
    "FeedbackListResponse",
]
