import logging
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import HTTPException

from .repos.student_profile_repo import StudentRepo
from .repos.student_assignment_repo import StudentAssignmentRepo
from .student_model import StudentProfile
from .schemas.student_schema import (
    StudentDetailResponse,
    StudentListResponse,
    StudentAssignmentListResponse,
    StudentAssignmentResponse,
)
from admitplus.utils.crypto_utils import generate_uuid


class StudentService:
    def __init__(self):
        self.student_repo = StudentRepo()
        self.student_assignment_repo = StudentAssignmentRepo()
        logging.info(f"[Student Service] Initialized with repositories")

    async def create_student_by_agency(
        self, student_profile_data, created_by_member_id: Optional[str] = None
    ) -> StudentDetailResponse:
        try:
            student_id = generate_uuid()
            logging.info(
                f"[Student Service] [CreateStudentProfile] Creating student profile: {student_id}"
            )

            # Convert request to StudentProfile model with validation
            request_dict = (
                student_profile_data.model_dump(exclude_none=True)
                if hasattr(student_profile_data, "model_dump")
                else student_profile_data.dict(exclude_none=True)
            )

            # Create StudentProfile with validation
            now = datetime.utcnow()
            student_profile = StudentProfile(
                student_id=student_id,
                stage=request_dict.get("stage") or "unknown",
                source="agency",
                basic_info=request_dict["basic_info"],
                education=request_dict.get("education"),
                test_scores=request_dict.get("test_scores"),
                background=request_dict.get("background"),
                created_by_member_id=created_by_member_id,
                created_at=now,
                updated_at=now,
            )

            # Convert to dict for storage
            profile_dict = student_profile.model_dump(mode="json", exclude_none=True)

            insert_id = await self.student_repo.create_student_profile(
                student_id, profile_dict
            )
            if not insert_id:
                raise HTTPException(
                    status_code=500, detail="Failed to create student profile"
                )

            # Auto-create assignment for the creator member
            if created_by_member_id:
                assignment_id = generate_uuid()
                assignment_insert_id = (
                    await self.student_assignment_repo.create_student_assignment(
                        student_id, created_by_member_id, assignment_id, role=None
                    )
                )
                if not assignment_insert_id:
                    logging.error(
                        f"[Student Service] [CreateStudentProfile] Failed to create assignment for student: {student_id}"
                    )
                    raise HTTPException(
                        status_code=500, detail="Failed to create student assignment"
                    )
                logging.info(
                    f"[Student Service] [CreateStudentProfile] Auto-created assignment: {assignment_id} for student: {student_id}"
                )

            logging.info(
                f"[Student Service] [CreateStudentProfile] Successfully created student profile: {student_id}"
            )
            # Return the validated StudentProfile directly (timestamps may differ slightly from DB, acceptable)
            return StudentDetailResponse(**student_profile.model_dump(mode="json"))
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [CreateStudentProfile] Error creating student profile: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to create student profile"
            )

    async def get_my_students(
        self,
        member_id: str,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> StudentListResponse:
        """
        Get students assigned to the current member based on student_assignments
        """
        try:
            logging.info(
                f"[Student Service] [GetMyStudents] Getting students for member_id: {member_id}, search: {search}, page: {page}, page_size: {page_size}"
            )

            # Validate pagination parameters
            if page < 1:
                raise HTTPException(
                    status_code=400, detail="Page number must be greater than 0"
                )
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=400, detail="Page size must be between 1 and 100"
                )

            # Step 1: Get all student_ids assigned to this member
            student_ids = (
                await self.student_assignment_repo.find_student_ids_by_member_id(
                    member_id
                )
            )

            if not student_ids:
                logging.info(
                    f"[Student Service] [GetMyStudents] No students assigned to member_id: {member_id}"
                )
                return StudentListResponse(
                    student_list=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    has_next=False,
                    has_prev=False,
                )

            # Step 2: Fetch students from repository with pagination and search filter
            (
                student_dicts,
                total_count,
            ) = await self.student_repo.find_students_by_student_ids(
                student_ids=student_ids, search=search, page=page, page_size=page_size
            )

            # Convert dicts to StudentProfile objects
            student_profiles = []
            for student_dict in student_dicts:
                try:
                    student_profile = StudentProfile(**student_dict)
                    student_profiles.append(student_profile)
                except Exception as e:
                    logging.warning(
                        f"[Student Service] [GetMyStudents] Skipping invalid student data: {str(e)}"
                    )
                    continue

            # Calculate pagination info
            has_next = (page * page_size) < total_count
            has_prev = page > 1

            logging.info(
                f"[Student Service] [GetMyStudents] Successfully retrieved {len(student_profiles)}/{total_count} students for member_id: {member_id}"
            )
            return StudentListResponse(
                student_list=student_profiles,
                total=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_prev=has_prev,
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [GetMyStudents] Error getting students: {str(e)}"
            )
            logging.error(
                f"[Student Service] [GetMyStudents] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to retrieve student list"
            )

    async def get_student_detail(self, student_id) -> StudentDetailResponse:
        """
        Get a student's detailed profile by ID.

        Args:
            student_id: The unique identifier of the student.

        Returns:
            StudentDetailResponse: The student's detailed profile.

        Raises:
            HTTPException: If the student profile is not found (404) or if
                there is an internal server error (500) when fetching the profile.
        """
        try:
            logging.info(
                f"[Student Service] [GetStudentProfile] Get students profile: {student_id}"
            )

            student_profile = await self.student_repo.find_student_by_id(student_id)
            if not student_profile:
                raise HTTPException(status_code=404, detail="Student profile not found")

            return StudentDetailResponse.model_validate(student_profile)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [GetStudentProfile] Error getting students profile: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to get students profile"
            )

    async def update_student_profile(
        self, student_id: str, student_profile_data
    ) -> StudentDetailResponse:
        """
        Update a student's profile by ID.

        Args:
            student_id: The unique identifier of the student.
            student_profile_data: The new profile data used to update the student.
                Can be a Pydantic model or a plain dict; only non-null fields
                are applied. Nested ``basic_info`` fields are merged with
                existing data.

        Returns:
            StudentDetailResponse: The updated student's detailed profile.

        Raises:
            HTTPException: If the student profile is not found (404), if the
                update operation fails (500), or if the updated profile cannot
                be retrieved (500).
        """
        try:
            logging.info(
                f"[Student Service] [UpdateStudentProfile] Updating students profile: {student_id}"
            )

            # Get existing student profile
            existing_profile = await self.student_repo.find_student_by_id(student_id)
            if not existing_profile:
                raise HTTPException(status_code=404, detail="Student profile not found")

            # Convert Pydantic model to dict if needed
            if hasattr(student_profile_data, "model_dump"):
                update_dict = student_profile_data.model_dump(exclude_none=True)
            elif hasattr(student_profile_data, "dict"):
                update_dict = student_profile_data.dict(exclude_none=True)
            else:
                update_dict = student_profile_data

            # Handle nested basic_info update - merge with existing data
            if "basic_info" in update_dict and update_dict["basic_info"]:
                existing_basic_info = existing_profile.get("basic_info", {})
                # Merge existing basic_info with update data
                merged_basic_info = {**existing_basic_info, **update_dict["basic_info"]}
                update_dict["basic_info"] = merged_basic_info

            # Use StudentRepository to update students profile
            result = await self.student_repo.update_student_profile(
                student_id, update_dict
            )
            if result == 0:
                raise HTTPException(
                    status_code=500, detail="Failed to update students profile"
                )

            # Get updated students profile
            updated_profile = await self.student_repo.find_student_by_id(student_id)
            if not updated_profile:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve updated students profile",
                )

            # Convert to StudentDetailResponse using model_validate for proper nested model handling
            return StudentDetailResponse.model_validate(updated_profile)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [UpdateStudentProfile] Error updating students profile: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to update students profile"
            )

    """
    Student Assignment Management Endpoints
    """

    async def add_assignment(
        self, student_id, member_id, role: Optional[str] = None
    ) -> StudentAssignmentResponse:
        try:
            logging.info(
                f"[Student Service] [AddAssignment] Creating assignment for student_id: {student_id}, member_id: {member_id}"
            )

            assignment_id = generate_uuid()
            now = datetime.utcnow()

            insert_id = await self.student_assignment_repo.create_student_assignment(
                student_id, member_id, assignment_id, role=role
            )

            if not insert_id:
                raise HTTPException(
                    status_code=500, detail="Failed to create student assignment"
                )

            logging.info(
                f"[Student Service] [AddAssignment] Successfully created assignment: {assignment_id}"
            )

            return StudentAssignmentResponse(
                assignment_id=assignment_id,
                student_id=student_id,
                member_id=member_id,
                role=role,
                created_at=now,
                updated_at=now,
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [AddAssignment] Error creating student assignment: {str(e)}"
            )
            logging.error(
                f"[Student Service] [AddAssignment] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to create student assignment"
            )

    async def list_assignments(
        self, student_id: str, page: int = 1, page_size: int = 10
    ) -> StudentAssignmentListResponse:
        try:
            logging.info(
                f"[Student Service] [ListStudentAssignments] Listing assignments for student_id: {student_id}, page: {page}, page_size: {page_size}"
            )

            # Validate pagination parameters
            if page < 1:
                raise HTTPException(
                    status_code=400, detail="Page number must be greater than 0"
                )
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=400, detail="Page size must be between 1 and 100"
                )

            (
                assignment_dicts,
                total_count,
            ) = await self.student_assignment_repo.find_student_assignments(
                student_id, page, page_size
            )

            assignment_list = []
            for assignment_dict in assignment_dicts:
                try:
                    assignment = StudentAssignmentResponse(**assignment_dict)
                    assignment_list.append(assignment)
                except Exception as e:
                    logging.warning(
                        f"[Student Service] [ListStudentAssignments] Skipping invalid assignment data: {str(e)}"
                    )
                    continue

            logging.info(
                f"[Student Service] [ListStudentAssignments] Successfully retrieved {len(assignment_list)}/{total_count} assignments for student_id: {student_id}"
            )
            return StudentAssignmentListResponse(assignment_list=assignment_list)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [ListStudentAssignments] Error listing student assignments: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to list student assignments"
            )

    async def list_agency_students(
        self, agency_id: str, page: int = 1, page_size: int = 10
    ) -> StudentAssignmentListResponse:
        try:
            logging.info(
                f"[Student Service] [ListAgencyStudents] Listing assignments for agency_id: {agency_id}, page: {page}, page_size: {page_size}"
            )

            # Validate pagination parameters
            if page < 1:
                raise HTTPException(
                    status_code=400, detail="Page number must be greater than 0"
                )
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=400, detail="Page size must be between 1 and 100"
                )

            (
                assignment_dicts,
                total_count,
            ) = await self.student_assignment_repo.find_student_ids_by_agency_id(
                agency_id, page, page_size
            )

            assignment_list = []
            for assignment_dict in assignment_dicts:
                try:
                    assignment = StudentAssignmentResponse(**assignment_dict)
                    assignment_list.append(assignment)
                except Exception as e:
                    logging.warning(
                        f"[Student Service] [ListAgencyStudents] Skipping invalid assignment data: {str(e)}"
                    )
                    continue

            logging.info(
                f"[Student Service] [ListAgencyStudents] Successfully retrieved {len(assignment_list)}/{total_count} assignments for agency_id: {agency_id}"
            )
            return StudentAssignmentListResponse(assignment_list=assignment_list)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Service] [ListAgencyStudents] Error listing student assignments: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to list student assignments"
            )

    async def ensure_member_can_access_student(
        self, student_id: str, member_id: str
    ) -> None:
        """
        Ensure that a member has access to a student by checking student assignments.
        Uses efficient direct query instead of fetching all student_ids.
        Allows access if member_id equals student_id (student accessing their own resources).
        Raises HTTPException with 403 if access is denied.
        """
        logging.info(
            f"[Student Service] [Ensure Member Access] Checking access for member {member_id} to student {student_id}"
        )

        # Allow access if member is accessing their own student resources
        if member_id == student_id:
            logging.info(
                f"[Student Service] [Ensure Member Access] Access granted: member {member_id} is accessing their own student resources"
            )
            return

        has_access = (
            await self.student_assignment_repo.check_member_has_access_to_student(
                member_id=member_id, student_id=student_id
            )
        )

        if not has_access:
            logging.warning(
                f"[Student Service] [Ensure Member Access] Access denied: member {member_id} does not have access to student {student_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied. Member does not have access to this student",
            )

        logging.info(
            f"[Student Service] [Ensure Member Access] Access granted: member {member_id} has access to student {student_id}"
        )
