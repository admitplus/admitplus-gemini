import logging
import traceback

from fastapi import APIRouter, HTTPException, Query, Path, Form, File, UploadFile
from typing import Optional

from .exam_task_schema import (
    TaskListResponse,
    TaskDetailResponse,
    TaskCreateResponse,
)
from .exam_model import ExamSectionEnum, ExamEnum, TaskTypeEnum, SeriesEnum
from admitplus.common.response_schema import Response
from .exam_task_service import TaskService


task_service = TaskService()
router = APIRouter(prefix="/exams", tags=["IELTS Essay Test"])


@router.post(
    "/{exam}/{section}/tasks",
    response_model=Response[TaskCreateResponse],
    status_code=201,
)
async def create_task_handler(
    exam: str = Path(
        ...,
        OneOf=[each.value for each in ExamEnum],
        description="Exam name (e.g., ielts)",
    ),
    section: str = Path(
        ...,
        OneOf=[each.value for each in ExamSectionEnum],
        description="Section name (e.g., writing)",
    ),
    task_type: TaskTypeEnum = Form(...),
    source: str = Form("Cambridge"),
    series: SeriesEnum = Form(...),
    description: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    """
    Create a new task for a specific exam and section
    Returns the created task with generated task_id.
    """
    logging.info(
        f"""[Router] [CreateTask] Request received - exam={exam}, section={section}"""
    )
    if task_type == TaskTypeEnum.TASK1.value:
        if image is None:
            raise HTTPException(
                status_code=400, detail="Task 1 requires exactly one image"
            )

    try:
        result = await task_service.create_task(
            source=source,
            series=series,
            exam=exam,
            section=section,
            task_type=task_type,
            essay_prompt=description,
            image=image,
        )
        logging.info(
            f"""[Router] [CreateTask] Successfully created task: {result.task_id} (exam={exam}, section={section})"""
        )
        return Response(code=201, message="Task created successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [CreateTask] Validation error - exam={exam}, section={section}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [CreateTask] Unexpected error - exam={exam}, section={section}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{exam}/{section}/tasks", response_model=Response[TaskListResponse])
async def list_tasks_handler(
    exam: str = Path(..., description="Exam name (e.g., ielts)"),
    section: str = Path(..., description="Section name (e.g., writing)"),
    task_type: Optional[str] = Query(
        None, description="Task type filter (e.g., task1, task2)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """
    Get list of tasks for a specific exam and section
    Returns a paginated list of tasks matching the specified filters.
    """
    logging.info(
        f"""[Router] [ListTasks] Request received - exam={exam}, section={section}, task_type={task_type}, page={page}, page_size={page_size}"""
    )
    try:
        result = await task_service.list_tasks(
            exam=exam,
            section=section,
            task_type=task_type,
            page=page,
            page_size=page_size,
        )
        logging.info(
            f"""[Router] [ListTasks] Successfully retrieved {len(result.items)}/{result.total} tasks (exam={exam}, section={section}, task_type={task_type}, page={page})"""
        )
        return Response(code=200, message="Tasks retrieved successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [ListTasks] Validation error - exam={exam}, section={section}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [ListTasks] Unexpected error - exam={exam}, section={section}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tasks/{task_id}", response_model=Response[TaskDetailResponse])
async def get_task_handler(
    task_id: str = Path(..., description="Task ID (globally unique)"),
):
    """
    Get a single task by ID
    Returns detailed task information including full prompt with description and input assets.
    Task ID is globally unique, so exam and section are not required.
    """
    logging.info(f"""[Router] [GetTask] Request received - task_id={task_id}""")
    try:
        result = await task_service.get_task(task_id=task_id)
        logging.info(f"""[Router] [GetTask] Successfully retrieved task: {task_id}""")

        return Response(code=200, message="Task retrieved successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [GetTask] Task not found - task_id={task_id}, error: {e}"""
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetTask] Unexpected error - task_id={task_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/tasks/{task_id}")
async def delete_task_handler(
    task_id: str = Path(..., description="Task ID (globally unique)"),
):
    """
    Delete a single task by ID
    Returns a success message if the task is deleted.
    Task ID is globally unique, so exam and section are not required.
    """
    logging.info(f"""[Router] [DeleteTask] Request received - task_id={task_id}""")
    delete_count = await task_service.delete_task(task_id=task_id)
    if delete_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(code=200, message="Task deleted successfully")
