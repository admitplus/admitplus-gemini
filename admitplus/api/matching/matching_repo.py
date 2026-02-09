import logging
import traceback

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD
from admitplus.database.redis import BaseRedisCRUD


class MatchingRepo:
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

    # async def filter_by_location(self, request):
    #     """
    #     Filter universities by location (continent and/or country)
    #     """
    #     try:
    #         query = {}
    #         location_query = {}

    #         if request.target_continent:
    #             location_query["continent"] = request.target_continent
    #         if request.target_country:
    #             location_query["country"] = request.target_country

    #         if location_query:
    #             query["location"] = location_query
    #             logging.info(f"[Matching Repo] [Filter By Location] Filtering by location: {location_query}")
    #         else:
    #             logging.info("[Matching Repo] [Filter By Location] No location filters specified, returning all universities")

    #         projection = {
    #             "_id": 0,
    #             "university_id": 1,
    #         }
    #         filter_after_location = await self.mongo_repo.find_many(
    #             query,
    #             projection,
    #             None,
    #             self.university_profiles_collection
    #         )
    #         logging.info(f"[Matching Repo] [Filter By Location] Found {len(filter_after_location)} universities matching location criteria")
    #         return filter_after_location
    #     except Exception as e:
    #         logging.error(f"[Matching Repo] [Filter By Location] Error filtering by location: {str(e)}")
    #         logging.error(f"[Matching Repo] [Filter By Location] Stack trace: {traceback.format_exc()}")
    #         raise

    async def filter_by_location(self, request):
        """
        Filter universities by location (continent and/or country/state)
        """
        try:
            query = {}

            # 构建正确的查询条件
            if request.target_continent:
                query["location.continent"] = request.target_continent

            if request.target_country and request.target_country.strip():
                country_value = request.target_country.strip()
                # 支持按国家或州/省匹配（使用 $or 查询）
                location_conditions = [
                    {"location.country": {"$regex": country_value, "$options": "i"}},
                    {"location.state": {"$regex": country_value, "$options": "i"}},
                    {"location.province": {"$regex": country_value, "$options": "i"}},
                ]
                query["$or"] = location_conditions

            logging.info(
                f"[Matching Repo] [Filter By Location] Filtering by location: {query}"
            )

            projection = {
                "_id": 0,
                "university_id": 1,
            }

            filter_after_location = await self.mongo_repo.find_many(
                query, projection, None, self.university_profiles_collection
            )
            logging.info(
                f"[Matching Repo] [Filter By Location] Found {len(filter_after_location)} universities matching location criteria"
            )
            return filter_after_location

        except Exception as e:
            logging.error(
                f"[Matching Repo] [Filter By Location] Error filtering by location: {str(e)}"
            )
            logging.error(
                f"[Matching Repo] [Filter By Location] Stack trace: {traceback.format_exc()}"
            )
            raise

    async def filter_by_gpa(self, request, university_list):
        """
        Filter universities by GPA requirement (student GPA >= required GPA)
        """
        try:
            if not university_list:
                logging.info(
                    "[Matching Repo] [Filter By GPA] No universities to filter"
                )
                return []

            university_ids = [
                univ.get("university_id")
                for univ in university_list
                if univ.get("university_id")
            ]
            if not university_ids:
                logging.warning(
                    "[Matching Repo] [Filter By GPA] No valid universities IDs found"
                )
                return []

            logging.info(
                f"[Matching Repo] [Filter By GPA] Filtering {len(university_ids)} universities for GPA >= {request.gpa}, degree: {request.target_degree}"
            )

            query = {
                "university_id": {"$in": university_ids},
                "study_level": request.target_degree.lower(),
                "$or": [
                    {"requirements.gpa_average": {"$lte": request.gpa}},
                    {"requirements.gpa_average": {"$exists": False}},
                ],
            }
            projection = {"_id": 0, "university_id": 1}

            matching_requirements = await self.mongo_repo.find_many(
                query, projection, None, self.admission_requirements_collection
            )

            matching_ids = {
                req.get("university_id")
                for req in matching_requirements
                if req.get("university_id")
            }
            filtered = [
                univ
                for univ in university_list
                if univ.get("university_id") in matching_ids
            ]

            logging.info(
                f"[Matching Repo] [Filter By GPA] Filtered {len(university_list)} -> {len(filtered)} universities (GPA: {request.gpa})"
            )
            return filtered
        except Exception as e:
            logging.error(
                f"[Matching Repo] [Filter By GPA] Error filtering by GPA: {str(e)}"
            )
            logging.error(
                f"[Matching Repo] [Filter By GPA] Stack trace: {traceback.format_exc()}"
            )
            raise

    async def filter_by_major(self, request, university_list):
        try:
            if not university_list:
                return {"programs": []}

            university_ids = [
                univ.get("university_id")
                for univ in university_list
                if univ.get("university_id")
            ]
            if not university_ids:
                return {"programs": []}

            logging.info(
                f"[Matching Repo] [Filter By Major] Filtering {len(university_ids)} universities for major '{request.major}', degree: '{request.target_degree}'"
            )

            # Map degree level to database values
            degree_mapping = {
                "Undergraduate": ["undergraduate", "bachelor", "bachelors"],
                "Graduate": ["graduate", "masters", "master"],
                "PhD": ["phd", "doctoral", "doctorate"],
            }
            degree_levels = degree_mapping.get(
                request.target_degree, [request.target_degree.lower()]
            )

            # 专业匹配条件：精确匹配优先，模糊匹配备用
            major_conditions = []
            major_lower = request.major.lower()

            # 精确匹配
            major_conditions.append({"subdiscipline": request.major})
            major_conditions.append({"program_name": request.major})
            major_conditions.append({"discipline": request.major})

            # 模糊匹配（如果精确匹配找不到）
            major_conditions.append(
                {"subdiscipline": {"$regex": major_lower, "$options": "i"}}
            )
            major_conditions.append(
                {"program_name": {"$regex": major_lower, "$options": "i"}}
            )
            major_conditions.append(
                {"discipline": {"$regex": major_lower, "$options": "i"}}
            )

            # 添加包含关系匹配（如 "Computer" 匹配 "Computer Science"）
            if " " in request.major:
                words = request.major.split()
                for word in words:
                    if len(word) > 3:  # 只对长度大于3的单词进行匹配
                        major_conditions.append(
                            {"subdiscipline": {"$regex": word, "$options": "i"}}
                        )
                        major_conditions.append(
                            {"program_name": {"$regex": word, "$options": "i"}}
                        )

            # 构建查询条件 - 必须同时满足：university_id、degree_level 和 major 条件
            major_query = {
                "university_id": {"$in": university_ids},
                "$and": [
                    {
                        "$or": [
                            {"degree_level": {"$in": degree_levels}},
                            {"study_level": {"$in": degree_levels}},
                        ]
                    },
                    {"$or": major_conditions},
                ],
            }

            projection = {
                "_id": 0,
                "program_id": 1,
                "university_id": 1,
                "program_name": 1,
                "subdiscipline": 1,
            }

            matching_programs = await self.mongo_repo.find_many(
                major_query, projection, None, self.programs_collection
            )

            programs = [
                prog
                for prog in matching_programs
                if prog.get("program_id") and prog.get("university_id")
            ]

            # Fetch university_name and logo_url from university_profiles_collection
            if programs:
                unique_university_ids = list(
                    set(
                        [
                            prog.get("university_id")
                            for prog in programs
                            if prog.get("university_id")
                        ]
                    )
                )

                # Query university profiles to get university_name and logo_url
                university_query = {"university_id": {"$in": unique_university_ids}}
                university_projection = {
                    "_id": 0,
                    "university_id": 1,
                    "university_name": 1,
                    "logo_url": 1,
                }

                university_profiles = await self.mongo_repo.find_many(
                    university_query,
                    university_projection,
                    None,
                    self.university_profiles_collection,
                )

                # Create a mapping of university_id to university_name and logo_url
                university_info_map = {}
                for profile in university_profiles:
                    university_id = profile.get("university_id")
                    if university_id:
                        university_info_map[university_id] = {
                            "university_name": profile.get("university_name", ""),
                            "university_logo": profile.get("logo_url", ""),
                        }

                # Add university_name and university_logo to each program
                for prog in programs:
                    university_id = prog.get("university_id")
                    if university_id in university_info_map:
                        prog["university_name"] = university_info_map[university_id][
                            "university_name"
                        ]
                        prog["university_logo"] = university_info_map[university_id][
                            "university_logo"
                        ]
                    else:
                        # Fallback if university not found
                        prog["university_name"] = ""
                        prog["university_logo"] = ""
                        logging.warning(
                            f"[Matching Repo] [Filter By Major] University profile not found for university_id: {university_id}"
                        )

            result = {"programs": programs}

            logging.info(
                f"[Matching Repo] [Filter By Major] Found {len(programs)} matching programs"
            )
            return result

        except Exception as e:
            logging.error(f"[Matching Repo] [Filter By Major] Error: {str(e)}")
            raise
