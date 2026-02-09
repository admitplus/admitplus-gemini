import logging

from admitplus.database.redis import BaseRedisCRUD
from .suggestion_repo import SuggestionRepo


class SuggestionService:
    def __init__(self):
        self.redis_repo = BaseRedisCRUD()
        self.suggestion_repo = SuggestionRepo()

    async def university_autocomplete(self, query: str, country_code=None):
        try:
            logging.info(
                f"[SuggestionService] [UniversitySuggestions] Starting - country_code={country_code}, query='{query}'"
            )

            # Service layer: Build query filter
            # query is required, so always add university_name filter
            query_filter = {"university_name": {"$regex": f"^{query}", "$options": "i"}}

            # Add country_code filter if provided (merge, don't override)
            if country_code:
                query_filter["country_code"] = country_code

            logging.debug(
                f"[SuggestionService] [UniversitySuggestions] Query filter: {query_filter}"
            )

            # Service layer: Define projection fields
            projection = {"_id": 0, "university_name": 1, "logo_url": 1}
            logging.debug(
                f"[SuggestionService] [UniversitySuggestions] Projection: {projection}"
            )

            # Call Repository to get raw data
            logging.info(
                f"[SuggestionService] [UniversitySuggestions] Calling repository for universities"
            )
            universities = await self.suggestion_repo.find_universities(
                query_filter, projection
            )

            # Service layer: Process business logic (deduplication, sorting, limit count)
            logging.debug(
                f"[SuggestionService] [UniversitySuggestions] Processing {len(universities)} raw universities records"
            )

            # Create a dictionary to deduplicate by university_name, keeping the first occurrence with logo_url
            university_dict = {}
            for uni in universities:
                university_name = uni.get("university_name", "")
                if university_name:
                    # Only add if not already in dict, or if current entry has no logo_url but this one does
                    if university_name not in university_dict:
                        university_dict[university_name] = {
                            "university_name": university_name,
                            "logo_url": uni.get("logo_url", ""),
                        }
                    elif not university_dict[university_name].get(
                        "logo_url"
                    ) and uni.get("logo_url"):
                        # Update if current entry has no logo_url but this one does
                        university_dict[university_name]["logo_url"] = uni.get(
                            "logo_url", ""
                        )

            # Sort by university_name and convert to list
            result = sorted(
                university_dict.values(), key=lambda x: x["university_name"]
            )

            max_results = 10
            result = result[:max_results]
            logging.debug(
                f"[SuggestionService] [UniversitySuggestions] After deduplication and sorting: {len(university_dict)} total, returning {len(result)} (max={max_results})"
            )

            logging.info(
                f"[SuggestionService] [UniversitySuggestions] Success - found {len(result)} universities suggestions for country_code={country_code}, query='{query}'"
            )
            return result

        except Exception as err:
            logging.error(
                f"[SuggestionService] [UniversitySuggestions] Error - country_code={country_code}, query='{query}', error={str(err)}"
            )
            raise

    async def program_suggestions(self, degree_level: str, query: str) -> list[str]:
        """
        Get program name suggestions for autocomplete (global search across all universities).
        """
        return await self._search_programs_internal(
            query=query, degree_level=degree_level, university_id=None
        )

    async def search_programs(
        self, query: str, university_id: str, degree_level: str
    ) -> list[str]:
        """
        Search programs for a specific universities, filtered by degree and query prefix.
        """
        return await self._search_programs_internal(
            query=query, degree_level=degree_level, university_id=university_id
        )

    async def _search_programs_internal(
        self, query: str, degree_level: str, university_id: str | None = None
    ) -> list[str]:
        """
        Internal method to search programs with optional universities filter.
        This shared logic is used by both program_suggestions and search_programs.
        """
        try:
            logging.info(
                f"Searching programs - query='{query}', degree_level={degree_level}, university_id={university_id}"
            )

            # Service layer: Build query filter
            query_filter = {"program_name": {"$regex": f"^{query}", "$options": "i"}}

            # Add university_id filter if provided
            if university_id is not None:
                query_filter["university_id"] = university_id

            projection = {"_id": 0, "program_name": 1}
            logging.debug(f"Query filter: {query_filter}")
            logging.debug(f"Projection: {projection}")

            # Call Repository to get raw data
            logging.info(
                f"Calling repository for programs (degree_level={degree_level})"
            )
            programs = await self.suggestion_repo.find_programs(
                query_filter, projection, degree_level
            )
            logging.debug(f"Retrieved {len(programs)} documents")

            # Service layer: Process business logic (deduplication, sorting, limit count)
            program_names = set()
            for program in programs:
                name = program.get("program_name", "")
                if name:
                    program_names.add(name)

            # Sort and limit results
            result = sorted(program_names)
            max_results = 10
            result = result[:max_results]
            logging.debug(
                f"After processing: {len(program_names)} unique programs found, returning {len(result)} (max={max_results})"
            )

            success_msg = f"Success - found {len(result)} programs for degree_level={degree_level}, query='{query}'"
            if university_id:
                success_msg += f", university_id={university_id}"
            logging.info(success_msg)

            return result

        except Exception as err:
            error_msg = f"Error searching programs - query='{query}', degree_level={degree_level}"
            if university_id:
                error_msg += f", university_id={university_id}"
            error_msg += f", error={str(err)}"
            logging.error(error_msg)
            raise
