import logging
from typing import List, Optional, Dict, Any

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class AgencyMemberRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.agency_members_collection = settings.AGENCY_MEMBERS_COLLECTION
        logging.info(
            f"[Agency Member Repo] Initialized with db: {self.db_name}, collection: {self.agency_members_collection}"
        )

    async def find_member_ids_by_agency_id(self, agency_id: str) -> List[str]:
        """
        Find all member_ids for a given agency_id

        Args:
            agency_id: The agency ID

        Returns:
            List of member_ids
        """
        try:
            logging.info(
                f"[Agency Member Repo] [Find Member IDs By Agency ID] Finding member_ids for agency_id: {agency_id}"
            )

            members = await self.mongo_repo.find_many(
                query={"agency_id": agency_id},
                projection={"_id": 0, "member_id": 1},
                collection_name=self.agency_members_collection,
            )

            member_ids = [
                member.get("member_id") for member in members if member.get("member_id")
            ]

            logging.info(
                f"[Agency Member Repo] [Find Member IDs By Agency ID] Found {len(member_ids)} member_ids for agency_id: {agency_id}"
            )
            return member_ids

        except Exception as e:
            logging.error(
                f"[Agency Member Repo] [Find Member IDs By Agency ID] Error: {str(e)}"
            )
            return []
