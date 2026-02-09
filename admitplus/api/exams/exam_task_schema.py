from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InputAssets(BaseModel):
    """
    Input assets for a task (e.g., images, charts).

    Note: For attempts, image_url is used for input but image_text (extracted content)
    is stored instead of the URL.
    """

    image_url: Optional[str] = Field(
        None,
        description="Image URL (e.g., gcs://.../chart_0001.png) - used for input only",
    )
    image_description: Optional[str] = Field(
        None, description="Extracted text/content from image - stored in attempts"
    )


class TaskPrompt(BaseModel):
    """
    Task prompt containing description and optional input assets.
    """

    description: str = Field(..., description="Prompt description")
    input_assets: Optional[InputAssets] = Field(
        None, description="Input assets (images, etc.)"
    )


class TaskBaseResponse(BaseModel):
    """
    Base response model for task information.
    """

    task_id: str = Field(..., description="Task ID")
    source: str = Field(..., description="Source of the task")
    series: str = Field(..., description="Series of the task")
    exam: str = Field(..., description="Exam name")
    section: str = Field(..., description="Section name")
    task_type: str = Field(..., description="Task type")
    prompt: TaskPrompt = Field(..., description="Task prompt")
    created_at: datetime = Field(..., description="Creation timestamp")


class TaskDetailResponse(TaskBaseResponse):
    """
    Response model for detailed task information.
    """

    pass


class TaskListResponse(BaseModel):
    """
    Response model for paginated task list.
    """

    items: List[TaskBaseResponse] = Field(..., description="List of tasks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of tasks")


class TaskCreateResponse(TaskBaseResponse):
    """
    Response model for task creation.
    """

    pass


__all__ = [
    "InputAssets",
    "TaskPrompt",
    "TaskBaseResponse",
    "TaskCreateResponse",
    "TaskDetailResponse",
    "TaskListResponse",
]
