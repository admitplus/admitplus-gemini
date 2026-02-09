import logging
from datetime import datetime, timedelta

from fastapi import HTTPException

from .invite_repo import InviteRepo
from admitplus.api.agency.agency_profile_repo import AgencyRepo
from .user_profile_repo import UserRepo
from .invite_schema import (
    InviteRequest,
    InviteResponse,
    AcceptInviteRequest,
    AcceptInviteResponse,
    InviteType,
    InviteStatus,
)
from admitplus.utils.crypto_utils import generate_invite_token, generate_uuid


class InviteService:
    def __init__(self):
        self.invite_repo = InviteRepo()
        self.agency_repo = AgencyRepo()
        self.user_repo = UserRepo()
        logging.info(f"[Invite Service] Initialized with repositories")

    async def create_agency_invite(
        self, request: InviteRequest, created_by: str
    ) -> InviteResponse:
        """
        Create an invitation for a users to join an agencies
        """
        try:
            logging.info(
                f"[Invite Service] [Create Agency Invite] Creating invite for {request.email} to join agencies {request.agency_id}"
            )

            # 1. Validate input parameters
            if not request.email or not request.email.strip():
                logging.warning(
                    f"[Invite Service] [Create Agency Invite] Missing email for agencies {request.agency_id}"
                )
                raise HTTPException(status_code=400, detail="Email is required")

            if not request.agency_id or not request.agency_id.strip():
                logging.warning(
                    f"[Invite Service] [Create Agency Invite] Missing agency_id for email {request.email}"
                )
                raise HTTPException(status_code=400, detail="Agency ID is required")

            if not request.role:
                logging.warning(
                    f"[Invite Service] [Create Agency Invite] Missing role for email {request.email} and agencies {request.agency_id}"
                )
                raise HTTPException(status_code=400, detail="Role is required")

            # 2. Check if agencies exists
            agency = await self.agency_repo.find_agency_by_id(request.agency_id)
            if not agency:
                logging.warning(
                    f"[Invite Service] [Create Agency Invite] Agency {request.agency_id} not found"
                )
                raise HTTPException(status_code=404, detail="Agency not found")

            logging.info(
                f"[Invite Service] [Create Agency Invite] Agency {request.agency_id} found: {agency.name}"
            )

            # 3. Check if users already has a pending invite
            existing_invite = await self.invite_repo.find_pending_invite(
                request.email, request.agency_id
            )
            if existing_invite:
                logging.warning(
                    f"[Invite Service] [Create Agency Invite] User {request.email} already has pending invite for agencies {request.agency_id}"
                )
                raise HTTPException(
                    status_code=409,
                    detail="User already has a pending invite for this agencies",
                )

            logging.info(
                f"[Invite Service] [Create Agency Invite] No existing invite found for {request.email}"
            )

            # 4. Generate invite token and ID
            invite_token = generate_invite_token()
            invite_id = generate_uuid()
            logging.info(
                f"[Invite Service] [Create Agency Invite] Generated invite_id: {invite_id}"
            )

            # 5. Create invite data
            invite_data = {
                "invite_id": invite_id,
                "email": request.email.strip(),
                "role": request.role,
                "agency_id": request.agency_id,
                "invite_type": InviteType.AGENCY,
                "status": "pending",
                "message": request.message.strip() if request.message else None,
                "permissions": request.permissions if request.permissions else [],
                "token": invite_token,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
            }

            # 6. Save invite to database
            result = await self.invite_repo.create_invite(invite_data)
            if not result:
                logging.error(
                    f"[Invite Service] [Create Agency Invite] Failed to save invite to database for {request.email}"
                )
                raise HTTPException(status_code=500, detail="Failed to create invite")

            logging.info(
                f"[Invite Service] [Create Agency Invite] Successfully saved invite to database: {result}"
            )

            # 7. Store token in Redis for quick validation
            await self.invite_repo.set_invite_token(
                invite_token, invite_id, 7 * 24 * 3600, "agencies"
            )  # 7 days
            logging.info(
                f"[Invite Service] [Create Agency Invite] Successfully stored token in Redis"
            )

            # 8. Return response
            logging.info(
                f"[Invite Service] [Create Agency Invite] Successfully created agencies invite for {request.email} to agencies {request.agency_id}"
            )
            return InviteResponse(
                invite_id=invite_id,
                email=request.email,
                role=request.role,
                agency_id=request.agency_id,
                status=InviteStatus.PENDING,
                message=request.message,
                token=invite_token,
                created_at=invite_data["created_at"],
                expires_at=invite_data["expires_at"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Invite Service] [Create Agency Invite] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to create agencies invite"
            )

    async def create_student_invite(
        self, student_id: str, email: str, teacher_id: str
    ) -> dict:
        """
        Create an invitation for a students to join the platform
        """
        try:
            logging.info(
                f"[Invite Service] [Create Student Invite] Creating invite for students {student_id}"
            )

            # 1. Validate input parameters
            if not student_id or not student_id.strip():
                logging.warning(
                    f"[Invite Service] [Create Student Invite] Missing student_id for email {email}"
                )
                raise HTTPException(status_code=400, detail="Student ID is required")

            if not email or not email.strip():
                logging.warning(
                    f"[Invite Service] [Create Student Invite] Missing email for students {student_id}"
                )
                raise HTTPException(status_code=400, detail="Email is required")

            if not teacher_id or not teacher_id.strip():
                logging.warning(
                    f"[Invite Service] [Create Student Invite] Missing teacher_id for students {student_id}"
                )
                raise HTTPException(status_code=400, detail="Teacher ID is required")

            # 2. Generate invite token and ID
            invite_token = generate_invite_token()
            invite_id = generate_uuid()
            logging.info(
                f"[Invite Service] [Create Student Invite] Generated invite_id: {invite_id}"
            )

            # 3. Create students invite data
            invite_data = {
                "invite_id": invite_id,
                "student_id": student_id.strip(),
                "email": email.strip(),
                "teacher_id": teacher_id.strip(),
                "invite_type": InviteType.STUDENT,
                "status": "pending",
                "token": invite_token,
                "created_by": teacher_id.strip(),
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
            }

            # 4. Save invite to database
            result = await self.invite_repo.create_invite(invite_data)
            if not result:
                logging.error(
                    f"[Invite Service] [Create Student Invite] Failed to save invite to database for students {student_id}"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to create students invite"
                )

            logging.info(
                f"[Invite Service] [Create Student Invite] Successfully saved invite to database: {result}"
            )

            # 5. Store token in Redis for quick validation
            await self.invite_repo.set_invite_token(
                invite_token, invite_id, 7 * 24 * 3600, "students"
            )  # 7 days
            logging.info(
                f"[Invite Service] [Create Student Invite] Successfully stored token in Redis"
            )

            # 6. Return response
            logging.info(
                f"[Invite Service] [Create Student Invite] Successfully created students invite for {email} (student_id: {student_id})"
            )
            return {
                "invite_id": invite_id,
                "student_id": student_id,
                "email": email,
                "token": invite_token,
                "expires_at": invite_data["expires_at"],
            }

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Invite Service] [Create Student Invite] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to create students invite"
            )

    async def accept_invite(self, request: AcceptInviteRequest) -> AcceptInviteResponse:
        """
        Accept an invitation (agencies or students)
        """
        try:
            logging.info(
                f"[Invite Service] [Accept Invite] Accepting invite with token {request.token}"
            )

            # 1. Validate input parameters
            if not request.token or not request.token.strip():
                logging.warning(
                    f"[Invite Service] [Accept Invite] Missing token in request"
                )
                raise HTTPException(status_code=400, detail="Token is required")

            # 2. Get invite from token
            invite = await self.invite_repo.find_invite_by_token(request.token.strip())
            if not invite:
                logging.warning(
                    f"[Invite Service] [Accept Invite] No invite found for token"
                )
                raise HTTPException(
                    status_code=404, detail="Invalid or expired invite token"
                )

            logging.info(
                f"[Invite Service] [Accept Invite] Found {invite.get('invite_type', 'unknown')} invite for {invite.get('email', 'unknown email')}"
            )

            # 3. Validate invite status and expiry
            if invite["status"] != "pending":
                logging.warning(
                    f"[Invite Service] [Accept Invite] Invite {invite['invite_id']} is no longer pending (status: {invite['status']})"
                )
                raise HTTPException(status_code=400, detail="Invite is no longer valid")

            if datetime.utcnow() > invite["expires_at"]:
                logging.warning(
                    f"[Invite Service] [Accept Invite] Invite {invite['invite_id']} has expired (expired_at: {invite['expires_at']})"
                )
                raise HTTPException(status_code=400, detail="Invite has expired")

            logging.info(
                f"[Invite Service] [Accept Invite] Invite {invite['invite_id']} is valid and not expired"
            )

            # 4. Process based on invite type
            invite_type = invite.get("_collection")
            if invite_type == "agencies":
                logging.info(
                    f"[Invite Service] [Accept Invite] Processing agencies invite for {invite['email']}"
                )
                return await self._accept_agency_invite(request, invite)
            elif invite_type == "students":
                logging.info(
                    f"[Invite Service] [Accept Invite] Processing students invite for {invite['email']}"
                )
                return await self._accept_student_invite(request, invite)
            else:
                logging.error(
                    f"[Invite Service] [Accept Invite] Unknown invite type: {invite_type}"
                )
                raise HTTPException(status_code=400, detail="Unknown invite type")

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Invite Service] [Accept Invite] Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to accept invite")

    async def _accept_agency_invite(
        self, request: AcceptInviteRequest, invite: dict
    ) -> AcceptInviteResponse:
        """
        Accept agencies invite
        """
        try:
            logging.info(
                f"[Invite Service] [Accept Agency Invite] Processing agencies invite for {invite['email']}"
            )

            # 1. Generate user_id if not provided
            if not request.user_id:
                request.user_id = generate_uuid()
                logging.info(
                    f"[Invite Service] [Accept Agency Invite] Generated new user_id: {request.user_id}"
                )
            else:
                logging.info(
                    f"[Invite Service] [Accept Agency Invite] Using provided user_id: {request.user_id}"
                )

            # 2. Create new users
            user_data = {
                "user_id": request.user_id,
                "email": invite["email"],
                "role": "agencies",  # Default role for invited users
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }

            result = await self.user_repo.create_user(user_data)
            if not result:
                logging.error(
                    f"[Invite Service] [Accept Agency Invite] Failed to create users for {invite['email']}"
                )
                raise HTTPException(status_code=500, detail="Failed to create users")

            logging.info(
                f"[Invite Service] [Accept Agency Invite] Successfully created users: {result}"
            )

            # 3. Create agencies membership
            membership_data = {
                "user_id": request.user_id,
                "agency_id": invite["agency_id"],
                "role": invite["role"],
                "status": "active",
                "joined_at": datetime.utcnow(),
                "permissions": invite.get(
                    "permissions", []
                ),  # Use permissions from invite if available
            }

            result = await self.agency_repo.create_agency_membership(membership_data)
            if not result:
                logging.error(
                    f"[Invite Service] [Accept Agency Invite] Failed to create agencies membership for users {request.user_id}"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to create agencies membership"
                )

            logging.info(
                f"[Invite Service] [Accept Agency Invite] Successfully created agencies membership: {result}"
            )

            # 4. Update invite status
            await self.invite_repo.update_invite_status(invite["invite_id"], "accepted")
            logging.info(
                f"[Invite Service] [Accept Agency Invite] Updated invite status to accepted"
            )

            # 5. Remove token from Redis
            await self.invite_repo.delete_invite_token(request.token)
            logging.info(
                f"[Invite Service] [Accept Agency Invite] Removed token from Redis"
            )

            # 6. Return response
            logging.info(
                f"[Invite Service] [Accept Agency Invite] Successfully accepted agencies invite for {invite['email']}"
            )
            return AcceptInviteResponse(
                success=True,
                message="Agency invite accepted successfully",
                user_id=request.user_id,
                invite_type=InviteType.AGENCY,
                agency_id=invite["agency_id"],
                role=invite["role"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Invite Service] [Accept Agency Invite] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to accept agencies invite"
            )

    async def _accept_student_invite(
        self, request: AcceptInviteRequest, invite: dict
    ) -> AcceptInviteResponse:
        """
        Accept students invite
        """
        try:
            logging.info(
                f"[Invite Service] [Accept Student Invite] Processing students invite for {invite['email']}"
            )

            # 1. For students invites, the users account was already created with student_id as user_id
            # We just need to activate the account
            student_user_id = invite["student_id"]  # Use student_id as user_id
            logging.info(
                f"[Invite Service] [Accept Student Invite] Using student_id as user_id: {student_user_id}"
            )

            # 2. Activate the users account
            result = await self.user_repo.update_user_status(student_user_id, True)
            if result == 0:
                logging.error(
                    f"[Invite Service] [Accept Student Invite] Failed to activate users account for {student_user_id}"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to activate users account"
                )

            logging.info(
                f"[Invite Service] [Accept Student Invite] Successfully activated users account"
            )

            # 3. Update invite status
            await self.invite_repo.update_invite_status(invite["invite_id"], "accepted")
            logging.info(
                f"[Invite Service] [Accept Student Invite] Updated invite status to accepted"
            )

            # 4. Remove token from Redis
            await self.invite_repo.delete_invite_token(request.token)
            logging.info(
                f"[Invite Service] [Accept Student Invite] Removed token from Redis"
            )

            # 5. Return response
            logging.info(
                f"[Invite Service] [Accept Student Invite] Successfully accepted students invite for {invite['email']}"
            )
            return AcceptInviteResponse(
                success=True,
                message="Student invite accepted successfully",
                user_id=student_user_id,
                invite_type=InviteType.STUDENT,
                student_id=invite["student_id"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Invite Service] [Accept Student Invite] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to accept students invite"
            )
