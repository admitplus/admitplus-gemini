import logging
import traceback
from datetime import datetime
from typing import Optional

from fastapi import HTTPException

from admitplus.database.mongo import BaseMongoCRUD
from admitplus.config import settings
from admitplus.api.user.invite_service import InviteService
from admitplus.api.user.invite_schema import InviteRequest, InviteType
from admitplus.api.student.repos.student_assignment_repo import StudentAssignmentRepo
from admitplus.api.student.repos.student_profile_repo import StudentRepo
from admitplus.api.student.student_model import StudentProfile
from .agency_schema import (
    AgencyMember,
    AgencyMemberListResponse,
    AgencyMemberQueryRequest,
    InviteMemberRequest,
    UpdateMemberRequest,
)
from admitplus.api.student.schemas.application.application_schema_v1 import (
    Application,
    ApplicationListResponse,
    ApplicationQueryRequest,
)
from admitplus.api.student.schemas.student_schema import StudentListResponse


class AgencyMembersService:
    """
    Service for managing agencies members and related operations.
    Handles member invitations, updates, removal, and applications management.
    """

    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.agency_members_collection = settings.AGENCY_MEMBERS_COLLECTION
        self.applications_collection = settings.STUDENT_APPLICATIONS_COLLECTION
        self.invite_service = InviteService()
        self.student_assignment_repo = StudentAssignmentRepo()
        self.student_repo = StudentRepo()

        logging.info(f"[Agency Members Service] Initialized with db: {self.db_name}")

    async def invite_member(
        self,
        agency_id: str,
        request: InviteMemberRequest,
        invited_by: str,
        base_url: str,
    ) -> dict:
        """
        Invite a member to join an agencies
        """
        try:
            logging.info(
                f"[Agency Members Service] [Invite Member] Inviting {request.email} to agencies {agency_id}"
            )

            # Validate input parameters
            if not agency_id or not agency_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Invite Member] Missing agency_id"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            if not request.email or not request.email.strip():
                logging.warning(
                    f"[Agency Members Service] [Invite Member] Missing email for agencies {agency_id}"
                )
                raise HTTPException(status_code=400, detail="Email is required")

            if not request.role:
                logging.warning(
                    f"[Agency Members Service] [Invite Member] Missing role for email {request.email}"
                )
                raise HTTPException(status_code=400, detail="Role is required")

            if not invited_by or not invited_by.strip():
                logging.warning(
                    f"[Agency Members Service] [Invite Member] Missing invited_by"
                )
                raise HTTPException(
                    status_code=400, detail="Invited by users ID is required"
                )

            # Convert InviteMemberRequest to InviteRequest for InviteService
            invite_request = InviteRequest(
                email=request.email,
                role=settings.USER_ROLE_AGENCY_STUDENT,
                agency_id=agency_id,
                invite_type=InviteType.AGENCY,
                message=f"You have been invited to join the agencies as a {request.role}",
                permissions=request.permissions,
            )

            # Use InviteService to create the invite
            invite_response = await self.invite_service.create_agency_invite(
                invite_request, invited_by
            )

            logging.info(
                f"[Agency Members Service] [Invite Member] Successfully created invite for {request.email}"
            )

            return {
                "invite_url": f"{base_url}invites/{invite_response.token}",
            }

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Invite Member] Error inviting {request.email}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to invite member")

    async def get_member_detail(self, agency_id: str, member_id: str) -> dict:
        """
        Get a member's detail by agency_id and member_id
        """
        try:
            logging.info(
                f"[Agency Members Service] [Get Member Detail] Getting member {member_id} from agency {agency_id}"
            )

            # Validate input parameters
            if not agency_id or not agency_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Get Member Detail] Missing agency_id"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            if not member_id or not member_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Get Member Detail] Missing member_id"
                )
                raise HTTPException(status_code=400, detail="Member ID is required")

            # Find member
            member = await self.mongo_repo.find_one(
                {"member_id": member_id, "agency_id": agency_id},
                collection_name=self.agency_members_collection,
            )

            if not member:
                logging.warning(
                    f"[Agency Members Service] [Get Member Detail] No member found with member_id: {member_id} and agency_id: {agency_id}"
                )
                raise HTTPException(status_code=404, detail="Member not found")

            # Convert to AgencyMember schema
            member_detail = AgencyMember(
                member_id=member.get("member_id", ""),
                user_id=member.get("user_id", ""),
                email=member.get("email", ""),
                first_name=member.get("first_name"),
                last_name=member.get("last_name"),
                role=member.get("role", ""),
                status=member.get("status", ""),
                permissions=member.get("permissions", []),
                joined_at=member.get("joined_at", datetime.utcnow()),
                last_active_at=member.get("last_active_at"),
            )

            logging.info(
                f"[Agency Members Service] [Get Member Detail] Successfully retrieved member {member_id}"
            )

            return member_detail.dict()

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Get Member Detail] Error getting member {member_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to get member detail")

    async def update_member(
        self, agency_id: str, member_id: str, request: UpdateMemberRequest
    ) -> dict:
        """
        Update a member's role, status, or permissions
        """
        try:
            logging.info(
                f"[Agency Members Service] [Update Member] Updating member {member_id} in agencies {agency_id}"
            )

            # Validate input parameters
            if not agency_id or not agency_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Update Member] Missing agency_id"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            if not member_id or not member_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Update Member] Missing member_id"
                )
                raise HTTPException(status_code=400, detail="Member ID is required")

            # Prepare update data
            update_data = {}
            if request.first_name is not None:
                update_data["first_name"] = request.first_name
                logging.info(
                    f"[Agency Members Service] [Update Member] Updating first_name to {request.first_name}"
                )
            if request.last_name is not None:
                update_data["last_name"] = request.last_name
                logging.info(
                    f"[Agency Members Service] [Update Member] Updating last_name to {request.last_name}"
                )
            if request.email is not None:
                update_data["email"] = request.email
                logging.info(
                    f"[Agency Members Service] [Update Member] Updating email to {request.email}"
                )
            if request.role is not None:
                update_data["role"] = request.role
                logging.info(
                    f"[Agency Members Service] [Update Member] Updating role to {request.role}"
                )
            if request.status is not None:
                update_data["status"] = request.status
                logging.info(
                    f"[Agency Members Service] [Update Member] Updating status to {request.status}"
                )
            if request.permissions is not None:
                update_data["permissions"] = request.permissions
                logging.info(
                    f"[Agency Members Service] [Update Member] Updating permissions"
                )

            if not update_data:
                logging.warning(
                    f"[Agency Members Service] [Update Member] No fields to update for member {member_id}"
                )
                raise HTTPException(status_code=400, detail="No fields to update")

            update_data["updated_at"] = datetime.utcnow()

            # Update member
            result = await self.mongo_repo.update_one(
                {"member_id": member_id, "agency_id": agency_id},
                {"$set": update_data},
                collection_name=self.agency_members_collection,
            )

            if result:
                logging.info(
                    f"[Agency Members Service] [Update Member] Successfully updated member {member_id}"
                )
            else:
                logging.warning(
                    f"[Agency Members Service] [Update Member] No member found with member_id: {member_id}"
                )

            return {
                "success": True,
                "message": "Member updated successfully",
                "member_id": member_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Update Member] Error updating member {member_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to update member")

    async def remove_member(self, agency_id: str, member_id: str) -> dict:
        """
        Remove a member from an agencies (soft delete)
        """
        try:
            logging.info(
                f"[Agency Members Service] [Remove Member] Removing member {member_id} from agencies {agency_id}"
            )

            # Validate input parameters
            if not agency_id or not agency_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Remove Member] Missing agency_id"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            if not member_id or not member_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Remove Member] Missing member_id"
                )
                raise HTTPException(status_code=400, detail="Member ID is required")

            # Soft delete by updating status
            result = await self.mongo_repo.update_one(
                {"member_id": member_id, "agency_id": agency_id},
                {
                    "$set": {
                        "status": "removed",
                        "left_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
                collection_name=self.agency_members_collection,
            )

            if result:
                logging.info(
                    f"[Agency Members Service] [Remove Member] Successfully removed member {member_id}"
                )
            else:
                logging.warning(
                    f"[Agency Members Service] [Remove Member] No member found with member_id: {member_id}"
                )

            return {
                "success": True,
                "message": "Member removed successfully",
                "member_id": member_id,
            }

        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Remove Member] Error removing member {member_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to remove member")

    async def get_agency_members(
        self, agency_id: str, request: AgencyMemberQueryRequest
    ) -> AgencyMemberListResponse:
        """
        Get agencies members with filtering and pagination
        """
        try:
            logging.info(
                f"[Agency Members Service] [Get Agency Members] Getting members for agencies {agency_id}"
            )

            # Validate input parameters
            if not agency_id or not agency_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Get Agency Members] Missing agency_id"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            # Build query
            query = {"agency_id": agency_id}
            if request.role:
                query["role"] = request.role
                logging.info(
                    f"[Agency Members Service] [Get Agency Members] Filtering by role: {request.role}"
                )
            if request.status:
                query["status"] = request.status
                logging.info(
                    f"[Agency Members Service] [Get Agency Members] Filtering by status: {request.status}"
                )
            else:
                # Exclude removed members by default
                query["status"] = {"$ne": "removed"}
                logging.info(
                    f"[Agency Members Service] [Get Agency Members] Excluding removed members by default"
                )
            if request.search:
                query["$or"] = [
                    {"email": {"$regex": request.search, "$options": "i"}},
                    {"first_name": {"$regex": request.search, "$options": "i"}},
                    {"last_name": {"$regex": request.search, "$options": "i"}},
                ]
                logging.info(
                    f"[Agency Members Service] [Get Agency Members] Filtering by search: {request.search}"
                )

            # Get members with pagination
            members, total_count = await self.mongo_repo.find_many_paginated(
                query=query,
                page=request.page,
                page_size=request.page_size,
                sort=[("joined_at", -1)],
                collection_name=self.agency_members_collection,
            )

            logging.info(
                f"[Agency Members Service] [Get Agency Members] Found {len(members)}/{total_count} members"
            )

            # Convert to response format
            member_items = []
            for member in members:
                member_id = member.get("member_id", "")
                if not member_id:
                    logging.warning(
                        f"[Agency Members Service] [Get Agency Members] Member missing member_id: {member}"
                    )

                member_items.append(
                    AgencyMember(
                        member_id=member_id,
                        user_id=member.get("user_id", ""),
                        email=member.get("email", ""),
                        first_name=member.get("first_name"),
                        last_name=member.get("last_name"),
                        role=member.get("role", ""),
                        status=member.get("status", ""),
                        permissions=member.get("permissions", []),
                        joined_at=member.get("joined_at", datetime.utcnow()),
                        last_active_at=member.get("last_active_at"),
                    )
                )

            has_next = (request.page * request.page_size) < total_count
            has_prev = request.page > 1

            logging.info(
                f"[Agency Members Service] [Get Agency Members] Returning {len(member_items)} members"
            )

            return AgencyMemberListResponse(
                members=member_items,
                total=total_count,
                page=request.page,
                page_size=request.page_size,
                has_next=has_next,
                has_prev=has_prev,
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Get Agency Members] Error getting members for agencies {agency_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to retrieve agencies members"
            )

    async def get_agency_member_students(
        self,
        member_id: str,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> StudentListResponse:
        """
        Get students assigned to a member based on student_assignments
        """
        try:
            logging.info(
                f"[Agency Members Service] [Get Agency Member Students] Getting students for member_id: {member_id}, search: {search}, page: {page}, page_size: {page_size}"
            )

            # Validate input parameters
            if not member_id or not member_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Get Agency Member Students] Missing member_id"
                )
                raise HTTPException(status_code=400, detail="Member ID is required")

            # Validate pagination parameters
            if page < 1:
                raise HTTPException(
                    status_code=400, detail="Page number must be greater than 0"
                )
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=400, detail="Page size must be between 1 and 100"
                )

            # Step 1: Get all student_ids assigned to this member from student_assignments
            student_ids = (
                await self.student_assignment_repo.find_student_ids_by_member_id(
                    member_id
                )
            )

            if not student_ids:
                logging.info(
                    f"[Agency Members Service] [Get Agency Member Students] No students assigned to member_id: {member_id}"
                )
                return StudentListResponse(
                    student_list=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    has_next=False,
                    has_prev=False,
                )

            # Step 2: Fetch students from repository with pagination and search filter
            (
                student_dicts,
                total_count,
            ) = await self.student_repo.find_students_by_student_ids(
                student_ids=student_ids, search=search, page=page, page_size=page_size
            )

            # Convert dicts to StudentProfile objects
            student_profiles = []
            for student_dict in student_dicts:
                try:
                    student_profile = StudentProfile(**student_dict)
                    student_profiles.append(student_profile)
                except Exception as e:
                    logging.warning(
                        f"[Agency Members Service] [Get Agency Member Students] Skipping invalid student data: {str(e)}"
                    )
                    continue

            # Calculate pagination info
            has_next = (page * page_size) < total_count
            has_prev = page > 1

            logging.info(
                f"[Agency Members Service] [Get Agency Member Students] Successfully retrieved {len(student_profiles)}/{total_count} students for member_id: {member_id}"
            )
            return StudentListResponse(
                student_list=student_profiles,
                total=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_prev=has_prev,
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Get Agency Member Students] Error getting students for member_id {member_id}: {str(e)}"
            )
            logging.error(
                f"[Agency Members Service] [Get Agency Member Students] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to retrieve member students"
            )

    async def get_agency_applications(
        self, agency_id: str, request: ApplicationQueryRequest
    ) -> ApplicationListResponse:
        """
        Get applications for an agencies with filtering and pagination
        """
        try:
            logging.info(
                f"[Agency Members Service] [Get Agency Applications] Getting applications for agencies {agency_id}"
            )

            # Validate input parameters
            if not agency_id or not agency_id.strip():
                logging.warning(
                    f"[Agency Members Service] [Get Agency Applications] Missing agency_id"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            # Build query
            query = {"agency_id": agency_id}
            if request.status:
                query["status"] = request.status
                logging.info(
                    f"[Agency Members Service] [Get Agency Applications] Filtering by status: {request.status}"
                )
            if request.owner_uid:
                query["owner_uid"] = request.owner_uid
                logging.info(
                    f"[Agency Members Service] [Get Agency Applications] Filtering by owner_uid: {request.owner_uid}"
                )
            if request.due_before:
                query["due_date"] = {"$lte": request.due_before}
                logging.info(
                    f"[Agency Members Service] [Get Agency Applications] Filtering by due_before: {request.due_before}"
                )
            if request.university_name:
                query["university_name"] = {
                    "$regex": request.university_name,
                    "$options": "i",
                }
                logging.info(
                    f"[Agency Members Service] [Get Agency Applications] Filtering by university: {request.university_name}"
                )
            if request.program_name:
                query["program_name"] = {
                    "$regex": request.program_name,
                    "$options": "i",
                }
                logging.info(
                    f"[Agency Members Service] [Get Agency Applications] Filtering by program: {request.program_name}"
                )
            if request.search:
                query["$or"] = [
                    {"university_name": {"$regex": request.search, "$options": "i"}},
                    {"program_name": {"$regex": request.search, "$options": "i"}},
                    {"owner_uid": {"$regex": request.search, "$options": "i"}},
                ]
                logging.info(
                    f"[Agency Members Service] [Get Agency Applications] Filtering by search: {request.search}"
                )

            # Get applications with pagination
            applications, total_count = await self.mongo_repo.find_many_paginated(
                query=query,
                page=request.page,
                page_size=request.page_size,
                sort=[("created_at", -1)],
                collection_name=self.applications_collection,
            )

            logging.info(
                f"[Agency Members Service] [Get Agency Applications] Found {len(applications)}/{total_count} applications"
            )

            # Convert to response format
            application_items = []
            for application in applications:
                application_items.append(
                    Application(
                        application_id=application.get("application_id", ""),
                        student_id=application.get("student_id", ""),
                        university_name=application.get("university_name", ""),
                        program_name=application.get("program_name", ""),
                        degree_level=application.get("degree_level", ""),
                        status=application.get("status", "draft"),
                        owner_uid=application.get("owner_uid", ""),
                        counselor_uid=application.get("counselor_uid"),
                        due_date=application.get("due_date"),
                        submitted_at=application.get("submitted_at"),
                        notes=application.get("notes"),
                        metadata=application.get("metadata", {}),
                        created_at=application.get("created_at", datetime.utcnow()),
                        updated_at=application.get("updated_at", datetime.utcnow()),
                    )
                )

            has_next = (request.page * request.page_size) < total_count
            has_prev = request.page > 1

            logging.info(
                f"[Agency Members Service] [Get Agency Applications] Returning {len(application_items)} applications"
            )

            return ApplicationListResponse(
                applications=application_items,
                total=total_count,
                page=request.page,
                page_size=request.page_size,
                has_next=has_next,
                has_prev=has_prev,
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Members Service] [Get Agency Applications] Error getting applications for agencies {agency_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to retrieve agencies applications"
            )
