import logging

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD
from admitplus.database.redis import BaseRedisCRUD


class UniversityRepo:
    def __init__(self):
        self.db_name = settings.MONGO_UNIVERSITY_WAREHOUSE_DB_NAME

        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.redis_repo = BaseRedisCRUD()

        self.university_profiles_collection = settings.UNIVERSITY_PROFILES_COLLECTION
        self.programs_collection = settings.UNIVERSITY_PROGRAMS_COLLECTION
        self.admission_cycles_collection = settings.ADMISSION_CYCLES_COLLECTION
        self.admission_requirements_collection = (
            settings.ADMISSION_REQUIREMENTS_COLLECTION
        )
        self.ranking_snapshots_collection = settings.RANKING_SNAPSHOTS_COLLECTION
        self.admission_outcomes_collection = settings.ADMISSION_OUTCOMES_COLLECTION

    async def find_university_profile(self, university_id: str):
        try:
            logging.info(
                f"[University Repo] [Find University Profile] Finding university profile: {university_id}"
            )

            query = {"university_id": university_id}
            university_profile = await self.mongo_repo.find_one(
                query, None, self.university_profiles_collection
            )

            if university_profile:
                logging.info(
                    f"[University Repo] [Find University Profile] Found university profile: {university_id}"
                )
            else:
                logging.warning(
                    f"[University Repo] [Find University Profile] University profile not found: {university_id}"
                )

            return university_profile
        except Exception as e:
            logging.error(
                f"[University Repo] [Find University Profile] Error: {str(e)}"
            )
            return None

    async def find_program_profile(self, university_id: str, program_id: str):
        try:
            logging.info(
                f"[University Repo] [Find Program Profile] Finding program profile: university_id={university_id}, program_id={program_id}"
            )

            program_profile = await self.mongo_repo.find_one(
                {"university_id": university_id, "program_id": program_id},
                None,
                self.programs_collection,
            )

            if program_profile:
                logging.info(
                    f"[University Repo] [Find Program Profile] Found program profile: university_id={university_id}, program_id={program_id}"
                )
            else:
                logging.warning(
                    f"[University Repo] [Find Program Profile] Program profile not found: university_id={university_id}, program_id={program_id}"
                )

            return program_profile
        except Exception as e:
            logging.error(f"[University Repo] [Find Program Profile] Error: {str(e)}")
            return None

    async def find_programs_by_university_id(self, university_id: str, limit: int = 1):
        """
        Find programs by university_id. Returns a list of programs.
        Useful when no specific program_id is provided.
        """
        try:
            logging.info(
                f"[University Repo] [Find Programs By University ID] Finding programs: university_id={university_id}, limit={limit}"
            )

            programs = await self.mongo_repo.find_many(
                query={"university_id": university_id},
                projection={"_id": 0},
                sort=None,
                collection_name=self.programs_collection,
            )

            # Limit results
            if limit > 0 and len(programs) > limit:
                programs = programs[:limit]

            if programs:
                logging.info(
                    f"[University Repo] [Find Programs By University ID] Found {len(programs)} program(s) for university_id: {university_id}"
                )
            else:
                logging.warning(
                    f"[University Repo] [Find Programs By University ID] No programs found for university_id: {university_id}"
                )

            return programs
        except Exception as e:
            logging.error(
                f"[University Repo] [Find Programs By University ID] Error: {str(e)}"
            )
            return []

    async def find_program_by_university_id_and_study_level(
        self, university_id: str, study_level: str
    ):
        """
        Find a program by university_id and study_level.
        Returns the first matching program or None.
        """
        try:
            logging.info(
                f"[University Repo] [Find Program By University ID And Study Level] Finding program: university_id={university_id}, study_level={study_level}"
            )

            query = {
                "university_id": university_id,
                "$or": [
                    {"degree_level": study_level.lower()},
                    {"study_level": study_level.lower()},
                ],
            }

            program = await self.mongo_repo.find_one(
                query=query,
                projection={"_id": 0},
                collection_name=self.programs_collection,
            )

            if program:
                logging.info(
                    f"[University Repo] [Find Program By University ID And Study Level] Found program for university_id: {university_id}, study_level: {study_level}"
                )
            else:
                logging.debug(
                    f"[University Repo] [Find Program By University ID And Study Level] No program found for university_id: {university_id}, study_level: {study_level}"
                )

            return program
        except Exception as e:
            logging.error(
                f"[University Repo] [Find Program By University ID And Study Level] Error: {str(e)}"
            )
            return None

    async def find_admission_cycle(self, university_id: str, study_level: str):
        try:
            logging.info(
                f"[University Repo] [Find Admission Cycle] Finding admission cycle: university_id={university_id}, study_level={study_level}"
            )

            admission_cycle = await self.mongo_repo.find_one(
                {"university_id": university_id, "study_level": study_level},
                None,
                self.admission_cycles_collection,
            )

            if admission_cycle:
                logging.info(
                    f"[University Repo] [Find Admission Cycle] Found admission cycle: university_id={university_id}, study_level={study_level}"
                )
            else:
                logging.warning(
                    f"[University Repo] [Find Admission Cycle] Admission cycle not found: university_id={university_id}, study_level={study_level}"
                )

            return admission_cycle
        except Exception as e:
            logging.error(f"[University Repo] [Find Admission Cycle] Error: {str(e)}")
            return None

    async def find_admission_requirements(self, university_id: str, study_level: str):
        try:
            logging.info(
                f"[University Repo] [Find Admission Requirements] Finding admission requirements: university_id={university_id}, study_level={study_level}"
            )

            # Try to find by degree_level first, then by study_level (for backward compatibility)
            admission_requirements = await self.mongo_repo.find_one(
                {"university_id": university_id, "study_level": study_level},
                None,
                self.admission_requirements_collection,
            )

            if admission_requirements:
                logging.info(
                    f"[University Repo] [Find Admission Requirements] Found admission requirements: university_id={university_id}, study_level={study_level}"
                )
            else:
                logging.warning(
                    f"[University Repo] [Find Admission Requirements] Admission requirements not found: university_id={university_id}, study_level={study_level}"
                )

            return admission_requirements
        except Exception as e:
            logging.error(
                f"[University Repo] [Find Admission Requirements] Error: {str(e)}"
            )
            return None

    async def find_admission_requirement_by_program_id(self, program_id: str):
        try:
            logging.info(
                f"[University Repo] [Find Admission Requirements] Finding admission requirements"
            )

            admission_requirements = await self.mongo_repo.find_one(
                {
                    "program_id": program_id,
                },
                None,
                self.admission_requirements_collection,
            )

            if admission_requirements:
                logging.info(
                    f"[University Repo] [Find Admission Requirements] Found admission requirements: "
                )
            else:
                logging.warning(
                    f"[University Repo] [Find Admission Requirements] Admission requirements not found: "
                )

            return admission_requirements
        except Exception as e:
            logging.error(
                f"[University Repo] [Find Admission Requirements] Error: {str(e)}"
            )
            return None
