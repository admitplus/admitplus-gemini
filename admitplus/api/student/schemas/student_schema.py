from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from ..student_model import (
    StudentStage,
    StudentBasicInfo,
    StudentEducationSummary,
    StudentTestScores,
    StudentBackground,
    StudentProfile,
)
from pydantic import EmailStr
from datetime import date


class StudentCreateByAgencyRequest(BaseModel):
    stage: Optional[StudentStage] = None  # 可省略，默认为 unknown
    basic_info: StudentBasicInfo
    education: Optional[StudentEducationSummary] = None
    test_scores: Optional[StudentTestScores] = None
    background: Optional[StudentBackground] = None


class StudentDetailResponse(StudentProfile):
    pass


class StudentListResponse(BaseModel):
    student_list: List[StudentProfile] = Field(..., description="Student details")
    total: int = Field(..., description="Total number of students")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class AgencyStudentsOverviewQueryRequest(BaseModel):
    """
    Request model for querying agency students overview with pagination
    """

    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Number of items per page")


class AgencyStudentsOverviewResponse(BaseModel):
    """
    Response model for agency students overview with pagination
    """

    agency_id: str = Field(..., description="Agency ID")
    students: List[StudentProfile] = Field(..., description="List of student profiles")
    total_count: int = Field(..., description="Total number of students")
    total_pages: int = Field(..., description="Total number of pages")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")


class StudentBasicInfoUpdate(BaseModel):
    """
    Update model for student basic info - all fields optional for partial updates
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class StudentUpdateRequest(BaseModel):
    """
    Request model for updating student profile information
    """

    stage: Optional[StudentStage] = None
    basic_info: Optional[StudentBasicInfoUpdate] = None
    education: Optional[StudentEducationSummary] = None
    test_scores: Optional[StudentTestScores] = None
    background: Optional[StudentBackground] = None


"""
Student Assignment Management Endpoints
"""


class StudentAssignmentCreateRequest(BaseModel):
    member_id: str = Field(..., description="Agency member ID to assign to the student")
    role: Optional[str] = Field(None, description="Role of the member")


class StudentAssignmentResponse(BaseModel):
    assignment_id: str = Field(..., description="Assignment ID")
    student_id: str = Field(..., description="Student ID")
    member_id: str = Field(..., description="Member ID")
    role: Optional[str] = Field(None, description="Role of the member")
    created_at: datetime = Field(..., description="When assignment was created")
    updated_at: datetime = Field(..., description="When assignment was last updated")


class StudentAssignmentListResponse(BaseModel):
    assignment_list: List[StudentAssignmentResponse] = Field(
        ..., description="Student assignment list"
    )


"""
Student Highlight Management Schemas

Schemas for creating, updating, and retrieving student highlights.
Highlights represent important achievements, experiences, or notable information
about students that can be categorized (e.g., academic, research, leadership, impact).
"""


class StudentHighlightCreateRequest(BaseModel):
    category: str = Field(..., description="Highlight category")
    text: str = Field(..., description="Highlight text content")
    importance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Importance score between 0 and 1"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the highlight"
    )
    source_type: Optional[str] = Field(
        default="manual", description="Source type of the highlight"
    )
    source_id: Optional[str] = Field(None, description="Source ID if applicable")


class StudentHighlightResponse(BaseModel):
    highlight_id: str = Field(..., description="Highlight ID")
    student_id: str = Field(..., description="Student ID")
    source_type: str = Field(..., description="Source type")
    source_id: Optional[str] = Field(None, description="Source ID")
    category: str = Field(..., description="Highlight category")
    text: str = Field(..., description="Highlight text content")
    importance_score: float = Field(..., description="Importance score")
    tags: List[str] = Field(default_factory=list, description="Tags")
    created_by_member_id: str = Field(
        ..., description="Member ID who created the highlight"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StudentHighlightListResponse(BaseModel):
    highlight_list: List[StudentHighlightResponse] = Field(
        ..., description="Highlight list"
    )


class StudentHighlightUpdateRequest(BaseModel):
    category: Optional[str] = Field(None, description="Highlight category")
    text: Optional[str] = Field(None, description="Highlight text content")
    importance_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Importance score between 0 and 1"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with the highlight"
    )
    source_type: Optional[str] = Field(None, description="Source type of the highlight")
    source_id: Optional[str] = Field(None, description="Source ID if applicable")


"""
Application Management Schemas
"""


class ApplicationSummary(BaseModel):
    """
    Application summary for students view
    """

    application_id: str = Field(..., description="Application ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    status: str = Field(..., description="Application status")
    created_at: datetime = Field(..., description="When applications was created")
    updated_at: datetime = Field(..., description="When applications was last updated")
    due_date: Optional[datetime] = Field(None, description="Application due date")


class ApplicationListResponse(BaseModel):
    """
    Response model for applications list
    """

    applications: List[ApplicationSummary] = Field(
        ..., description="List of applications"
    )
    total: int = Field(..., description="Total number of applications")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of items per page")
    has_next: Optional[bool] = Field(None, description="Whether there are more pages")
    has_prev: Optional[bool] = Field(
        None, description="Whether there are previous pages"
    )


class CreateApplicationRequest(BaseModel):
    """
    Request model for creating an applications
    """

    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    degree_level: str = Field(..., description="Degree level")
    due_date: Optional[datetime] = Field(None, description="Application due date")
    notes: Optional[str] = Field(None, description="Application notes")


class CreateApplicationResponse(BaseModel):
    """
    Response model for creating an applications
    """

    application_id: str = Field(..., description="Application ID")
    student_id: str = Field(..., description="Student ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    status: str = Field(..., description="Application status")
    created_at: datetime = Field(..., description="When applications was created")
