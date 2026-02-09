import logging
from typing import Any, Optional, Dict

from admitplus.database.redis import BaseRedisCRUD
from .information_repo import InformationRepo
from .suggestion_repo import SuggestionRepo
from .university_repo import UniversityRepo
from .information_schema import (
    ApplicationInfo,
    Location,
    UniversitiesByMajorRequest,
    UniversityProgramQueryRequest,
    UniversityProgramResponse,
)


def find_program(programs: list[dict[str, Any]], target: str) -> dict[str, Any] | None:
    """
    Find a program from a list of programs by matching the program_name (case-insensitive)
    """
    return next(
        (p for p in programs if p.get("program_name", "").lower() == target.lower()),
        None,
    )


class InformationService:
    def __init__(self):
        self.information_repo = InformationRepo()
        self.redis_repo = BaseRedisCRUD()
        self.suggestion_repo = SuggestionRepo()
        self.university_repo = UniversityRepo()
        logging.info(f"[Information Service] Initialized")

    async def get_program_details(self, request: UniversityProgramQueryRequest):
        """
        Get detailed information about a specific universities program
        """
        logging.info(
            f"[Service] [GetProgramDetails] Starting - university_id: {request.university_id}, degree: {request.degree}, program_name: {request.program_name}, country: {request.country}"
        )

        try:
            # Get universities details
            logging.debug(
                f"[Service] [GetProgramDetails] Fetching universities details for university_id: {request.university_id}"
            )
            university_details = await self.information_repo.find_university_by_id(
                request.university_id
            )

            if not university_details:
                logging.warning(
                    f"[Service] [GetProgramDetails] University not found in database - university_id: {request.university_id}"
                )
                raise ValueError(
                    f"University with ID '{request.university_id}' not found in database"
                )

            university_name = university_details.get("university_name", "Unknown")
            logging.info(
                f"[Service] [GetProgramDetails] Found universities: {university_name} (ID: {request.university_id})"
            )

            # Get program details
            logging.debug(
                f"[Service] [GetProgramDetails] Fetching {request.degree} program details - university_id: {request.university_id}, program_name: {request.program_name}"
            )
            program_details_list = await self.information_repo.find_program_details(
                university_id=request.university_id,
                degree=request.degree,
                program_name=request.program_name,
            )

            if not program_details_list:
                logging.warning(
                    f"[Service] [GetProgramDetails] Program not found - university_id: {request.university_id}, degree: {request.degree}, program_name: {request.program_name}"
                )
                raise ValueError(
                    f"Program details for universities ID '{request.university_id}' and degree '{request.degree}' not found in database"
                )

            program_details = program_details_list[0]  # Get first result
            logging.info(
                f"[Service] [GetProgramDetails] Found {len(program_details_list)} program detail(s), using first result"
            )

            # Log the actual program_details structure for debugging
            logging.debug(
                f"[Service] [GetProgramDetails] Program details keys: {list(program_details.keys())}"
            )
            logging.debug(
                f"[Service] [GetProgramDetails] Program details application_info: {program_details.get('application_info')}"
            )

            # Create response objects
            logging.debug(f"[Service] [GetProgramDetails] Creating response objects")
            location_data = university_details.get("location")
            location = Location(**location_data) if location_data else None
            if location:
                logging.debug(
                    f"[Service] [GetProgramDetails] Location data processed - city: {location.city}, state: {location.state}, country: {location.country}"
                )
            else:
                logging.debug(
                    f"[Service] [GetProgramDetails] No location data available"
                )

            # Extract application_info from program_details
            app_info = program_details.get("application_info")
            logging.debug(
                f"[Service] [GetProgramDetails] Extracted app_info: {app_info}"
            )
            logging.debug(
                f"[Service] [GetProgramDetails] app_info type: {type(app_info)}"
            )

            # If application_info doesn't exist or is empty, try to use program_details directly
            # This handles cases where the program data is at the top level
            if not app_info:
                logging.debug(
                    f"[Service] [GetProgramDetails] No application_info found in program_details, checking top-level fields"
                )
                # Check if program_details itself has application-related fields
                if (
                    program_details.get("degree_level")
                    or program_details.get("application_deadlines")
                    or program_details.get("requirements")
                ):
                    logging.debug(
                        f"[Service] [GetProgramDetails] Found application fields at top level, using program_details as app_info"
                    )
                    app_info = program_details

            # For undergraduate programs, try to find matching program in the list
            undergraduate_program_match = None
            if app_info:
                undergraduate_programs_list = app_info.get("undergraduate_programs", [])
                logging.debug(
                    f"[Service] [GetProgramDetails] undergraduate_programs list: {undergraduate_programs_list}"
                )
                if undergraduate_programs_list and isinstance(
                    undergraduate_programs_list, list
                ):
                    undergraduate_program_match = find_program(
                        undergraduate_programs_list, request.program_name
                    )
                    if not undergraduate_program_match:
                        logging.debug(
                            f"[Service] [GetProgramDetails] Program '{request.program_name}' not found in undergraduate_programs list"
                        )
                else:
                    # If undergraduate_programs is empty/None or not a list, and this is an undergraduate program,
                    # use the entire app_info as the program data
                    if request.degree == "undergraduate":
                        logging.debug(
                            f"[Service] [GetProgramDetails] No undergraduate_programs list found for undergraduate degree, using app_info directly"
                        )
                        undergraduate_program_match = app_info if app_info else None

            application_info = ApplicationInfo(
                degree_level=app_info.get("degree_level") if app_info else None,
                application_deadlines=app_info.get("application_deadlines")
                if app_info
                else None,
                requirements=app_info.get("requirements") if app_info else None,
                undergraduate_programs=undergraduate_program_match,
            )

            logging.debug(
                f"[Service] [GetProgramDetails] Final application_info - degree_level: {application_info.degree_level}, "
                f"has_deadlines: {application_info.application_deadlines is not None}, "
                f"has_requirements: {application_info.requirements is not None}, "
                f"has_undergraduate_programs: {application_info.undergraduate_programs is not None}"
            )

            if undergraduate_program_match:
                logging.debug(
                    f"[Service] [GetProgramDetails] Found matching undergraduate program: {request.program_name}"
                )
            else:
                logging.debug(
                    f"[Service] [GetProgramDetails] No matching undergraduate program found in list"
                )

            # Build response
            logging.debug(
                f"[Service] [GetProgramDetails] Building UniversityProgramResponse"
            )
            logo_url = university_details.get("logo_url", "")
            if logo_url:
                logging.debug(
                    f"[Service] [GetProgramDetails] Found logo_url: {logo_url}"
                )
            else:
                logging.debug(
                    f"[Service] [GetProgramDetails] No logo_url found in university_profile"
                )

            # Log program_details fields for debugging
            admission_overview_link = program_details.get("admission_overview_link")
            admission_statistics = program_details.get("admission_statistics")
            logging.debug(
                f"[Service] [GetProgramDetails] admission_overview_link from program_details: {admission_overview_link}"
            )
            logging.debug(
                f"[Service] [GetProgramDetails] admission_statistics from program_details: {admission_statistics}"
            )
            logging.debug(
                f"[Service] [GetProgramDetails] Full program_details structure: {program_details}"
            )

            response = UniversityProgramResponse(
                university_name=university_details.get("university_name", ""),
                logo_url=logo_url,
                location=location,
                founded_year=university_details.get("founded_year"),
                type=university_details.get("type"),
                website=university_details.get("website"),
                student=university_details.get("students"),
                ranking=university_details.get("ranking", {}).get("usnews")
                if isinstance(university_details.get("ranking"), dict)
                else university_details.get("ranking"),
                admission_overview_link=admission_overview_link,
                admission_statistics=admission_statistics,
                application_info=application_info,
            )

            logging.info(
                f"[Service] [GetProgramDetails] Successfully processed - universities: {university_name}, program: {request.program_name}, degree: {request.degree}"
            )
            return response

        except ValueError:
            # Re-raise ValueError with original message
            raise
        except Exception as err:
            logging.error(
                f"[Service] [GetProgramDetails] Unexpected error - university_id: {request.university_id}, degree: {request.degree}, program_name: {request.program_name}, error: {type(err).__name__}: {str(err)}"
            )
            logging.exception(f"[Service] [GetProgramDetails] Exception details")
            raise

    async def list_universities_by_major(self, request: UniversitiesByMajorRequest):
        """
        Get list of universities that offer a specific program and degree
        """
        logging.info(
            f"[Service] [ListUniversitiesByProgram] Starting - program_name: {request.program_name}, degree: {request.degree}, country: {request.country}"
        )

        try:
            # Get universities by program name
            logging.debug(
                f"[Service] [ListUniversitiesByProgram] Fetching universities - program_name: {request.program_name}, degree: {request.degree}"
            )
            university_list = (
                await self.information_repo.find_universities_by_program_name(
                    program_name=request.program_name, degree=request.degree
                )
            )

            logging.info(
                f"[Service] [ListUniversitiesByProgram] Found {len(university_list)} universities(ies) offering program: {request.program_name}"
            )

            if len(university_list) == 0:
                logging.warning(
                    f"[Service] [ListUniversitiesByProgram] No universities found - program_name: {request.program_name}, degree: {request.degree}"
                )
            else:
                # Fetch logo_urls from university_profiles_collection
                logging.debug(
                    f"[Service] [ListUniversitiesByProgram] Fetching logo_urls for {len(university_list)} universities"
                )
                university_ids = [
                    uni.get("university_id")
                    for uni in university_list
                    if uni.get("university_id")
                ]

                if university_ids:
                    logo_url_map = (
                        await self.information_repo.find_logo_urls_by_university_ids(
                            university_ids
                        )
                    )

                    # Add logo_url to each university in the list
                    for university in university_list:
                        university_id = university.get("university_id")
                        if university_id:
                            university["logo_url"] = logo_url_map.get(university_id, "")

                    logging.debug(
                        f"[Service] [ListUniversitiesByProgram] Added logo_urls to {len([u for u in university_list if u.get('logo_url')])} universities"
                    )

            # Return all raw data without transformation
            logging.debug(
                f"[Service] [ListUniversitiesByProgram] Returning raw data for {len(university_list)} universities(ies)"
            )

            result = {"university_list": university_list}
            logging.info(
                f"[Service] [ListUniversitiesByProgram] Successfully processed - program: {request.program_name}, degree: {request.degree}, universities: {len(university_list)}"
            )
            return result

        except Exception as err:
            logging.error(
                f"[Service] [ListUniversitiesByProgram] Unexpected error - program_name: {request.program_name}, degree: {request.degree}, country: {request.country}, error: {type(err).__name__}: {str(err)}"
            )
            logging.exception(
                f"[Service] [ListUniversitiesByProgram] Exception details"
            )
            raise

    async def get_university_detail(
        self, university_id: str, study_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific university by university_id.
        If study_level is provided, also includes admission_cycles, admission_requirements,
        and program-related information (admission_overview_link, admission_statistics, application_info).
        Returns detailed university information.
        """
        logging.info(
            f"[Service] [GetUniversityDetail] Starting - university_id: {university_id}, study_level: {study_level}"
        )

        try:
            # Get university details by ID
            university_details = await self.information_repo.find_university_by_id(
                university_id
            )

            if not university_details:
                logging.warning(
                    f"[Service] [GetUniversityDetail] University not found in database - university_id: {university_id}"
                )
                raise ValueError(
                    f"University with ID '{university_id}' not found in database"
                )

            university_name = university_details.get("university_name", "Unknown")
            logging.info(
                f"[Service] [GetUniversityDetail] Successfully retrieved university details - ID: {university_id}, Name: {university_name}"
            )

            # Normalize student field name (database might have "students" but response expects "student")
            if "students" in university_details and "student" not in university_details:
                university_details["student"] = university_details.pop("students")

            # Extract ranking information from university_details
            ranking_data = university_details.get("ranking")
            if ranking_data:
                if isinstance(ranking_data, dict):
                    # Try to get usnews ranking (most common)
                    ranking = ranking_data.get("usnews")
                    if ranking:
                        university_details["ranking"] = ranking
                        logging.debug(
                            f"[Service] [GetUniversityDetail] Found ranking: {ranking}"
                        )
                    else:
                        # Try to get any numeric ranking value
                        for key, value in ranking_data.items():
                            if isinstance(value, (int, float)):
                                university_details["ranking"] = value
                                logging.debug(
                                    f"[Service] [GetUniversityDetail] Found ranking from {key}: {value}"
                                )
                                break
                elif isinstance(ranking_data, (int, float)):
                    university_details["ranking"] = ranking_data
            else:
                university_details["ranking"] = None

            # If study_level is provided, fetch admission_cycles, admission_requirements, and program details
            if study_level:
                # Normalize study_level to lowercase format
                # Frontend will pass: "undergraduate", "graduate", or "phd"
                normalized_study_level = study_level.lower()

                logging.debug(
                    f"[Service] [GetUniversityDetail] Using study_level: '{normalized_study_level}'"
                )

                # Fetch admission_cycle using study_level
                logging.debug(
                    f"[Service] [GetUniversityDetail] Fetching admission cycle - university_id: {university_id}, study_level: {normalized_study_level}"
                )
                admission_cycle = await self.university_repo.find_admission_cycle(
                    university_id, normalized_study_level
                )
                if admission_cycle:
                    # Remove _id field if present (MongoDB ObjectId)
                    if "_id" in admission_cycle:
                        del admission_cycle["_id"]
                    university_details["admission_cycle"] = admission_cycle
                    logging.info(
                        f"[Service] [GetUniversityDetail] Found admission cycle for study_level: {normalized_study_level}"
                    )
                else:
                    logging.debug(
                        f"[Service] [GetUniversityDetail] No admission cycle found for study_level: {normalized_study_level}"
                    )

                # Fetch admission_requirements using normalized study_level
                # Repository will try both degree_level and study_level fields
                logging.debug(
                    f"[Service] [GetUniversityDetail] Fetching admission requirements - university_id: {university_id}, study_level: {normalized_study_level}"
                )
                admission_requirements = (
                    await self.university_repo.find_admission_requirements(
                        university_id, normalized_study_level
                    )
                )
                if admission_requirements:
                    # Remove _id field if present (MongoDB ObjectId)
                    if "_id" in admission_requirements:
                        del admission_requirements["_id"]
                    university_details["admission_requirements"] = (
                        admission_requirements
                    )
                    logging.info(
                        f"[Service] [GetUniversityDetail] Found admission requirements for study_level: {normalized_study_level}"
                    )
                else:
                    logging.debug(
                        f"[Service] [GetUniversityDetail] No admission requirements found for study_level: {normalized_study_level}"
                    )

                # Fetch program details for admission_overview_link, admission_statistics, and application_info
                logging.debug(
                    f"[Service] [GetUniversityDetail] Fetching program details - university_id: {university_id}, study_level: {normalized_study_level}"
                )
                program_details = await self.university_repo.find_program_by_university_id_and_study_level(
                    university_id, normalized_study_level
                )

                if program_details:
                    # Extract admission_overview_link
                    admission_overview_link = program_details.get(
                        "admission_overview_link"
                    )
                    if admission_overview_link:
                        university_details["admission_overview_link"] = (
                            admission_overview_link
                        )
                        logging.debug(
                            f"[Service] [GetUniversityDetail] Found admission_overview_link: {admission_overview_link}"
                        )

                    # Extract admission_statistics
                    admission_statistics = program_details.get("admission_statistics")
                    if admission_statistics:
                        university_details["admission_statistics"] = (
                            admission_statistics
                        )
                        logging.debug(
                            f"[Service] [GetUniversityDetail] Found admission_statistics"
                        )

                    # Extract and build application_info
                    app_info = program_details.get("application_info", {})
                    if app_info:
                        application_info = {
                            "degree_level": app_info.get("degree_level"),
                            "application_deadlines": app_info.get(
                                "application_deadlines"
                            ),
                            "requirements": app_info.get("requirements"),
                            "undergraduate_programs": app_info.get(
                                "undergraduate_programs"
                            ),
                        }
                        university_details["application_info"] = application_info
                        logging.debug(
                            f"[Service] [GetUniversityDetail] Found application_info"
                        )
                    else:
                        # Initialize empty application_info structure
                        university_details["application_info"] = {
                            "degree_level": None,
                            "application_deadlines": None,
                            "requirements": None,
                            "undergraduate_programs": None,
                        }
                else:
                    logging.debug(
                        f"[Service] [GetUniversityDetail] No program found for study_level: {normalized_study_level}, initializing empty fields"
                    )
                    # Initialize empty fields if no program found
                    if "admission_overview_link" not in university_details:
                        university_details["admission_overview_link"] = None
                    if "admission_statistics" not in university_details:
                        university_details["admission_statistics"] = None
                    if "application_info" not in university_details:
                        university_details["application_info"] = {
                            "degree_level": None,
                            "application_deadlines": None,
                            "requirements": None,
                            "undergraduate_programs": None,
                        }
            else:
                # If no study_level provided, initialize empty fields
                if "ranking" not in university_details:
                    university_details["ranking"] = None
                if "admission_overview_link" not in university_details:
                    university_details["admission_overview_link"] = None
                if "admission_statistics" not in university_details:
                    university_details["admission_statistics"] = None
                if "application_info" not in university_details:
                    university_details["application_info"] = {
                        "degree_level": None,
                        "application_deadlines": None,
                        "requirements": None,
                        "undergraduate_programs": None,
                    }

            return university_details

        except ValueError:
            # Re-raise ValueError with original message
            raise
        except Exception as err:
            logging.error(
                f"[Service] [GetUniversityDetail] Unexpected error - university_id: {university_id}, study_level: {study_level}, error: {type(err).__name__}: {str(err)}"
            )
            logging.exception(f"[Service] [GetUniversityDetail] Exception details")
            raise

    async def search_universities(
        self,
        query: str,
        country: Optional[str] = None,
        degree_level: Optional[str] = None,
    ):
        """
        Search universities by name with optional filters for country and degree_level.
        Returns detailed university information.
        """
        logging.info(
            f"[Service] [SearchUniversities] Starting - query: {query}, country: {country}, degree_level: {degree_level}"
        )

        try:
            # Normalize degree_level: map common abbreviations to full names
            normalized_degree_level = None
            if degree_level:
                degree_lower = degree_level.lower()
                degree_mapping = {
                    "undergrad": "undergraduate",
                    "grad": "graduate",
                    "master": "graduate",
                    "masters": "graduate",
                    "bachelor": "undergraduate",
                    "phd": "phd",
                    "doctorate": "phd",
                }
                normalized_degree_level = degree_mapping.get(degree_lower, degree_lower)
                logging.debug(
                    f"[Service] [SearchUniversities] Mapped degree_level '{degree_level}' to '{normalized_degree_level}'"
                )

            # Call repository to search universities
            universities = await self.information_repo.search_universities(
                query=query, country=country, degree_level=normalized_degree_level
            )

            logging.info(
                f"[Service] [SearchUniversities] Successfully retrieved {len(universities)} universities"
            )
            return {"universities": universities}

        except Exception as err:
            logging.error(
                f"[Service] [SearchUniversities] Unexpected error - query: {query}, country: {country}, degree_level: {degree_level}, error: {type(err).__name__}: {str(err)}"
            )
            logging.exception(f"[Service] [SearchUniversities] Exception details")
            raise
