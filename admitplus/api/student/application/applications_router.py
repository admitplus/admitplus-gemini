import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Body, Path

from admitplus.common.response_schema import Response
from admitplus.dependencies.role_check import get_current_user
from ..schemas.application.application_schema import (
    StudentApplicationResponse,
    StudentApplicationCreateRequest,
    StudentApplicationListResponse,
    StudentApplicationDetailResponse,
    StudentApplicationUpdateRequest,
)
from .application_service import ApplicationService


application_service = ApplicationService()
router = APIRouter(prefix="", tags=["Applications"])


@router.post(
    "/students/{student_id}/applications",
    response_model=Response[StudentApplicationResponse],
)
async def create_application_handler(
    student_id: str,
    request: StudentApplicationCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create an application for a student
    """
    logging.info(
        f"[Application Router] [Create Application] Creating application for student {student_id}"
    )
    try:
        result = await application_service.create_application(
            student_id=student_id, request=request, created_by=current_user["user_id"]
        )
        logging.info(
            f"[Application Router] [Create Application] Successfully created application {result.application_id} for student {student_id}"
        )
        return Response(
            code=201, message="Application created successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Application Router] [Create Application] Error creating application for student {student_id}: {str(e)}"
        )
        logging.error(
            f"[Application Router] [Create Application] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while creating application"
        )


@router.get(
    "/students/{student_id}/applications",
    response_model=Response[StudentApplicationListResponse],
)
async def list_applications_handler(
    student_id: str = Path(..., description="student ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get applications by student ID
    """
    logging.info(
        f"[Application Router] [List Applications] Getting applications for student {student_id}"
    )
    try:
        result = await application_service.list_applications(student_id)
        logging.info(
            f"[Application Router] [List Applications] Successfully retrieved {len(result.application_list)} applications for student {student_id}"
        )
        return Response(
            code=200, message="Applications retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Application Router] [List Applications] Error getting applications for student {student_id}: {str(e)}"
        )
        logging.error(
            f"[Application Router] [List Applications] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving applications",
        )


@router.get(
    "/applications/{application_id}",
    response_model=Response[StudentApplicationDetailResponse],
)
async def get_application_handler(
    application_id: str = Path(..., description="Application ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get one application by ID
    """
    logging.info(
        f"[Application Router] [Get Application] Getting application {application_id}"
    )
    try:
        result = await application_service.get_application(application_id)
        logging.info(
            f"[Application Router] [Get Application] Successfully retrieved application {application_id}"
        )
        return Response(
            code=200, message="Application retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Application Router] [Get Application] Error getting application {application_id}: {str(e)}"
        )
        logging.error(
            f"[Application Router] [Get Application] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while retrieving application"
        )


@router.patch(
    "/applications/{application_id}",
    response_model=Response[StudentApplicationDetailResponse],
)
async def update_application_handler(
    application_id: str = Path(..., description="Application ID"),
    request: StudentApplicationUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update application
    """
    logging.info(
        f"[Application Router] [Update Application] Updating application {application_id}"
    )
    try:
        result = await application_service.update_application(
            application_id, request, current_user["user_id"]
        )
        logging.info(
            f"[Application Router] [Update Application] Successfully updated application {application_id}"
        )
        return Response(
            code=200, message="Application updated successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Application Router] [Update Application] Error updating application {application_id}: {str(e)}"
        )
        logging.error(
            f"[Application Router] [Update Application] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while updating application"
        )


@router.delete(
    "/applications/{application_id}",
    response_model=Response[StudentApplicationDetailResponse],
)
async def delete_application_handler(
    application_id: str = Path(..., description="Application ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Soft delete applications
    """
    logging.info(
        f"[Application Router] [Delete Application] Soft deleting applications {application_id}"
    )
    try:
        result = await application_service.delete_application(
            application_id, current_user["user_id"]
        )
        logging.info(
            f"[Application Router] [Delete Application] Successfully deleted applications {application_id}"
        )
        return Response(
            code=200, message="Application deleted successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Application Router] [Delete Application] Error deleting applications {application_id}: {str(e)}"
        )
        logging.error(
            f"[Application Router] [Delete Application] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while deleting applications"
        )
