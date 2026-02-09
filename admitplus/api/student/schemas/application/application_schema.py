from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class StudentApplicationCreateRequest(BaseModel):
    """
    Request model for creating a student application
    """

    university_id: str = Field(..., description="University ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    degree_level: str = Field(..., description="Degree level")


class StudentApplicationResponse(BaseModel):
    """
    Response model for student application
    """

    application_id: str = Field(..., description="Application ID")
    student_id: str = Field(..., description="Student ID")
    university_id: str = Field(..., description="University ID")
    university_name: str = Field(..., description="University name")
    university_logo: str = Field(..., description="University logo")
    program_name: str = Field(..., description="Program name")
    degree_level: str = Field(..., description="Degree level")
    status: str = Field(..., description="Application status")
    result: Optional[str] = Field(None, description="Application result")
    created_by_member_id: Optional[str] = Field(
        None, description="Member ID who created the application"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StudentApplicationListResponse(BaseModel):
    application_list: List[StudentApplicationResponse]


class StudentApplicationDetailResponse(StudentApplicationResponse):
    pass


class StudentApplicationUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="Application status")
    result: Optional[str] = Field(None, description="Application result")
