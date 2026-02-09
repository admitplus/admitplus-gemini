import logging
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from admitplus.config import settings
from admitplus.dependencies.role_check import get_current_user
from .agency_schema import (
    AgencyListResponse,
    AgencyCreateRequest,
    AgencyUpdateRequest,
    AgencyResponse,
)
from admitplus.common.response_schema import Response
from admitplus.api.student.schemas.student_schema import (
    AgencyStudentsOverviewResponse,
    StudentProfile,
)
from .agency_service import AgencyService
from admitplus.api.analysis.analyze_service import AnalysisService


agency_service = AgencyService()
analysis_service = AnalysisService()


router = APIRouter(prefix="/agencies", tags=["Agency"])


@router.get("/", response_model=Response[AgencyListResponse])
async def list_agencies_handler(
    include_inactive: bool = False,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    """
    Retrieve all agencies with optional filtering and pagination.

    Args:
        include_inactive: Whether to include inactive agencies (default: False)
        page: Page number (default: 1)
        page_size: Number of items per page (default: 10)
    """
    try:
        logging.info(
            f"[Agency Router] [List Agencies] Starting, include_inactive={include_inactive}, page={page}, page_size={page_size}"
        )

        agencies_response = await agency_service.list_agencies(
            include_inactive=include_inactive, page=page, page_size=page_size
        )

        logging.info(
            f"[Agency Router] [List Agencies] Returned {len(agencies_response.AgencyList)} agencies"
        )
        return Response(
            code=200, message="Agencies retrieved successfully", data=agencies_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Agency Router] [List Agencies] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=Response[AgencyResponse])
async def create_agency_handler(
    request: AgencyCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new agencies with validation and authorization.

    Args:
        request: Agency creation request data
        current_user: Current authenticated users

    Returns:
        Response containing created agencies data

    Raises:
        HTTPException: If authorization fails or creation errors
    """
    try:
        logging.info(
            f"[Agency Router] [Create Agency] Starting creation for: {request.name}"
        )
        logging.info(
            f"[Agency Router] [Create Agency] Requested by users: {current_user.get('user_id', 'Unknown')}"
        )

        # Check authorization
        user_role = current_user.get("role")
        if user_role not in [settings.USER_ROLE_ADMIN, settings.USER_ROLE_AGENCY_ADMIN]:
            logging.warning(
                f"[Agency Router] [Create Agency] Access denied for users {current_user.get('user_id')} with role {user_role}"
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied. Only admin users can create agencies",
            )

        # Validate request data
        if not request.name or not request.name.strip():
            logging.warning(
                f"[Agency Router] [Create Agency] Invalid name provided: {request.name}"
            )
            raise HTTPException(status_code=400, detail="Agency name is required")

        if not request.slug or not request.slug.strip():
            logging.warning(
                f"[Agency Router] [Create Agency] Invalid slug provided: {request.slug}"
            )
            raise HTTPException(status_code=400, detail="Agency slug is required")

        # Validate slug format (alphanumeric and hyphens only)
        import re

        if not re.match(r"^[a-zA-Z0-9-]+$", request.slug):
            logging.warning(
                f"[Agency Router] [Create Agency] Invalid slug format: {request.slug}"
            )
            raise HTTPException(
                status_code=400,
                detail="Agency slug must contain only alphanumeric characters and hyphens",
            )

        # Create agencies
        result = await agency_service.create_agency(request)

        logging.info(
            f"[Agency Router] [Create Agency] Successfully created agencies: {result.agency_id}"
        )
        return Response(code=201, message="Agency created successfully", data=result)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Agency Router] [Create Agency] Unexpected error: {str(e)}")
        logging.error(
            f"[Agency Router] [Create Agency] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while creating agencies"
        )


@router.get("/{agency_id}", response_model=Response[AgencyResponse])
async def find_agency_handler(
    agency_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get agencies information by agencies id
    """
    try:
        logging.info(
            f"[Agency Router] [Find Agency] Received request to get agencies {agency_id}"
        )

        # Check authorization
        user_role = current_user.get("role")
        if user_role not in [
            settings.USER_ROLE_ADMIN,
            settings.USER_ROLE_AGENCY_ADMIN,
            settings.USER_ROLE_AGENCY_MEMBER,
        ]:
            logging.warning(
                f"[Agency Router] [Find Agency] Access denied for users {current_user.get('user_id')} with role {user_role}"
            )
            raise HTTPException(
                status_code=403, detail="Access denied. Insufficient permissions"
            )

        result = await agency_service.find_agency_by_id(agency_id)
        if not result:
            logging.error(
                f"[Agency Router] [Find Agency] Agency not found: {agency_id}"
            )
            raise HTTPException(status_code=404, detail="Agency not found")

        logging.info(
            f"[Agency Router] [Find Agency] Successfully retrieved agencies: {agency_id}"
        )
        return Response(code=200, message="Agency retrieved successfully", data=result)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Agency Router] [Find Agency] Error: {str(e)}")
        logging.error(
            f"[Agency Router] [Find Agency] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{agency_id}", response_model=Response[AgencyResponse])
async def update_agency_handler(
    agency_id: str,
    update_data: AgencyUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Update agencies information
    """
    try:
        logging.info(
            f"[Agency Router] [Update Agency] Received request to update agencies {agency_id}"
        )

        # Check authorization
        user_role = current_user.get("role")
        if user_role not in [settings.USER_ROLE_ADMIN, settings.USER_ROLE_AGENCY_ADMIN]:
            logging.warning(
                f"[Agency Router] [Update Agency] Access denied for users {current_user.get('user_id')} with role {user_role}"
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied. Only admin users can update agencies",
            )

        # Validate request data
        if not update_data.dict(exclude_unset=True):
            logging.warning(
                f"[Agency Router] [Update Agency] No fields to update for agencies {agency_id}"
            )
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await agency_service.update_agency(agency_id, update_data)
        if not result:
            logging.error(
                f"[Agency Router] [Update Agency] Agency not found: {agency_id}"
            )
            raise HTTPException(status_code=404, detail="Agency not found")

        logging.info(
            f"[Agency Router] [Update Agency] Successfully updated agencies: {agency_id}"
        )
        return Response(code=200, message="Agency updated successfully", data=result)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Agency Router] [Update Agency] Error: {str(e)}")
        logging.error(
            f"[Agency Router] [Update Agency] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{agency_id}/students/overview",
    response_model=Response[AgencyStudentsOverviewResponse],
)
async def get_agency_students_overview(
    agency_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(get_current_user),
):
    """
    获取机构学生的概览信息（支持分页）
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
        settings.USER_ROLE_AGENCY_MEMBER,
    ]:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only agency users can view agency students",
        )

    logging.info(
        f"[Agency Router] [Get Agency Students Overview] Getting students for agency {agency_id}"
    )
    try:
        offset = (page - 1) * size
        result = await analysis_service.get_agency_students_overview(
            agency_id=agency_id, skip=offset, limit=size, filters=None
        )

        student_profiles = [
            StudentProfile(**student_dict)
            for student_dict in result.get("students", [])
        ]

        overview_response = AgencyStudentsOverviewResponse(
            agency_id=agency_id,
            students=student_profiles,
            total_count=result.get("total_count", 0),
            total_pages=result.get("total_pages", 0),
            page=page,
            size=size,
        )

        logging.info(
            f"[Agency Router] [Get Agency Students Overview] Successfully retrieved {len(student_profiles)} students for agency {agency_id}"
        )
        return Response(
            code=200,
            message="Agency students overview retrieved successfully",
            data=overview_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Get Agency Students Overview] Error getting students for agency {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Get Agency Students Overview] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving agency students overview",
        )
