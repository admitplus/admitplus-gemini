import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import HTTPException

from .agency_profile_repo import AgencyRepo
from .agency_schema import (
    AgencyCreateRequest,
    AgencyResponse,
    AgencyListResponse,
    AgencyUpdateRequest,
    InviteContractedTeacherRequest,
)
from admitplus.utils.crypto_utils import generate_invite_token, generate_uuid
from admitplus.api.user.invite_repo import InviteRepo


class AgencyService:
    def __init__(self):
        self.agency_repo = AgencyRepo()
        self.invite_repo = InviteRepo()

    async def list_agencies(
        self, include_inactive: bool = False, page: int = 1, page_size: int = 1000
    ):
        try:
            logging.info(
                f"[Agency Service] [List Agencies] Starting, include_inactive={include_inactive}, page={page}, page_size={page_size}"
            )

            agencies_response = await self.agency_repo.find_all_agencies(
                include_inactive=include_inactive, page=page, page_size=page_size
            )

            # Additional client-side filtering if needed
            if not include_inactive and agencies_response.AgencyList:
                filtered_agencies = [
                    agency
                    for agency in agencies_response.AgencyList
                    if agency.status != "inactive"
                ]
                agencies_response.AgencyList = filtered_agencies
                logging.debug(
                    f"[Agency Service] [List Agencies] Client-side filtered to {len(filtered_agencies)} active agencies"
                )

            logging.info(
                f"[Agency Service] [List Agencies] Retrieved {len(agencies_response.AgencyList)} agencies"
            )
            return agencies_response

        except Exception as e:
            logging.error(f"[Agency Service] [List Agencies] Error: {str(e)}")
            return AgencyListResponse(AgencyList=[])

    async def create_agency(self, request: AgencyCreateRequest) -> AgencyResponse:
        try:
            logging.info(
                f"[Agency Service] [Create Agency] Starting creation for: {request.name}"
            )

            # Generate unique agencies ID
            agency_id = generate_uuid()
            logging.debug(
                f"[Agency Service] [Create Agency] Generated agency_id: {agency_id}"
            )

            # Check if agencies with same name or slug already exists
            existing_agencies_response = await self.agency_repo.find_all_agencies(
                include_inactive=True
            )
            for agency in existing_agencies_response.AgencyList:
                if agency.name == request.name:
                    logging.warning(
                        f"[Agency Service] [Create Agency] Agency with name '{request.name}' already exists"
                    )
                    raise HTTPException(
                        status_code=409, detail="Agency with this name already exists"
                    )
                if agency.slug == request.slug:
                    logging.warning(
                        f"[Agency Service] [Create Agency] Agency with slug '{request.slug}' already exists"
                    )
                    raise HTTPException(
                        status_code=409, detail="Agency with this slug already exists"
                    )

            created_agency = await self.agency_repo.create_agency(agency_id, request)

            if not created_agency:
                logging.error(
                    f"[Agency Service] [Create Agency] Failed to create agencies in database"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to create agencies in database"
                )

            logging.info(
                f"[Agency Service] [Create Agency] Successfully created agencies: {agency_id}"
            )
            return created_agency

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Service] [Create Agency] Unexpected error: {str(e)}"
            )
            logging.error(
                f"[Agency Service] [Create Agency] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Internal server error while creating agencies"
            )

    async def find_agency_by_id(self, agency_id: str) -> Optional[AgencyResponse]:
        try:
            logging.info(
                f"[Agency Service] [Find Agency By ID] Fetching agencies: {agency_id}"
            )

            agency = await self.agency_repo.find_agency_by_id(agency_id)
            if not agency:
                logging.warning(
                    f"[Agency Service] [Find Agency By ID] Agency not found: {agency_id}"
                )
                return None

            logging.info(
                f"[Agency Service] [Find Agency By ID] Successfully found agencies: {agency.name}"
            )
            return agency

        except Exception as e:
            logging.error(f"[Agency Service] [Find Agency By ID] Error: {str(e)}")
            logging.error(
                f"[Agency Service] [Find Agency By ID] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Internal server error while fetching agencies"
            )

    async def update_agency(
        self, agency_id: str, request: AgencyUpdateRequest
    ) -> Optional[AgencyResponse]:
        try:
            logging.info(
                f"[Agency Service] [Update Agency] Updating agencies: {agency_id}"
            )

            # Check if agencies exists
            existing_agency = await self.agency_repository.find_agency_by_id(agency_id)
            if not existing_agency:
                logging.error(
                    f"[Agency Service] [Update Agency] Agency not found: {agency_id}"
                )
                raise HTTPException(status_code=404, detail="Agency not found")

            # Update agencies
            updated_agency = await self.agency_repo.update_agency(agency_id, request)
            if not updated_agency:
                logging.error(
                    f"[Agency Service] [Update Agency] Failed to update agencies: {agency_id}"
                )
                raise HTTPException(status_code=500, detail="Failed to update agencies")

            logging.info(
                f"[Agency Service] [Update Agency] Successfully updated agencies: {agency_id}"
            )
            return updated_agency

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Agency Service] [Update Agency] Error: {str(e)}")
            logging.error(
                f"[Agency Service] [Update Agency] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Internal server error while updating agency"
            )

    async def invite_contracted_teacher(
        self, agency_id: str, request: InviteContractedTeacherRequest, created_by: str
    ) -> Dict[str, Any]:
        """
        Invite a contracted Teacher to join the platform
        """
        try:
            logging.info(
                f"[Agency Service] [Invite Contracted Teacher] Creating invite for {request.email}"
            )

            # 1. Validate input parameters
            if not request.email or not request.email.strip():
                logging.warning(
                    f"[Agency Service] [Invite Contracted Teacher] Missing email"
                )
                raise HTTPException(status_code=400, detail="Email is required")

            # 2. Generate or use provided teacher_id
            teacher_id = request.teacher_id
            if not teacher_id:
                teacher_id = generate_uuid()
                logging.info(
                    f"[Agency Service] [Invite Contracted Teacher] Generated student_id: {teacher_id}"
                )
            else:
                # 只是记录日志，不检查学生是否存在（因为学生可能已经通过其他方式创建）
                logging.info(
                    f"[Agency Service] [Invite Contracted Teacher] Using provided student_id: {teacher_id}"
                )

            # 3. Check if there's already a pending invite for this email/teacher
            existing_invite = await self.invite_repo.mongo_repo.find_one(
                query={
                    "$or": [
                        {"email": request.email.strip(), "status": "pending"},
                        {"teacher_id": teacher_id, "status": "pending"},
                    ]
                },
                collection_name=self.invite_repo.invites_collection,
            )

            if existing_invite:
                logging.warning(
                    f"[Agency Service] [Invite Contracted Teacher] Pending invite already exists for {request.email}"
                )
                raise HTTPException(
                    status_code=409,
                    detail="A pending invite already exists for this email or teacher",
                )

            # 4. Generate invite token and ID
            invite_token = generate_invite_token()
            invite_id = generate_uuid()
            logging.info(
                f"[Agency Service] [Invite Contracted Teacher] Generated invite_id: {invite_id}"
            )

            # 5. Set contract start date
            contract_start_date = (
                request.contract_start_date
                if request.contract_start_date
                else datetime.utcnow()
            )

            # 6. Create invite data with contract_status
            invite_data = {
                "invite_id": invite_id,
                "agency_id": agency_id,
                "email": request.email.strip(),
                "teacher_id": teacher_id.strip(),
                "invite_type": "待定",
                "contract_status": "contracted",  # Mark as contracted
                "contract_start_date": contract_start_date,
                "status": "pending",
                "token": invite_token,
                "message": request.message.strip() if request.message else None,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow()
                + timedelta(days=7),  # 7 days expiry for invite link
            }

            # 7. Save invite to database
            result = await self.invite_repo.create_invite(invite_data)
            if not result:
                logging.error(
                    f"[Agency Service] [Invite Contracted Teacher] Failed to save invite to database"
                )
                raise HTTPException(status_code=500, detail="Failed to create invite")

            logging.info(
                f"[Agency Service] [Invite Contracted Teacher] Successfully saved invite to database: {result}"
            )

            # 8. Store token in Redis for quick validation
            await self.invite_repo.set_invite_token(
                invite_token, invite_id, 7 * 24 * 3600, "student"
            )  # 7 days
            logging.info(
                f"[Agency Service] [Invite Contracted Teacher] Successfully stored token in Redis"
            )

            # 9. Return response
            logging.info(
                f"[Agency Service] [Invite Contracted Teacher] Successfully created contracted student invite for {request.email}"
            )
            return {
                "invite_id": invite_id,
                "teacher_id": teacher_id.strip(),
                "email": request.email,
                "token": invite_token,
                "contract_status": "contracted",
                "contract_start_date": contract_start_date.isoformat(),
                "expires_at": invite_data["expires_at"].isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Agency Service] [Invite Contracted Teacher] Error: {str(e)}"
            )
            logging.error(
                f"[Agency Service] [Invite Contracted Teacher] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to create contracted teacher invite"
            )
