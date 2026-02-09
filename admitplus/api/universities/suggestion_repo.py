from typing import List, Dict, Any
import logging

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class SuggestionRepo:
    def __init__(self):
        self.db_name = settings.MONGO_UNIVERSITY_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.university_profiles_collection = settings.UNIVERSITY_PROFILES_COLLECTION
        self.programs_collection = settings.UNIVERSITY_PROGRAMS_COLLECTION

    async def find_universities(
        self, query_filter: Dict[str, Any], projection: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Pure data access: Retrieve universities data based on query filter and projection fields
        """
        try:
            logging.info(
                f"[SuggestionRepo] [FindUniversities] Starting query with filter: {query_filter}"
            )
            logging.debug(
                f"[SuggestionRepo] [FindUniversities] Projection: {projection}"
            )
            logging.debug(
                f"[SuggestionRepo] [FindUniversities] Collection: {self.university_profiles_collection}"
            )

            result = await self.mongo_repo.find_many(
                query_filter, projection, None, self.university_profiles_collection
            )

            logging.info(
                f"[SuggestionRepo] [FindUniversities] Success - found {len(result)} universities records"
            )
            logging.debug(
                f"[SuggestionRepo] [FindUniversities] Sample results: {result[:2] if result else 'No results'}"
            )
            return result
        except Exception as e:
            logging.error(
                f"[SuggestionRepo] [FindUniversities] Error querying universities: {str(e)}"
            )
            raise

    async def find_programs(
        self, query_filter: Dict[str, Any], projection: Dict[str, Any], degree: str
    ) -> List[Dict[str, Any]]:
        """
        Pure data access: Retrieve program data based on query filter and projection fields.
        The degree determines which concrete collection to query.
        """
        try:
            logging.info(
                f"[SuggestionRepo] [FindPrograms] Starting query - degree={degree}'"
            )
            logging.debug(
                f"[SuggestionRepo] [FindPrograms] Query filter: {query_filter}"
            )
            logging.debug(f"[SuggestionRepo] [FindPrograms] Projection: {projection}")

            result = await self.mongo_repo.find_many(
                query_filter, projection, None, self.programs_collection
            )

            logging.info(
                f"[SuggestionRepo] [FindPrograms] Success - found {len(result)} program records from '{self.programs_collection}'"
            )
            logging.debug(
                f"[SuggestionRepo] [FindPrograms] Sample results: {result[:2] if result else 'No results'}"
            )
            return result
        except Exception as e:
            logging.error(
                f"[SuggestionRepo] [FindPrograms] Error querying programs for degree={degree}: {str(e)}"
            )
            raise
