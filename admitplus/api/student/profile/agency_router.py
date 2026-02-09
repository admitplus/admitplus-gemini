import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from admitplus.common.response_schema import Response
from ..schemas.student_schema import (
    StudentCreateByAgencyRequest,
    StudentDetailResponse,
    StudentListResponse,
    StudentAssignmentListResponse,
    StudentAssignmentResponse,
    StudentUpdateRequest,
    StudentAssignmentCreateRequest,
)
from ..student_service import StudentService
from admitplus.dependencies.role_check import (
    RoleChecker,
    Role,
    CurrentUser,
    get_current_user,
)
from admitplus.api.analysis.analyze_service import AnalysisService
from admitplus.api.files.file_service import FileService
from admitplus.config import settings


router = APIRouter(prefix="/students/agency", tags=["Student Profile"])

student_service = StudentService()
analysis_service = AnalysisService()
file_service = FileService()


"""
Student Profile Management Endpoints
Handles CRUD operations for student profiles including creation, retrieval, update, and listing.
"""


@router.post(
    "",
    response_model=Response[StudentDetailResponse],
    description="Create a student profile",
)
async def create_student_by_agency_handler(
    request: StudentCreateByAgencyRequest,
    current_user: CurrentUser = Depends(
        RoleChecker(role=[Role.AGENCY_MEMBER, Role.AGENCY_ADMIN])
    ),
):
    """
    Create a student profile
    """
    logging.info(
        f"[Student Router] [CreateStudentProfile] Creating student profile by user: {current_user.user_id}"
    )
    try:
        result = await student_service.create_student_by_agency(
            request, created_by_member_id=current_user.user_id
        )
        logging.info(
            f"[Student Router] [CreateStudentProfile] Successfully created student profile: {result.student_id}"
        )
        return Response(
            code=201, message="Student profile created successfully", data=result
        )
    except HTTPException as http_err:
        logging.warning(
            f"[Student Router] [CreateStudentProfile] HTTP error: {http_err.detail}"
        )
        raise http_err
    except Exception as e:
        logging.error(
            f"[Student Router] [CreateStudentProfile] Error creating student profile: {str(e)}"
        )
        logging.error(
            f"[Student Router] [CreateStudentProfile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student profile creation",
        )


@router.get("/{student_id}", response_model=Response[StudentDetailResponse])
async def get_student_detail_handler(
    student_id: str,
    _: CurrentUser = Depends(
        RoleChecker(role=[Role.AGENCY_ADMIN, Role.AGENCY_MEMBER, Role.STUDENT])
    ),
):
    """
    Get students profile information by students ID
    Allows access for STUDENT, AGENCY_MEMBER, and AGENCY_ADMIN roles
    """
    logging.info(
        f"[Student Router] [GetStudentProfile] Getting students profile for student_id: {student_id}"
    )
    try:
        if not student_id or not student_id.strip():
            raise HTTPException(status_code=400, detail="Student ID is required")

        result = await student_service.get_student_detail(student_id)
        logging.info(
            f"[Student Router] [GetStudentProfile] Successfully retrieved students profile for student_id: {student_id}"
        )
        return Response(
            code=200, message="Student profile retrieved successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [GetStudentProfile] Error getting students profile for student_id {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [GetStudentProfile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during students profile retrieval",
        )


@router.patch("/{student_id}", response_model=Response[StudentDetailResponse])
async def update_student_profile_handler(
    student_id: str, request: StudentUpdateRequest
):
    """
    Update existing students profile information
    """
    logging.info(
        f"[Student Router] [UpdateStudentProfile] Updating students profile for student_id: {student_id}"
    )
    try:
        if not student_id or not student_id.strip():
            raise HTTPException(status_code=400, detail="Student ID is required")

        result = await student_service.update_student_profile(student_id, request)
        logging.info(
            f"[Student Router] [UpdateStudentProfile] Successfully updated students profile for student_id: {student_id}"
        )
        return Response(
            code=200, message="Student profile updated successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [UpdateStudentProfile] Error updating students profile for student_id {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [UpdateStudentProfile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during students profile update",
        )


"""
Student Assignment Management Endpoints
Handles assignment operations for students including creating and listing assignments.
"""


@router.post(
    "/{student_id}/assignments", response_model=Response[StudentAssignmentResponse]
)
async def create_student_assignment_handler(
    student_id: str,
    request: StudentAssignmentCreateRequest,
    _: CurrentUser = Depends(RoleChecker(role=[Role.AGENCY_ADMIN])),
):
    """
    Create a student assignment (assign a member to a student)
    """
    logging.info(
        f"[Student Router] [CreateStudentAssignment] Creating assignment for student_id: {student_id}, member_id: {request.member_id}"
    )
    try:
        if not student_id or not student_id.strip():
            raise HTTPException(status_code=400, detail="Student ID is required")

        if not request.member_id or not request.member_id.strip():
            raise HTTPException(status_code=400, detail="Member ID is required")

        result = await student_service.add_assignment(
            student_id, request.member_id, request.role
        )

        logging.info(
            f"[Student Router] [CreateStudentAssignment] Successfully created assignment: {result.assignment_id} for student: {student_id}"
        )

        return Response(
            code=200, message="Student assignment created successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [CreateStudentAssignment] Error: {str(e)}, student_id: {student_id}"
        )
        logging.error(
            f"[Student Router] [CreateStudentAssignment] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student assignment creation",
        )


@router.get(
    "/{student_id}/assignments", response_model=Response[StudentAssignmentListResponse]
)
async def list_student_assignments_handler(
    student_id: str,
    page: int = 1,
    page_size: int = 10,
    _: CurrentUser = Depends(RoleChecker(role=[Role.AGENCY_MEMBER])),
):
    """
    List student assignments with pagination
    """
    logging.info(
        f"[Student Router] [ListStudentAssignments] Listing assignments for student_id: {student_id}, page: {page}, page_size: {page_size}"
    )
    try:
        if not student_id or not student_id.strip():
            raise HTTPException(status_code=400, detail="Student ID is required")

        result = await student_service.list_assignments(student_id, page, page_size)
        logging.info(
            f"[Student Router] [ListStudentAssignments] Successfully retrieved {len(result.assignment_list)} assignments for student_id: {student_id}"
        )
        return Response(
            code=200, message="Student assignments retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [ListStudentAssignments] Error listing assignments for student_id {student_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [ListStudentAssignments] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student assignments retrieval",
        )


@router.get("/{agency_id}", response_model=Response[StudentAssignmentListResponse])
async def list_agency_students_handler(
    agency_id: str,
    page: int = 1,
    page_size: int = 10,
    _: CurrentUser = Depends(RoleChecker(role=[Role.AGENCY_MEMBER])),
):
    """
    List student assignments for an agency with pagination
    """
    logging.info(
        f"[Student Router] [ListAgencyStudents] Listing assignments for agency_id: {agency_id}, page: {page}, page_size: {page_size}"
    )
    try:
        if not agency_id or not agency_id.strip():
            raise HTTPException(status_code=400, detail="Agency ID is required")

        result = await student_service.list_agency_students(agency_id, page, page_size)
        logging.info(
            f"[Student Router] [ListAgencyStudents] Successfully retrieved {len(result.assignment_list)} assignments for agency_id: {agency_id}"
        )
        return Response(
            code=200, message="Student assignments retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Student Router] [ListAgencyStudents] Error listing assignments for agency_id {agency_id}: {str(e)}"
        )
        logging.error(
            f"[Student Router] [ListAgencyStudents] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during student assignments retrieval",
        )
