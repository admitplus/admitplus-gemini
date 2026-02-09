import logging
from typing import Optional, Dict, Any, List

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class InformationRepo:
    def __init__(self):
        self.db_name = settings.MONGO_UNIVERSITY_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.university_profiles_collection = settings.UNIVERSITY_PROFILES_COLLECTION
        self.programs_collection = settings.UNIVERSITY_PROGRAMS_COLLECTION

        logging.info(f"[Information Repo] Initialized with DB: {self.db_name}")

    async def find_university_by_name(
        self, university_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find universities by name
        """
        try:
            logging.info(
                f"[Information Repo] [Find University] Finding universities: {university_name}"
            )

            query = {"university_name": university_name}
            result = await self.mongo_repo.find_one(
                query=query,
                projection=None,
                collection_name=self.university_profiles_collection,
            )

            if result:
                logging.info(
                    f"[Information Repo] [Find University] Found universities: {university_name}"
                )
            else:
                logging.warning(
                    f"[Information Repo] [Find University] University not found: {university_name}"
                )

            return result
        except Exception as e:
            logging.error(f"[Information Repo] [Find University] Error: {str(e)}")
            raise

    async def find_university_by_id(
        self, university_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find universities by ID
        """
        logging.info(
            f"[Repo] [FindUniversityById] Starting query - university_id: {university_id}"
        )

        try:
            query = {"university_id": university_id}
            projection = {
                "_id": 0
            }  # Exclude _id to avoid ObjectId serialization issues
            logging.debug(
                f"[Repo] [FindUniversityById] Query: {query}, Collection: {self.university_profiles_collection}, Projection: {projection}"
            )

            result = await self.mongo_repo.find_one(
                query=query,
                projection=projection,
                collection_name=self.university_profiles_collection,
            )

            if result:
                university_name = result.get("university_name", "Unknown")
                logging.info(
                    f"[Repo] [FindUniversityById] Found universities - ID: {university_id}, Name: {university_name}"
                )
            else:
                logging.warning(
                    f"[Repo] [FindUniversityById] University not found - university_id: {university_id}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[Repo] [FindUniversityById] Database error - university_id: {university_id}, error: {type(e).__name__}: {str(e)}"
            )
            logging.exception(f"[Repo] [FindUniversityById] Exception details")
            raise

    async def find_program_details(
        self, university_id: str, degree: str, program_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find program details by universities ID, degree, and program name
        """
        logging.info(
            f"[Repo] [FindProgramDetails] Starting query - university_id: {university_id}, degree: {degree}, program_name: {program_name}"
        )

        try:
            # Build query with degree filter
            # Programs may have either degree_level or study_level field
            query = {
                "university_id": university_id,
                "program_name": program_name,
                "$or": [
                    {"degree_level": degree.lower()},
                    {"study_level": degree.lower()},
                ],
            }
            logging.debug(f"[Repo] [FindProgramDetails] Query: {query}")

            # Execute query - exclude _id to avoid ObjectId serialization issues
            projection = {"_id": 0}  # Exclude _id but include all other fields
            logging.debug(f"[Repo] [FindProgramDetails] Using projection: {projection}")

            # Execute query
            logging.debug(
                f"[Repo] [FindProgramDetails] Executing MongoDB query on collection: {self.programs_collection}"
            )
            result = await self.mongo_repo.find_many(
                query=query,
                projection=projection,
                sort=None,
                collection_name=self.programs_collection,
            )

            # Log results
            if result:
                logging.info(
                    f"[Repo] [FindProgramDetails] Query successful - Found {len(result)} program(s) - university_id: {university_id}, program_name: {program_name}"
                )
                if len(result) > 1:
                    logging.debug(
                        f"[Repo] [FindProgramDetails] Multiple programs found ({len(result)}), will use first result"
                    )
            else:
                logging.warning(
                    f"[Repo] [FindProgramDetails] No programs found - university_id: {university_id}, degree: {degree}, program_name: {program_name}"
                )
            return result
        except ValueError:
            # Re-raise ValueError (e.g., invalid degree type)
            raise
        except Exception as e:
            logging.error(
                f"[Repo] [FindProgramDetails] Database error - university_id: {university_id}, degree: {degree}, program_name: {program_name}, error: {type(e).__name__}: {str(e)}"
            )
            logging.exception(f"[Repo] [FindProgramDetails] Exception details")
            raise

    async def find_universities_by_program_name(
        self,
        program_name: str,
        degree: str,
        projection: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find universities that offer a specific program name and degree
        """
        logging.info(
            f"[Repo] [FindUniversitiesByProgramName] Starting query - program_name: {program_name}, degree: {degree}"
        )

        try:
            # Build query with regex for case-insensitive matching
            query = {"program_name": {"$regex": f"^{program_name}$", "$options": "i"}}
            logging.debug(f"[Repo] [FindUniversitiesByProgramName] Query: {query}")

            # Execute query - only return university_name and university_id
            # If projection provided, use it; otherwise return only university_name and university_id
            if projection is None:
                # Only include university_name and university_id, exclude _id
                final_projection = {"_id": 0, "university_name": 1, "university_id": 1}
            else:
                final_projection = projection

            logging.debug(
                f"[Repo] [FindUniversitiesByProgramName] Using projection: {final_projection}"
            )

            # Execute query
            logging.debug(
                f"[Repo] [FindUniversitiesByProgramName] Executing MongoDB query on collection: {self.programs_collection}"
            )
            result = await self.mongo_repo.find_many(
                query=query,
                projection=final_projection,
                sort=None,
                collection_name=self.programs_collection,
            )

            # Log results
            if result:
                logging.info(
                    f"[Repo] [FindUniversitiesByProgramName] Query successful - Found {len(result)} universities(ies) offering program: {program_name} (degree: {degree})"
                )
                # Log first few universities names for debugging
                if len(result) > 0:
                    sample_names = [
                        uni.get("university_name", "Unknown") for uni in result[:3]
                    ]
                    logging.debug(
                        f"[Repo] [FindUniversitiesByProgramName] Sample universities: {', '.join(sample_names)}"
                    )
            else:
                logging.warning(
                    f"[Repo] [FindUniversitiesByProgramName] No universities found - program_name: {program_name}, degree: {degree}"
                )
            return result
        except ValueError:
            # Re-raise ValueError (e.g., invalid degree type)
            raise
        except Exception as e:
            logging.error(
                f"[Repo] [FindUniversitiesByProgramName] Database error - program_name: {program_name}, degree: {degree}, error: {type(e).__name__}: {str(e)}"
            )
            logging.exception(
                f"[Repo] [FindUniversitiesByProgramName] Exception details"
            )
            raise

    async def find_logo_urls_by_university_ids(
        self, university_ids: List[str]
    ) -> Dict[str, str]:
        """
        Find logo_urls for multiple universities by their IDs
        Returns a dictionary mapping university_id to logo_url
        """
        logging.info(
            f"[Repo] [FindLogoUrlsByUniversityIds] Starting query - university_ids count: {len(university_ids)}"
        )

        try:
            if not university_ids:
                logging.warning(
                    f"[Repo] [FindLogoUrlsByUniversityIds] Empty university_ids list provided"
                )
                return {}

            # Build query to find all universities with the given IDs
            query = {"university_id": {"$in": university_ids}}

            # Only fetch university_id and logo_url
            projection = {"_id": 0, "university_id": 1, "logo_url": 1}

            logging.debug(
                f"[Repo] [FindLogoUrlsByUniversityIds] Query: {query}, Collection: {self.university_profiles_collection}"
            )

            # Execute query
            results = await self.mongo_repo.find_many(
                query=query,
                projection=projection,
                sort=None,
                collection_name=self.university_profiles_collection,
            )

            # Create a mapping of university_id to logo_url
            logo_url_map = {}
            for result in results:
                university_id = result.get("university_id")
                logo_url = result.get("logo_url", "")
                if university_id:
                    logo_url_map[university_id] = logo_url

            logging.info(
                f"[Repo] [FindLogoUrlsByUniversityIds] Found logo_urls for {len(logo_url_map)} out of {len(university_ids)} universities"
            )
            return logo_url_map

        except Exception as e:
            logging.error(
                f"[Repo] [FindLogoUrlsByUniversityIds] Database error - university_ids count: {len(university_ids)}, error: {type(e).__name__}: {str(e)}"
            )
            logging.exception(f"[Repo] [FindLogoUrlsByUniversityIds] Exception details")
            raise

    async def search_universities(
        self,
        query: str,
        country: Optional[str] = None,
        degree_level: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search universities by name with optional filters for country and degree_level.
        If degree_level is provided, only returns universities that have programs for that degree level.
        """
        logging.info(
            f"[Repo] [SearchUniversities] Starting search - query: {query}, country: {country}, degree_level: {degree_level}"
        )

        try:
            # Build query for university profiles
            university_query = {"university_name": {"$regex": query, "$options": "i"}}

            # Add country filter if provided
            if country:
                # Try both country_code and location.country fields
                university_query["$or"] = [
                    {"country_code": country.upper()},
                    {"location.country": {"$regex": country, "$options": "i"}},
                ]

            logging.debug(
                f"[Repo] [SearchUniversities] University query: {university_query}"
            )

            # If degree_level is provided, we need to filter by universities that have programs for that degree
            if degree_level:
                # First, find university_ids that have programs for this degree level
                program_query = {
                    "$or": [
                        {"degree_level": degree_level.lower()},
                        {"study_level": degree_level.lower()},
                    ]
                }

                logging.debug(
                    f"[Repo] [SearchUniversities] Program query for degree_level filter: {program_query}"
                )
                programs = await self.mongo_repo.find_many(
                    query=program_query,
                    projection={"_id": 0, "university_id": 1},
                    sort=None,
                    collection_name=self.programs_collection,
                )

                university_ids_with_programs = list(
                    set(
                        [
                            p.get("university_id")
                            for p in programs
                            if p.get("university_id")
                        ]
                    )
                )
                logging.info(
                    f"[Repo] [SearchUniversities] Found {len(university_ids_with_programs)} universities with {degree_level} programs"
                )

                if university_ids_with_programs:
                    university_query["university_id"] = {
                        "$in": university_ids_with_programs
                    }
                else:
                    # No universities have programs for this degree level
                    logging.warning(
                        f"[Repo] [SearchUniversities] No universities found with {degree_level} programs"
                    )
                    return []

            # Execute query on university profiles
            projection = {"_id": 0}  # Return all fields except _id
            logging.debug(
                f"[Repo] [SearchUniversities] Executing query on university_profiles collection"
            )

            result = await self.mongo_repo.find_many(
                query=university_query,
                projection=projection,
                sort=[("university_name", 1)],
                collection_name=self.university_profiles_collection,
            )

            # Limit results
            if limit:
                result = result[:limit]

            logging.info(
                f"[Repo] [SearchUniversities] Found {len(result)} universities matching criteria"
            )
            return result

        except Exception as e:
            logging.error(
                f"[Repo] [SearchUniversities] Database error - query: {query}, country: {country}, degree_level: {degree_level}, error: {type(e).__name__}: {str(e)}"
            )
            logging.exception(f"[Repo] [SearchUniversities] Exception details")
            raise
