import logging
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from admitplus.dependencies.role_check import get_current_user
from admitplus.common.response_schema import Response
from .file_schema import FileMetadata, FileType, FileListRequest
from .file_service import FileService


router = APIRouter(prefix="/users", tags=["User Avatar"])
file_service = FileService()


@router.post("/{user_id}/avatar", response_model=Response[FileMetadata])
async def upload_avatar_handler(
    user_id: str, file: UploadFile = File(...), user=Depends(get_current_user)
):
    """
    Upload users avatar files
    Returns presigned upload URL for direct upload to GCP
    """
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to perform this action"
        )

        logging.info(
            f"[Avatar Router] [Upload Avatar] Starting avatar upload for users {user_id}"
        )
    try:
        # Read files content
        file_content = await file.read()

        # Upload files directly
        result = await file_service.upload_file(
            file_content=file_content,
            file_name=file.filename or "avatar",
            content_type=file.content_type or "image/jpeg",
            file_type=FileType.avatar,
            uploaded_by=user_id,
            student_id=user_id,  # Pass users ID as student_id
        )

        logging.info(
            f"[Avatar Router] [Upload Avatar] Successfully uploaded avatar for users {user_id}"
        )
        return Response(code=201, message="Avatar uploaded successfully", data=result)
    except ValueError as e:
        logging.error(
            f"[Avatar Router] [Upload Avatar] Validation error for users {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Avatar Router] [Upload Avatar] Failed to create avatar upload for users {user_id}: {str(e)}"
        )
        logging.error(
            f"[Avatar Router] [Upload Avatar] Error details: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during avatar upload"
        )


@router.get("/{user_id}/avatar", response_model=Response[Optional[FileMetadata]])
async def get_avatar_handler(user_id: str, user=Depends(get_current_user)):
    """
    Get users avatar information by searching for avatar files
    """
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to perform this action"
        )

    logging.info(f"[Avatar Router] [Get Avatar] Getting avatar for users {user_id}")
    try:
        # Use files list functionality to find avatar

        request = FileListRequest(
            page=1, page_size=1, file_type=FileType.avatar, student_id=user_id
        )

        result = await file_service.list_files(request)

        avatar_data = result.files[0] if result.files else None

        logging.info(
            f"[Avatar Router] [Get Avatar] Successfully retrieved avatar for users {user_id}"
        )
        return Response(
            code=200, message="Avatar retrieved successfully", data=avatar_data
        )
    except Exception as e:
        logging.error(
            f"[Avatar Router] [Get Avatar] Failed to get avatar for users {user_id}: {str(e)}"
        )
        logging.error(
            f"[Avatar Router] [Get Avatar] Error details: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during avatar retrieval"
        )


@router.delete("/{user_id}/avatar", response_model=Response[Optional[FileMetadata]])
async def delete_avatar_handler(user_id: str, user=Depends(get_current_user)):
    """
    Delete users avatar by finding and deleting avatar files
    """
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to perform this action"
        )

    logging.info(f"[Avatar Router] [Delete Avatar] Deleting avatar for users {user_id}")
    try:
        # First find the users's avatar files
        request = FileListRequest(
            page=1, page_size=10, file_type=FileType.avatar, student_id=user_id
        )

        files_result = await file_service.list_files(request)

        if not files_result.files:
            logging.info(
                f"[Avatar Router] [Delete Avatar] No avatar found for users {user_id}"
            )
            return Response(code=200, message="No avatar found to delete", data=None)

        # Delete the found avatar files
        deleted_files = []
        for file_metadata in files_result.files:
            result = await file_service.delete_file(file_metadata.file_id, user_id)
            if result:
                deleted_files.append(result)

        logging.info(
            f"[Avatar Router] [Delete Avatar] Successfully deleted {len(deleted_files)} avatar files for users {user_id}"
        )
        return Response(
            code=200,
            message=f"Avatar deleted successfully ({len(deleted_files)} files)",
            data=deleted_files[0] if deleted_files else None,
        )
    except Exception as e:
        logging.error(
            f"[Avatar Router] [Delete Avatar] Failed to delete avatar for users {user_id}: {str(e)}"
        )
        logging.error(
            f"[Avatar Router] [Delete Avatar] Error details: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during avatar deletion"
        )
