import logging
from typing import Optional, Dict, Any

from .university_repo import UniversityRepo


class UniversityService:
    def __init__(self):
        self.university_repo = UniversityRepo()
        logging.info("[University Service] Initialized with repository")

    async def find_university_profile(
        self, university_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            logging.info(
                f"[University Service] [Find University Profile] Finding universities profile: {university_id}"
            )
            result = await self.university_repo.find_university_profile(university_id)
            if result:
                logging.info(
                    f"[University Service] [Find University Profile] Found universities profile: {university_id}"
                )
            else:
                logging.warning(
                    f"[University Service] [Find University Profile] University profile not found: {university_id}"
                )
            return result
        except Exception as e:
            logging.error(
                f"[University Service] [Find University Profile] Error: {str(e)}"
            )
            raise

    async def find_program_profile(
        self, university_id: str, program_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            logging.info(
                f"[University Service] [Find Program Profile] Finding program profile: university_id={university_id}, program_id={program_id}"
            )
            result = await self.university_repo.find_program_profile(
                university_id, program_id
            )
            if result:
                logging.info(
                    f"[University Service] [Find Program Profile] Found program profile: university_id={university_id}, program_id={program_id}"
                )
            else:
                logging.warning(
                    f"[University Service] [Find Program Profile] Program profile not found: university_id={university_id}, program_id={program_id}"
                )
            return result
        except Exception as e:
            logging.error(
                f"[University Service] [Find Program Profile] Error: {str(e)}"
            )
            raise

    async def find_admission_cycle(
        self, university_id: str, study_level: str
    ) -> Optional[Dict[str, Any]]:
        try:
            logging.info(
                f"[University Service] [Find Admission Cycle] Finding admission cycle: university_id={university_id}, study_level={study_level}"
            )
            result = await self.university_repo.find_admission_cycle(
                university_id, study_level
            )
            if result:
                logging.info(
                    f"[University Service] [Find Admission Cycle] Found admission cycle: university_id={university_id}, study_level={study_level}"
                )
            else:
                logging.warning(
                    f"[University Service] [Find Admission Cycle] Admission cycle not found: university_id={university_id}, study_level={study_level}"
                )
            return result
        except Exception as e:
            logging.error(
                f"[University Service] [Find Admission Cycle] Error: {str(e)}"
            )
            raise

    async def find_admission_requirements(
        self, university_id: str, degree_level: str
    ) -> Optional[Dict[str, Any]]:
        try:
            logging.info(
                f"[University Service] [Find Admission Requirements] Finding admission requirements: university_id={university_id}, degree_level={degree_level}"
            )
            result = await self.university_repo.find_admission_requirements(
                university_id, degree_level
            )
            if result:
                logging.info(
                    f"[University Service] [Find Admission Requirements] Found admission requirements: university_id={university_id}, degree_level={degree_level}"
                )
            else:
                logging.warning(
                    f"[University Service] [Find Admission Requirements] Admission requirements not found: university_id={university_id}, degree_level={degree_level}"
                )
            return result
        except Exception as e:
            logging.error(
                f"[University Service] [Find Admission Requirements] Error: {str(e)}"
            )
            raise
