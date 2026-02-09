import logging
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from admitplus.common.response_schema import Response
from ..schemas.student_schema import (
    StudentHighlightListResponse,
    StudentHighlightResponse,
    StudentHighlightCreateRequest,
    StudentHighlightUpdateRequest,
)
from .student_highlight_service import StudentHighlightService
from admitplus.dependencies.role_check import get_current_user
from admitplus.api.analysis.analyze_service import AnalysisService
from admitplus.api.files.file_service import FileService

router = APIRouter(prefix="/students", tags=["Highlight"])

highlight_service = StudentHighlightService()
analysis_service = AnalysisService()
file_service = FileService()


@router.post(
    "/{student_id}/highlights", response_model=Response[StudentHighlightResponse]
)
async def create_student_highlight_handler(
    student_id: str,
    request: StudentHighlightCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a student highlight
    """
    logging.info(
        f"[Student Router] [CreateStudentHighlight] Creating highlight for student_id: {student_id}"
    )
    try:
        if not student_id or not student_id.strip():
            raise HTTPException(status_code=400, detail="Student ID is required")

        created_by_member_id = current_user.get("user_id")
        result = await highlight_service.create_student_highlight(
            student_id, created_by_member_id, request
        )

        logging.info(
            f"[Student Router] [CreateStudentHighlight] Successfully created highlight: {result.highlight_id} for student: {student_id}"
        )

        return Response(
            code=201, message="Student highlight created successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [CreateStudentHighlight] Error creating highlight for student_id {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [CreateStudentHighlight] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student highlight creation",
        )


@router.get(
    "/{student_id}/highlights", response_model=Response[StudentHighlightListResponse]
)
async def list_student_highlights_handler(
    student_id: str,
    page: int = 1,
    page_size: int = 10,
    category: Optional[str] = None,
    q: Optional[str] = None,
):
    """
    List student highlights with pagination, category filter, and text search
    """
    logging.info(
        f"[Student Router] [ListStudentHighlights] Listing highlights for student_id: {student_id}, page: {page}, page_size: {page_size}, category: {category}, q: {q}"
    )
    try:
        if not student_id or not student_id.strip():
            raise HTTPException(status_code=400, detail="Student ID is required")

        result = await highlight_service.list_student_highlights(
            student_id, page, page_size, category, q
        )

        logging.info(
            f"[Student Router] [ListStudentHighlights] Successfully retrieved {len(result.highlight_list)} highlights for student_id: {student_id}"
        )

        return Response(
            code=200, message="Student highlights retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [ListStudentHighlights] Error listing highlights for student_id {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [ListStudentHighlights] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student highlights retrieval",
        )


@router.patch(
    "/highlights/{highlight_id}", response_model=Response[StudentHighlightResponse]
)
async def update_student_highlight_handler(
    highlight_id: str, request: StudentHighlightUpdateRequest
):
    """
    Update a student highlight
    """
    logging.info(
        f"[Student Router] [UpdateStudentHighlight] Updating highlight: {highlight_id}"
    )
    try:
        if not highlight_id or not highlight_id.strip():
            raise HTTPException(status_code=400, detail="Highlight ID is required")

        result = await highlight_service.update_student_highlight(highlight_id, request)

        logging.info(
            f"[Student Router] [UpdateStudentHighlight] Successfully updated highlight: {highlight_id}"
        )

        return Response(
            code=200, message="Student highlight updated successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [UpdateStudentHighlight] Error updating highlight {highlight_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [UpdateStudentHighlight] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student highlight update",
        )
