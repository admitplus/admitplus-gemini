import logging
import traceback

from fastapi import APIRouter, HTTPException, Body, Depends, Path, Query

from admitplus.dependencies.role_check import get_current_user
from .exam_attempt_schema import (
    AttemptCreateRequest,
    AttemptResponse,
    AttemptListResponse,
)
from admitplus.common.response_schema import Response
from .exam_attempt_service import AttemptService


attempt_service = AttemptService()
router = APIRouter(prefix="/exams", tags=["Exam Attempts"])


@router.post("/attempts", response_model=Response[AttemptResponse])
async def create_attempt_handler(
    request: AttemptCreateRequest = Body(..., description="Attempt creation request"),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new exam attempt
    Returns the created attempt with generated attempt_id.
    Task content is stored directly in the attempt.
    """
    student_id = current_user.get("user_id")
    if not student_id:
        logging.error(f"""[Router] [CreateAttempt] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [CreateAttempt] Request received - student_id={student_id}, task_id={request.task_id}, mode={request.mode}"""
    )
    try:
        result = await attempt_service.create_attempt(
            student_id=student_id, request=request
        )
        logging.info(
            f"""[Router] [CreateAttempt] Successfully created attempt: {result.attempt_id} (student_id={student_id}, task_id={request.task_id}, mode={request.mode})"""
        )
        return Response(code=201, message="Attempt created successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [CreateAttempt] Validation error - student_id={student_id}, exam={request.exam}, section={request.section}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [CreateAttempt] Unexpected error - student_id={student_id}, task_id={request.task_id}, mode={request.mode}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/attempts/{attempt_id}", response_model=Response[AttemptResponse])
async def get_attempt_handler(
    attempt_id: str = Path(..., description="Attempt ID (globally unique)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single attempt by ID
    Returns detailed attempt information including student answer.
    Attempt ID is globally unique, so exam and section are not required.

    Authorization:
    - Users can only access their own attempts
    """
    user_id = current_user.get("user_id")

    if not user_id:
        logging.error(f"""[Router] [GetAttempt] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GetAttempt] Request received - attempt_id={attempt_id}, user_id={user_id}"""
    )
    try:
        result = await attempt_service.get_attempt(attempt_id=attempt_id)

        # Authorization check: users can only access their own attempts
        if result.student_id != user_id:
            logging.warning(
                f"""[Router] [GetAttempt] Unauthorized access attempt - attempt_id={attempt_id}, user_id={user_id}, attempt_student_id={result.student_id}"""
            )
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this attempt",
            )

        logging.info(
            f"""[Router] [GetAttempt] Successfully retrieved attempt: {attempt_id}"""
        )

        return Response(code=200, message="Attempt retrieved successfully", data=result)
    except HTTPException:
        raise
    except ValueError as e:
        logging.error(
            f"""[Router] [GetAttempt] Attempt not found - attempt_id={attempt_id}, error: {e}"""
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetAttempt] Unexpected error - attempt_id={attempt_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tasks/{task_id}/attempts", response_model=Response[AttemptListResponse])
async def list_attempts_handler(
    task_id: str = Path(..., description="Task ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of attempts for a specific task
    Returns a paginated list of attempts for the current student and specified task.
    """
    student_id = current_user.get("user_id")
    if not student_id:
        logging.error(f"""[Router] [ListAttempts] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [ListAttempts] Request received - student_id={student_id}, task_id={task_id}, page={page}, page_size={page_size}"""
    )
    try:
        result = await attempt_service.list_attempts(
            student_id=student_id, task_id=task_id, page=page, page_size=page_size
        )
        logging.info(
            f"""[Router] [ListAttempts] Successfully retrieved {len(result.items)}/{result.total} attempts (student_id={student_id}, task_id={task_id}, page={page})"""
        )
        return Response(
            code=200, message="Attempts retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except ValueError as e:
        logging.error(
            f"""[Router] [ListAttempts] Validation error - student_id={student_id}, task_id={task_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [ListAttempts] Unexpected error - student_id={student_id}, task_id={task_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/attempts", response_model=Response[AttemptListResponse])
async def list_students_attempts_handler(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of attempts for the current student
    Returns a paginated list of all attempts for the authenticated student.
    """
    student_id = current_user.get("user_id")
    if not student_id:
        logging.error(
            f"""[Router] [ListStudentAttempts] Missing user_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [ListStudentAttempts] Request received - student_id={student_id}, page={page}, page_size={page_size}"""
    )
    try:
        result = await attempt_service.list_student_attempts(
            student_id=student_id, page=page, page_size=page_size
        )
        logging.info(
            f"""[Router] [ListStudentAttempts] Successfully retrieved {len(result.items)}/{result.total} attempts (student_id={student_id}, page={page})"""
        )
        return Response(
            code=200, message="Attempts retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except ValueError as e:
        logging.error(
            f"""[Router] [ListStudentAttempts] Validation error - student_id={student_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [ListStudentAttempts] Unexpected error - student_id={student_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")
