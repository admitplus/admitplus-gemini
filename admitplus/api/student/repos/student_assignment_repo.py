import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD
from admitplus.api.agency.agency_member_repo import AgencyMemberRepo


class StudentAssignmentRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.student_assignment_repo = BaseMongoCRUD(self.db_name)
        self.agency_member_repo = AgencyMemberRepo()

        self.student_assignments_collection = settings.STUDENT_ASSIGNMENTS_COLLECTION
        logging.info(
            f"[Student Assignment Repo] Initialized with db: {self.db_name}, collection: {self.student_assignments_collection}"
        )

    async def create_student_assignment(
        self, student_id: str, member_id: str, assignment_id: str, role: Optional[str]
    ) -> Optional[str]:
        """
        Create a new student assignment (assign a member to a student)
        """
        try:
            logging.info(
                f"[Student Assignment Repo] [Create Student Assignment] Creating assignment: {assignment_id}"
            )

            now = datetime.utcnow()
            data = {
                "assignment_id": assignment_id,
                "student_id": student_id,
                "member_id": member_id,
                "role": role,
                "created_at": now,
                "updated_at": now,
            }

            insert_id = await self.student_assignment_repo.insert_one(
                document=data, collection_name=self.student_assignments_collection
            )

            if insert_id:
                logging.info(
                    f"[Student Assignment Repo] [Create Student Assignment] Successfully created assignment: {assignment_id}"
                )
            else:
                logging.error(
                    f"[Student Assignment Repo] [Create Student Assignment] Failed to create assignment: {assignment_id}"
                )

            return insert_id

        except Exception as e:
            logging.error(
                f"[Student Assignment Repo] [Create Student Assignment] Error: {str(e)}"
            )
            return None

    async def find_student_assignments(
        self, student_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Find student assignments with pagination
        """
        try:
            logging.info(
                f"[Student Assignment Repo] [Find Student Assignments] Finding assignments for student_id: {student_id}, page: {page}, page_size: {page_size}"
            )

            (
                assignments,
                total_count,
            ) = await self.student_assignment_repo.find_many_paginated(
                query={"student_id": student_id},
                page=page,
                page_size=page_size,
                sort=[("created_at", -1)],
                projection={"_id": 0},
                collection_name=self.student_assignments_collection,
            )

            logging.info(
                f"[Student Assignment Repo] [Find Student Assignments] Found {len(assignments)}/{total_count} assignments for student_id: {student_id}"
            )
            return assignments, total_count
        except Exception as e:
            logging.error(
                f"[Student Assignment Repo] [Find Student Assignments] Error: {str(e)}"
            )
            return [], 0

    async def find_student_ids_by_member_id(self, member_id: str) -> List[str]:
        """
        Find all student_ids assigned to a given member
        """
        try:
            logging.info(
                f"[Student Assignment Repo] [Find Student IDs By Member ID] Finding student_ids for member_id: {member_id}"
            )

            assignments = await self.student_assignment_repo.find_many(
                query={"member_id": member_id},
                projection={"_id": 0, "student_id": 1},
                sort=[("created_at", -1)],
                collection_name=self.student_assignments_collection,
            )

            student_ids = [
                assignment.get("student_id")
                for assignment in assignments
                if assignment.get("student_id")
            ]
            # Remove duplicates while preserving order
            seen = set()
            unique_student_ids = []
            for student_id in student_ids:
                if student_id not in seen:
                    seen.add(student_id)
                    unique_student_ids.append(student_id)

            logging.info(
                f"[Student Assignment Repo] [Find Student IDs By Member ID] Found {len(unique_student_ids)} unique student_ids for member_id: {member_id}"
            )
            return unique_student_ids
        except Exception as e:
            logging.error(
                f"[Student Assignment Repo] [Find Student IDs By Member ID] Error: {str(e)}"
            )
            return []

    async def find_student_ids_by_agency_id(
        self, agency_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Find all student assignments for a given agency with pagination
        """
        try:
            logging.info(
                f"[Student Assignment Repo] [Find Student IDs By Agency ID] Finding assignments for agency_id: {agency_id}, page: {page}, page_size: {page_size}"
            )

            # Step 1: Get all member_ids for the agency
            member_ids = await self.agency_member_repo.find_member_ids_by_agency_id(
                agency_id
            )

            if not member_ids:
                logging.info(
                    f"[Student Assignment Repo] [Find Student IDs By Agency ID] No members found for agency_id: {agency_id}"
                )
                return [], 0

            # Step 2: Query assignments where member_id is in the list of member_ids
            (
                assignments,
                total_count,
            ) = await self.student_assignment_repo.find_many_paginated(
                query={"member_id": {"$in": member_ids}},
                page=page,
                page_size=page_size,
                sort=[("created_at", -1)],
                projection={"_id": 0},
                collection_name=self.student_assignments_collection,
            )

            logging.info(
                f"[Student Assignment Repo] [Find Student IDs By Agency ID] Found {len(assignments)}/{total_count} assignments for agency_id: {agency_id}"
            )
            return assignments, total_count
        except Exception as e:
            logging.error(
                f"[Student Assignment Repo] [Find Student IDs By Agency ID] Error: {str(e)}"
            )
            return [], 0

    async def check_member_has_access_to_student(
        self, member_id: str, student_id: str
    ) -> bool:
        """
        Check if a member has access to a specific student.
        More efficient than fetching all student_ids for the member.
        Returns True if access exists, False otherwise.
        """
        try:
            logging.info(
                f"[Student Assignment Repo] [Check Member Access] Checking if member {member_id} has access to student {student_id}"
            )

            assignment = await self.student_assignment_repo.find_one(
                query={"member_id": member_id, "student_id": student_id},
                projection={"_id": 0, "assignment_id": 1},
                collection_name=self.student_assignments_collection,
            )

            has_access = assignment is not None
            logging.info(
                f"[Student Assignment Repo] [Check Member Access] Member {member_id} {'has' if has_access else 'does not have'} access to student {student_id}"
            )
            return has_access

        except Exception as e:
            logging.error(
                f"[Student Assignment Repo] [Check Member Access] Error checking access: {str(e)}"
            )
            return False

    async def find_all_unique_member_ids(self) -> List[str]:
        """
        Find all unique member_ids from student_assignments collection.
        This is a fallback method when agency_members collection doesn't have the data.

        Returns:
            List of unique member_ids
        """
        try:
            logging.info(
                f"[Student Assignment Repo] [Find All Unique Member IDs] Finding all unique member_ids"
            )

            # Get all assignments with member_id projection
            assignments = await self.student_assignment_repo.find_many(
                query={},
                projection={"_id": 0, "member_id": 1},
                collection_name=self.student_assignments_collection,
            )

            # Extract unique member_ids
            member_ids_set = set()
            for assignment in assignments:
                member_id = assignment.get("member_id")
                if member_id:
                    member_ids_set.add(member_id)

            member_ids = list(member_ids_set)

            logging.info(
                f"[Student Assignment Repo] [Find All Unique Member IDs] Found {len(member_ids)} unique member_ids"
            )
            return member_ids

        except Exception as e:
            logging.error(
                f"[Student Assignment Repo] [Find All Unique Member IDs] Error: {str(e)}"
            )
            return []
