import logging
import traceback

from fastapi import APIRouter, Depends, Query, Body, Path, HTTPException

from admitplus.api.files.file_schema import (
    FileAnalyzeRequest,
    FileAnalyzeResultResponse,
)
from admitplus.common.response_schema import Response
from admitplus.dependencies.role_check import get_current_user
from admitplus.api.student.schemas.student_file_schema import (
    StudentFileAttachRequest,
    StudentFileResponse,
    StudentFileListResponse,
)
from admitplus.api.student.files.student_file_service import StudentFileService

student_file_service = StudentFileService()

router = APIRouter(prefix="/students", tags=["Student Files"])


@router.post("/{student_id}/files", response_model=Response[StudentFileResponse])
async def attach_file_to_student_handler(
    student_id: str = Path(..., description="Student ID"),
    request: StudentFileAttachRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Attach a file to a student.
    The file must already be uploaded via /files/upload endpoint.
    """
    logging.info(
        f"[Student File Router] [Attach File] Request received - student_id={student_id}, file_id={request.file_id}, file_type={request.file_type}"
    )
    try:
        file_meta = await student_file_service.attach_file_to_student(
            student_id=student_id,
            request=request,
            current_member_id=current_user["user_id"],
        )
        logging.info(
            f"[Student File Router] [Attach File] Successfully attached file {request.file_id} to student {student_id}"
        )
        return Response(
            code=201, message="File attached to student successfully", data=file_meta
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student File Router] [Attach File] Error attaching file {request.file_id} to student {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student File Router] [Attach File] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while attaching file to student",
        )


@router.get("/{student_id}/files", response_model=Response[StudentFileListResponse])
async def list_student_files_handler(
    student_id: str = Path(..., description="Student ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all files for a student with pagination.
    """
    logging.info(
        f"[Student File Router] [List Files] Request received - student_id={student_id}, page={page}, page_size={page_size}"
    )
    try:
        result = await student_file_service.list_student_files(
            student_id=student_id,
            page=page,
            page_size=page_size,
            current_member_id=current_user["user_id"],
        )
        logging.info(
            f"[Student File Router] [List Files] Successfully retrieved {len(result.file_list)} files for student {student_id} (total: {result.total})"
        )
        return Response(
            code=200, message="Student files retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student File Router] [List Files] Error listing files for student {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student File Router] [List Files] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while listing student files"
        )


@router.get("/files/{student_file_id}", response_model=Response[StudentFileResponse])
async def get_student_file_metadata_handler(
    student_file_id: str = Path(..., description="Student file ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get file metadata by file_id.
    """
    logging.info(
        f"[Student File Router] [Get File Metadata] Request received - file_id={student_file_id}"
    )
    try:
        file_meta = await student_file_service.get_file_metadata(
            file_id=student_file_id,
            current_member_id=current_user["user_id"],
        )
        logging.info(
            f"[Student File Router] [Get File Metadata] Successfully retrieved metadata for file {student_file_id}"
        )
        return Response(
            code=200, message="File metadata retrieved successfully", data=file_meta
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student File Router] [Get File Metadata] Error retrieving metadata for file {student_file_id}: {str(e)}"
        )
        logging.error(
            f"[Student File Router] [Get File Metadata] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving file metadata",
        )


@router.delete("/files/{student_file_id}", response_model=Response[StudentFileResponse])
async def delete_student_file_handler(
    student_file_id: str = Path(..., description="Student file ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a student file (removes from file_metadata, files_storage, and GCS).
    """
    logging.info(
        f"[Student File Router] [Delete File] Request received - file_id={student_file_id}"
    )
    try:
        file_meta = await student_file_service.delete_student_file(
            file_id=student_file_id,
            current_member_id=current_user["user_id"],
        )
        logging.info(
            f"[Student File Router] [Delete File] Successfully deleted file {student_file_id}"
        )
        return Response(code=200, message="File deleted successfully", data=file_meta)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student File Router] [Delete File] Error deleting file {student_file_id}: {str(e)}"
        )
        logging.error(
            f"[Student File Router] [Delete File] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while deleting file"
        )


@router.post(
    "/files/{student_file_id}/analyze",
    response_model=Response[FileAnalyzeResultResponse],
)
async def analyze_student_file_handler(
    student_file_id: str = Path(..., description="Student file ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a student file and extract highlights.
    """
    logging.info(
        f"[Student File Router] [Analyze File] Request received - file_id={student_file_id}"
    )
    try:
        result = await student_file_service.analyze_student_file(
            file_id=student_file_id,
            current_member_id=current_user["user_id"],
        )
        logging.info(
            f"[Student File Router] [Analyze File] Successfully analyzed file {student_file_id} - extracted {result.extracted_text_length} chars, created {result.new_highlights_created} highlights"
        )
        return Response(code=200, message="File analyzed successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student File Router] [Analyze File] Error analyzing file {student_file_id}: {str(e)}"
        )
        logging.error(
            f"[Student File Router] [Analyze File] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while analyzing file"
        )
