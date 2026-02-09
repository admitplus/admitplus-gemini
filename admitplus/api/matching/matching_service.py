import logging
import traceback

from starlette.exceptions import HTTPException

from .matching_repo import MatchingRepo
from .matching_schema import UniversitySearchFilter


class MatchingService:
    def __init__(self):
        self.matching_repo = MatchingRepo()

    async def matching(self, request: UniversitySearchFilter):
        """
        Perform universities matching based on location, GPA, and major filters
        """
        try:
            logging.info(
                f"[Matching Service] [Matching] Starting matching process - degree: {request.target_degree}, major: {request.major}, GPA: {request.gpa}, continent: {request.target_continent}, country: {request.target_country}"
            )

            # Step 1: Filter by location
            logging.info("[Matching Service] [Matching] Step 1: Filtering by location")
            filter_by_location = await self.matching_repo.filter_by_location(request)
            if not filter_by_location:
                logging.warning(
                    "[Matching Service] [Matching] Step 1 failed: No universities found matching location criteria"
                )
                return {"programs": []}
            logging.info(
                f"[Matching Service] [Matching] Step 1 completed: {len(filter_by_location)} universities found"
            )

            # Step 2: Filter by GPA
            logging.info(
                f"[Matching Service] [Matching] Step 2: Filtering {len(filter_by_location)} universities by GPA"
            )
            filter_by_gpa = await self.matching_repo.filter_by_gpa(
                request, filter_by_location
            )
            if not filter_by_gpa:
                logging.warning(
                    "[Matching Service] [Matching] Step 2 failed: No universities found matching GPA requirements"
                )
                return {"programs": []}
            logging.info(
                f"[Matching Service] [Matching] Step 2 completed: {len(filter_by_gpa)} universities passed GPA filter"
            )

            # Step 3: Filter by major
            logging.info(
                f"[Matching Service] [Matching] Step 3: Filtering {len(filter_by_gpa)} universities by major"
            )
            filter_by_major = await self.matching_repo.filter_by_major(
                request, filter_by_gpa
            )

            programs_count = len(filter_by_major.get("programs", []))
            logging.info(
                f"[Matching Service] [Matching] Matching completed successfully - found {programs_count} matching programs from {len(filter_by_gpa)} universities"
            )
            return filter_by_major

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Matching Service] [Matching] Error during matching process: {str(e)}"
            )
            logging.error(
                f"[Matching Service] [Matching] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to perform universities matching"
            )
