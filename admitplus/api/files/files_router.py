import logging
import traceback

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
)

from admitplus.dependencies.role_check import get_current_user
from admitplus.api.files.file_schema import (
    FileListRequest,
    FileListResponse,
    FileStorageInfoResponse,
    FileType,
    FileUploadResponse,
)
from admitplus.common.response_schema import OperationSuccessResponse, Response
from admitplus.api.files.file_service import FileService


file_service = FileService()
router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=Response[FileUploadResponse])
async def upload_file_handler(
    file: UploadFile = File(..., description="File to upload"),
    file_type: FileType = Form(..., description="Type of files"),
    student_id: str = Form(
        None, description="Student ID (if associated with students)"
    ),
    application_id: str = Form(
        None, description="Application ID (if associated with applications)"
    ),
    agency_id: str = Form(None, description="Agency ID (if associated with agencies)"),
    description: str = Form(None, description="File description"),
    current_user: dict = Depends(get_current_user),
):
    """
    Simple files upload: upload files directly to GCS and store metadata in MongoDB
    """
    user_id = current_user.get("user_id", "unknown")
    logging.info(
        f"[File Router] [Upload File] Starting files upload for user {user_id}"
    )
    logging.info(
        f"[File Router] [Upload File] File: {file.filename}, Type: {file_type}, Size: {file.size if hasattr(file, 'size') else 'unknown'}"
    )

    try:
        # Validate files size (max 50MB)
        file_content = await file.read()
        file_size = len(file_content)
        logging.info(
            f"[File Router] [Upload File] File content read, size: {file_size} bytes"
        )

        if file_size > 50 * 1024 * 1024:  # 50MB
            logging.warning(
                f"[File Router] [Upload File] File size {file_size} bytes exceeds 50MB limit for user {user_id}"
            )
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

        # Validate files type
        if not file.content_type:
            logging.warning(
                f"[File Router] [Upload File] Missing content type for files {file.filename} from user {user_id}"
            )
            raise HTTPException(status_code=400, detail="File content type is required")

        logging.info(
            f"[File Router] [Upload File] Validation passed, proceeding with upload"
        )
        logging.info(
            f"[File Router] [Upload File] Upload parameters - Student: {student_id}, Application: {application_id}, Agency: {agency_id}"
        )

        result = await file_service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type,
            file_type=file_type,
            uploaded_by=user_id,
            student_id=student_id,
            application_id=application_id,
            agency_id=agency_id,
            description=description,
        )

        logging.info(
            f"[File Router] [Upload File] Successfully uploaded file {result.file_id} for user {user_id}"
        )
        logging.info(f"[File Router] [Upload File] Storage path: {result.storage_path}")

        return Response(code=200, message="File uploaded successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[File Router] [Upload File] Unexpected error for user {user_id}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{file_id}", response_model=Response[FileStorageInfoResponse])
async def get_file_metadata_handler(
    file_id: str = Path(..., description="File ID"),
):
    """
    Get file storage info by file ID
    """
    logging.info(
        f"[File Router] [Get File Info] Starting storage info retrieval for file {file_id}"
    )

    try:
        result = await file_service.get_file_info(file_id)

        if not result:
            logging.warning(f"[File Router] [Get File Info] File {file_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

        logging.info(
            f"[File Router] [Get File Info] Successfully retrieved storage info for file {file_id}"
        )
        logging.info(
            f"[File Router] [Get File Info] File details - Size: {result.size_bytes} bytes, Status: {result.status}"
        )

        return Response(
            code=200, message="File storage info retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[File Router] [Get File Info] Unexpected error for file {file_id}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{file_id}/download")
async def download_file_handler(
    file_id: str = Path(..., description="File ID"),
):
    """
    Generate presigned URL for files download
    """
    logging.info(
        f"[File Router] [Download File] Starting download URL generation for files {file_id}"
    )

    try:
        download_url = await file_service.generate_download_url(file_id)

        if not download_url:
            logging.warning(
                f"[File Router] [Download File] File {file_id} not found or not available for download"
            )
            raise HTTPException(
                status_code=404, detail="File not found or not available for download"
            )

        logging.info(
            f"[File Router] [Download File] Successfully generated download URL for files {file_id}"
        )
        logging.info(
            f"[File Router] [Download File] Download URL: {download_url[:100]}..."
        )  # Log first 100 chars for security

        return Response(
            code=200,
            message="Download URL generated successfully",
            data={"download_url": download_url},
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[File Router] [Download File] Unexpected error for files {file_id}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=Response[FileListResponse])
async def list_files_handler(
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(10, description="Items per page", ge=1, le=100),
    student_id: str = Query(None, description="Filter by students ID"),
):
    """
    List files with pagination and filtering

    Filters:
    - student_id: Filter by students ID
    """
    logging.info(
        f"[File Router] [List Files] Starting files list request - Page: {page}, Page Size: {page_size}, Student ID: {student_id}"
    )

    try:
        request = FileListRequest(page=page, page_size=page_size, student_id=student_id)

        logging.info(f"[File Router] [List Files] Created FileListRequest with filters")
        result = await file_service.list_files(request)

        logging.info(f"[File Router] [List Files] Successfully retrieved files list")
        logging.info(
            f"[File Router] [List Files] Result summary - Total: {result.total}, Page: {result.page}, Page Size: {result.page_size}, Has Next: {result.has_next}, Files Count: {len(result.files)}"
        )

        return Response(code=200, message="Files retrieved successfully", data=result)
    except Exception as e:
        logging.error(
            f"[File Router] [List Files] Unexpected error: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{file_id}", response_model=Response[OperationSuccessResponse])
async def delete_file_handler(
    file_id: str = Path(..., description="File ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Hard delete a file: delete GCS blob and MongoDB document
    """
    user_id = current_user.get("user_id", "unknown")
    logging.info(
        f"[File Router] [Delete File] Starting file deletion for file {file_id} by user {user_id}"
    )

    try:
        success = await file_service.delete_file(file_id, user_id)

        if not success:
            logging.warning(
                f"[File Router] [Delete File] File {file_id} not found for user {user_id}"
            )
            raise HTTPException(status_code=404, detail="File not found")

        logging.info(
            f"[File Router] [Delete File] Successfully deleted file {file_id} by user {user_id}"
        )

        return Response(
            code=200,
            message="File deleted successfully",
            data=OperationSuccessResponse(
                success=True, message="File deleted successfully"
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[File Router] [Delete File] Unexpected error for file {file_id} by user {user_id}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
