import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class StudentRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.student_profile_collection = settings.STUDENT_PROFILES_COLLECTION
        self.student_applications_collection = settings.STUDENT_APPLICATIONS_COLLECTION
        logging.info(
            f"[Student Repo] Initialized with db: {self.db_name}, student_collection: {self.student_profile_collection}"
        )

    # ==================== Student Profile by Agency ====================

    async def create_student_profile(
        self, student_id: str, profile_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a new student profile
        """
        try:
            logging.info(
                f"[Student Repo] [Create Student Profile] Creating student profile: {student_id}"
            )

            profile_data_clean = {
                k: v
                for k, v in profile_data.items()
                if k not in ["student_id", "created_at", "updated_at"]
            }

            # Set timestamps at repository level for consistency
            now = datetime.utcnow()
            document = {
                **profile_data_clean,
                "student_id": student_id,
                "created_at": now,
                "updated_at": now,
            }

            result = await self.mongo_repo.insert_one(
                document=document, collection_name=self.student_profile_collection
            )

            if result:
                logging.info(
                    f"[Student Repo] [Create Student Profile] Successfully created student profile: {student_id}"
                )
            else:
                logging.error(
                    f"[Student Repo] [Create Student Profile] Failed to create student profile: {student_id}"
                )

            return result

        except Exception as e:
            logging.error(f"[Student Repo] [Create Student Profile] Error: {str(e)}")
            return None

    async def find_students_by_student_ids(
        self,
        student_ids: List[str],
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Find students by a list of student_ids with optional search filter and pagination
        """
        try:
            logging.info(
                f"[Student Repo] [Find Students By Student IDs] Finding students for {len(student_ids)} student_ids, search: {search}, page: {page}, page_size: {page_size}"
            )

            if not student_ids:
                logging.info(
                    f"[Student Repo] [Find Students By Student IDs] No student_ids provided, returning empty result"
                )
                return [], 0

            # Build query
            query = {"student_id": {"$in": student_ids}}

            # Add search filter if provided
            if search:
                search_pattern = {"$regex": search, "$options": "i"}
                query["$or"] = [
                    {"basic_info.first_name": search_pattern},
                    {"basic_info.last_name": search_pattern},
                    {"basic_info.email": search_pattern},
                    {"basic_info.phone": search_pattern},
                ]

            projection = {"_id": 0}
            result, total_count = await self.mongo_repo.find_many_paginated(
                query=query,
                page=page,
                page_size=page_size,
                sort=[("created_at", -1)],
                projection=projection,
                collection_name=self.student_profile_collection,
            )
            logging.info(
                f"[Student Repo] [Find Students By Student IDs] Found {len(result)}/{total_count} students"
            )
            return result, total_count
        except Exception as e:
            logging.error(
                f"[Student Repo] [Find Students By Student IDs] Error: {str(e)}"
            )
            return [], 0

    async def find_students_with_query(
        self,
        query: Dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        sort: Optional[List[tuple]] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Find students with a custom MongoDB query and pagination

        Args:
            query: MongoDB query dictionary
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort: Sort specification as list of tuples, e.g., [("created_at", -1)]

        Returns:
            Tuple of (students list, total count)
        """
        try:
            logging.info(
                f"[Student Repo] [Find Students With Query] Finding students with query, page: {page}, page_size: {page_size}"
            )

            if sort is None:
                sort = [("created_at", -1)]

            projection = {"_id": 0}
            result, total_count = await self.mongo_repo.find_many_paginated(
                query=query,
                page=page,
                page_size=page_size,
                sort=sort,
                projection=projection,
                collection_name=self.student_profile_collection,
            )
            for item in result:
                applications = await self.mongo_repo.find_many(
                    query={"student_id": item["student_id"]},
                    projection=projection,
                    collection_name=self.student_applications_collection,
                )
                item["applications_count"] = len(applications)
            logging.info(
                f"[Student Repo] [Find Students With Query] Found {len(result)}/{total_count} students"
            )
            return result, total_count
        except Exception as e:
            logging.error(f"[Student Repo] [Find Students With Query] Error: {str(e)}")
            return [], 0

    async def find_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Finds a student record by the given student ID.

        Args:
            student_id (str): The ID of the student to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The student data if found, otherwise None.
        """
        try:
            logging.info(f"[Student Repo] [Find By ID] Finding students: {student_id}")

            projection = {"_id": 0}
            result = await self.mongo_repo.find_one(
                query={"student_id": student_id},
                projection=projection,
                collection_name=self.student_profile_collection,
            )
            if result:
                logging.info(
                    f"[Student Repo] [Find By ID] Found students: {student_id}"
                )
            else:
                logging.warning(
                    f"[Student Repo] [Find By ID] Student not found: {student_id}"
                )
            return result
        except Exception as e:
            logging.error(f"[Student Repo] [Find By ID] Error: {str(e)}")
            return None

    async def update_student_profile(
        self, student_id: str, profile_data: Dict[str, Any]
    ) -> int:
        """
        Updates a student's profile information by student ID.

        Args:
            student_id (str): The ID of the student whose profile will be updated.
            profile_data (Dict[str, Any]): The profile fields and values to update.

        Returns:
            int: The number of documents updated (0 if the update failed).
        """
        try:
            logging.info(
                f"[Student Repo] [Update Profile] Updating students profile: {student_id}"
            )

            profile_data["updated_at"] = datetime.utcnow()

            result = await self.mongo_repo.update_one(
                query={"student_id": student_id},
                update={"$set": profile_data},
                collection_name=self.student_profile_collection,
            )

            if result:
                logging.info(
                    f"[Student Repo] [Update Profile] Successfully updated students: {student_id}"
                )
            return result

        except Exception as e:
            logging.error(f"[Student Repo] [Update Profile] Error: {str(e)}")
            return 0

    # ==================== Trial Students ====================

    async def find_trial_students_by_teacher_id(
        self, teacher_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all trial students for a given teachers
        """
        try:
            logging.info(
                f"[Student Repo] [Find Trial Students] Finding trial students for teachers: {teacher_id}"
            )

            query = {"teacher_id": teacher_id, "type": "trial"}

            result = await self.mongo_repo.find_many(
                query=query,
                sort=[("created_at", -1)],
                collection_name=self.student_collection,
            )

            logging.info(
                f"[Student Repo] [Find Trial Students] Found {len(result)} trial students for teachers: {teacher_id}"
            )
            return result

        except Exception as e:
            logging.error(f"[Student Repo] [Find Trial Students] Error: {str(e)}")
            return []
