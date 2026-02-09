import logging
import traceback
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from admitplus.config import settings
from admitplus.dependencies.role_check import get_current_user

from admitplus.common.response_schema import Response
from .agency_schema import (
    AgencyMemberListResponse,
    AgencyMemberQueryRequest,
    InviteMemberRequest,
    UpdateMemberRequest,
)
from admitplus.api.student.schemas.application.application_schema_v1 import (
    ApplicationListResponse,
    ApplicationQueryRequest,
)
from admitplus.api.student.schemas.student_schema import StudentListResponse
from admitplus.api.agency.agency_service import AgencyService
from admitplus.api.agency.agency_members_service import AgencyMembersService

agency_service = AgencyService()
agency_members_service = AgencyMembersService()

router = APIRouter(prefix="/agencies", tags=["Agency Members"])


@router.get("/{agency_id}/members", response_model=Response[AgencyMemberListResponse])
async def get_agency_members_handler(
    agency_id: str,
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    Get agencies members with filtering and pagination
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
        settings.USER_ROLE_AGENCY_MEMBER,
    ]:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only agencies users can view members",
        )

    logging.info(
        f"[Agency Router] [Get Agency Members] Getting members for agencies {agency_id}"
    )
    try:
        request = AgencyMemberQueryRequest(
            role=role, status=status, search=search, page=page, page_size=page_size
        )

        result = await agency_members_service.get_agency_members(agency_id, request)
        logging.info(
            f"[Agency Router] [Get Agency Members] Successfully retrieved members for agencies {agency_id}"
        )
        return Response(
            code=200, message="Agency members retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Get Agency Members] Error getting members for agencies {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Get Agency Members] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving agencies members",
        )


@router.post("/{agency_id}/members/invite", response_model=Response[dict])
async def invite_member_handler(
    agency_id: str,
    request: InviteMemberRequest,
    req: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Invite a member to join an agencies
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
    ]:
        raise HTTPException(
            status_code=403, detail="Access denied. Only admin users can invite members"
        )

    logging.info(
        f"[Agency Router] [Invite Member] Inviting member to agencies {agency_id}"
    )
    try:
        result = await agency_members_service.invite_member(
            agency_id, request, current_user["user_id"], req.base_url
        )
        logging.info(
            f"[Agency Router] [Invite Member] Successfully invited member to agencies {agency_id}"
        )
        return Response(code=200, message="Member invited successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Invite Member] Error inviting member to agencies {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Invite Member] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while inviting member"
        )


@router.get("/{agency_id}/members/{member_id}", response_model=Response[dict])
async def get_member_detail_handler(
    agency_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a member's detail by agency_id and member_id
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
        settings.USER_ROLE_AGENCY_MEMBER,
    ]:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only admin users and agency members can view member details",
        )

    logging.info(
        f"[Agency Router] [Get Member Detail] Getting member {member_id} from agency {agency_id}"
    )
    try:
        result = await agency_members_service.get_member_detail(agency_id, member_id)
        logging.info(
            f"[Agency Router] [Get Member Detail] Successfully retrieved member {member_id} from agency {agency_id}"
        )
        return Response(
            code=200, message="Member detail retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Get Member Detail] Error getting member {member_id} from agency {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Get Member Detail] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving member detail",
        )


@router.patch("/{agency_id}/members/{member_id}", response_model=Response[dict])
async def update_member_handler(
    agency_id: str,
    member_id: str,
    request: UpdateMemberRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Update a member's role, status, or permissions
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
    ]:
        raise HTTPException(
            status_code=403, detail="Access denied. Only admin users can update members"
        )

    logging.info(
        f"[Agency Router] [Update Member] Updating member {member_id} in agencies {agency_id}"
    )
    try:
        result = await agency_members_service.update_member(
            agency_id, member_id, request
        )
        logging.info(
            f"[Agency Router] [Update Member] Successfully updated member {member_id} in agencies {agency_id}"
        )
        return Response(code=200, message="Member updated successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Update Member] Error updating member {member_id} in agencies {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Update Member] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while updating member"
        )


@router.delete("/{agency_id}/members/{member_id}", response_model=Response[dict])
async def remove_member_handler(
    agency_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Remove a member from an agencies (soft delete)
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
    ]:
        raise HTTPException(
            status_code=403, detail="Access denied. Only admin users can remove members"
        )

    logging.info(
        f"[Agency Router] [Remove Member] Removing member {member_id} from agencies {agency_id}"
    )
    try:
        result = await agency_members_service.remove_member(agency_id, member_id)
        logging.info(
            f"[Agency Router] [Remove Member] Successfully removed member {member_id} from agencies {agency_id}"
        )
        return Response(code=200, message="Member removed successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Remove Member] Error removing member {member_id} from agencies {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Remove Member] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while removing member"
        )


@router.get(
    "/members/{member_id}/students", response_model=Response[StudentListResponse]
)
async def get_agency_member_students_handler(
    member_id: str,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    Get students assigned to a member based on student_assignments
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
        settings.USER_ROLE_AGENCY_MEMBER,
    ]:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only agency users can view member students",
        )

    logging.info(
        f"[Agency Router] [Get Agency Member Students] Getting students for member_id: {member_id}"
    )
    try:
        result = await agency_members_service.get_agency_member_students(
            member_id, search, page, page_size
        )
        logging.info(
            f"[Agency Router] [Get Agency Member Students] Successfully retrieved {len(result.student_list)} students for member_id: {member_id}"
        )
        return Response(
            code=200, message="Member students retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Get Agency Member Students] Error getting students for member_id {member_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Get Agency Member Students] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving member students",
        )


@router.get(
    "/{agency_id}/members/applications",
    response_model=Response[ApplicationListResponse],
)
async def get_agency_applications_handler(
    agency_id: str,
    status: Optional[str] = None,
    owner_uid: Optional[str] = None,
    due_before: Optional[datetime] = None,
    university_name: Optional[str] = None,
    program_name: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    Get applications for an agencies with filtering and pagination
    """
    if current_user.get("role") not in [
        settings.USER_ROLE_ADMIN,
        settings.USER_ROLE_AGENCY_ADMIN,
        settings.USER_ROLE_AGENCY_MEMBER,
    ]:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only agencies users can view applications",
        )

    logging.info(
        f"[Agency Router] [Get Agency Applications] Getting applications for agencies {agency_id}"
    )
    try:
        request = ApplicationQueryRequest(
            status=status,
            owner_uid=owner_uid,
            due_before=due_before,
            university_name=university_name,
            program_name=program_name,
            search=search,
            page=page,
            page_size=page_size,
        )

        result = await agency_members_service.get_agency_applications(
            agency_id, request
        )
        logging.info(
            f"[Agency Router] [Get Agency Applications] Successfully retrieved applications for agencies {agency_id}"
        )
        return Response(
            code=200, message="Agency applications retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Agency Router] [Get Agency Applications] Error getting applications for agencies {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Agency Router] [Get Agency Applications] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving agencies applications",
        )
