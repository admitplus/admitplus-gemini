from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .exam_model import AttemptModeEnum
from .exam_task_schema import TaskPrompt


class StudentAnswer(BaseModel):
    """
    Student's answer to a task.
    """

    text: Optional[str] = Field(None, description="Student's answer text")
    audio_url: Optional[str] = Field(None, description="Audio URL for speaking section")
    selected_options: Optional[List[int]] = Field(
        None, description="Selected option indices for multiple choice questions"
    )


class AttemptMetadata(BaseModel):
    """
    Metadata associated with an attempt.
    """

    time_spent_seconds: Optional[int] = Field(
        None, description="Time spent on the attempt in seconds"
    )


class AttemptCreateRequest(BaseModel):
    """
    Request model for creating a new attempt.
    """

    task_id: str = Field(..., description="Task ID")
    mode: str = Field(
        default=AttemptModeEnum.PRACTICE.value,
        description="Attempt mode (e.g., practice, exam)",
    )
    student_answer: StudentAnswer = Field(..., description="Student's answer")
    metadata: Optional[AttemptMetadata] = Field(None, description="Attempt metadata")


class AttemptBase(BaseModel):
    """
    Base model for attempt information.
    """

    attempt_id: str = Field(..., description="Attempt ID")
    task_id: str = Field(..., description="Task ID")
    exam: str = Field(..., description="Exam name")
    section: str = Field(..., description="Section name")
    task_type: str = Field(..., description="Task type")
    task_prompt: TaskPrompt = Field(..., description="Task prompt")
    mode: str = Field(..., description="Attempt mode (e.g., practice, exam)")
    student_id: str = Field(..., description="Student ID")
    student_answer: StudentAnswer = Field(..., description="Student's answer")
    created_at: datetime = Field(..., description="Creation timestamp")


class AttemptItem(AttemptBase):
    """
    Attempt item used in attempt list responses.
    """

    pass


class AttemptResponse(AttemptBase):
    """
    Response model for detailed attempt information.
    """

    metadata: Optional[AttemptMetadata] = Field(None, description="Attempt metadata")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class AttemptListResponse(BaseModel):
    """
    Response model for paginated attempt list.
    """

    items: List[AttemptItem] = Field(..., description="List of attempts")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of attempts")


__all__ = [
    "AttemptBase",
    "AttemptCreateRequest",
    "AttemptItem",
    "AttemptListResponse",
    "AttemptMetadata",
    "AttemptResponse",
    "StudentAnswer",
]
