import logging
from datetime import datetime
from typing import Optional, Dict, Any

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD
from admitplus.api.agency.agency_schema import (
    AgencyCreateRequest,
    AgencyResponse,
    AgencyListResponse,
    AgencyOut,
    AgencyUpdateRequest,
)


class AgencyRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.agency_profiles_collection = settings.AGENCY_PROFILES_COLLECTION

        logging.info(
            f"[Agency Repo] [Init] Initialized with db: {self.db_name}, collection: {self.agency_profiles_collection}"
        )

        if not self.agency_profiles_collection:
            logging.error(
                "[Agency Repo] [Init] No collection name available from environment or config!"
            )
            raise ValueError(
                "Collection name is required but not found in environment or config"
            )

        self.agency_repo = BaseMongoCRUD(self.db_name)

    async def find_all_agencies(
        self, include_inactive: bool = False, page: int = 1, page_size: int = 1000
    ) -> AgencyListResponse:
        try:
            logging.info(
                f"[Agency Repo] [Find All Agencies] Starting query, include_inactive={include_inactive}, page={page}, page_size={page_size}"
            )

            query = {}
            if not include_inactive:
                query["status"] = {"$ne": "inactive"}
                logging.debug(
                    "[Agency Repo] [Find All Agencies] Filtering out inactive agencies"
                )

            result, total_count = await self.agency_repo.find_many_paginated(
                query=query,
                collection_name=self.agency_profiles_collection,
                page=page,
                page_size=page_size,
                sort=[("created_at", -1)],
            )

            # Convert to AgencyOut objects
            agency_list = []
            for agency in result:
                agency_out = AgencyOut(
                    agency_id=agency.get("agency_id", ""),
                    name=agency.get("name", ""),
                    slug=agency.get("slug", ""),
                    status=agency.get("status", ""),
                    settings=agency.get("settings", {}),
                    created_at=agency.get("created_at", datetime.utcnow()),
                    updated_at=agency.get("updated_at", datetime.utcnow()),
                )
                agency_list.append(agency_out)

            logging.info(
                f"[Agency Repo] [Find All Agencies] Retrieved {len(agency_list)}/{total_count} agencies"
            )
            return AgencyListResponse(AgencyList=agency_list)

        except Exception as e:
            logging.error(f"[Agency Repo] [Find All Agencies] Error: {str(e)}")
            return AgencyListResponse(AgencyList=[])

    async def create_agency(
        self, agency_id: str, agency_data: AgencyCreateRequest
    ) -> Optional[AgencyResponse]:
        try:
            logging.info(
                f"[Agency Repo] [Create Agency] Starting creation with ID: {agency_id}, name: {agency_data.name}"
            )

            doc = {
                "agency_id": agency_id,
                "name": agency_data.name,
                "slug": agency_data.slug,
                "status": agency_data.status,
                "settings": agency_data.settings.dict()
                if hasattr(agency_data.settings, "dict")
                else agency_data.settings,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            result = await self.agency_repo.insert_one(
                document=doc, collection_name=self.agency_profiles_collection
            )

            if result:
                logging.info(
                    f"[Agency Repo] [Create Agency] Successfully created agencies: {agency_id}"
                )
                return AgencyResponse(
                    agency_id=doc["agency_id"],
                    name=doc["name"],
                    slug=doc["slug"],
                    status=doc["status"],
                    settings=agency_data.settings,
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                )
            else:
                logging.error(
                    f"[Agency Repo] [Create Agency] Failed to create agencies: {agency_id}"
                )
                return None

        except Exception as e:
            logging.error(
                f"[Agency Repo] [Create Agency] Error creating agencies: {str(e)}"
            )
            return None

    async def find_agency_by_id(self, agency_id: str) -> Optional[AgencyResponse]:
        try:
            logging.info(
                f"[Agency Repo] [Find Agency By ID] Searching for agencies: {agency_id}"
            )

            result = await self.agency_repo.find_one(
                query={"agency_id": agency_id},
                collection_name=self.agency_profiles_collection,
            )

            if result:
                logging.info(
                    f"[Agency Repo] [Find Agency By ID] Found agencies: {result.get('name')}"
                )
                # Convert to AgencyResponse
                return AgencyResponse(
                    agency_id=result.get("agency_id", ""),
                    name=result.get("name", ""),
                    slug=result.get("slug", ""),
                    status=result.get("status", ""),
                    settings=result.get("settings", {}),
                    created_at=result.get("created_at", datetime.utcnow()),
                    updated_at=result.get("updated_at", datetime.utcnow()),
                )
            else:
                logging.warning(
                    f"[Agency Repo] [Find Agency By ID] Agency not found: {agency_id}"
                )
                return None

        except Exception as e:
            logging.error(f"[Agency Repo] [Find Agency By ID] Error: {str(e)}")
            return None

    async def update_agency(
        self, agency_id: str, update_data: AgencyUpdateRequest
    ) -> Optional[AgencyResponse]:
        try:
            logging.info(
                f"[Agency Repo] [Update Agency] Updating agencies: {agency_id}"
            )

            # Convert Pydantic model to dict and add timestamp
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            count = await self.agency_repo.update_one(
                query={"agency_id": agency_id},
                update_data={"$set": update_dict},
                collection_name=self.agency_profiles_collection,
            )

            if count:
                logging.info(
                    f"[Agency Repo] [Update Agency] Successfully updated agencies: {agency_id}"
                )
                return await self.find_agency_by_id(agency_id)
            else:
                logging.error(
                    f"[Agency Repo] [Update Agency] Failed to update agencies: {agency_id}"
                )
                return None

        except Exception as e:
            logging.error(f"[Agency Repo] [Update Agency] Error: {str(e)}")
            return None

    async def delete_agency(self, agency_id: str) -> bool:
        try:
            logging.info(
                f"[Agency Repo] [Delete Agency] Soft deleting agencies: {agency_id}"
            )

            result = await self.agency_repo.update_one(
                query={"agency_id": agency_id},
                update_data={
                    "$set": {"status": "inactive", "updated_at": datetime.utcnow()}
                },
                collection_name=self.agency_profiles_collection,
            )

            if result:
                logging.info(
                    f"[Agency Repo] [Delete Agency] Successfully deleted agencies: {agency_id}"
                )
                return True
            else:
                logging.error(
                    f"[Agency Repo] [Delete Agency] Failed to delete agencies: {agency_id}"
                )
                return False

        except Exception as e:
            logging.error(f"[Agency Repo] [Delete Agency] Error: {str(e)}")
            return False

    async def create_agency_membership(
        self, membership_data: Dict[str, Any]
    ) -> Optional[str]:
        """Create agencies membership"""
        try:
            logging.info(
                f"[Agency Repo] [Create Membership] Creating agencies membership for user {membership_data.get('user_id', 'unknown')} in agencies {membership_data.get('agency_id', 'unknown')}"
            )

            result = await self.agency_repo.insert_one(
                document=membership_data,
                collection_name=settings.AGENCY_MEMBERS_COLLECTION,
            )

            if result:
                logging.info(
                    f"[Agency Repo] [Create Membership] Successfully created membership: {result}"
                )
            else:
                logging.warning(
                    f"[Agency Repo] [Create Membership] Failed to create membership for user {membership_data.get('user_id', 'unknown')}"
                )
            return result

        except Exception as e:
            logging.error(
                f"[Agency Repo] [Create Membership] Error creating membership: {str(e)}"
            )
            return None
