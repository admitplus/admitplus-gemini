from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, validator


class UniversityProgramQueryRequest(BaseModel):
    country: str = Field(...)
    university_id: str = Field(..., min_length=1, description="University ID")
    degree: str = Field(..., description="Degree type")
    program_name: str = Field(
        ..., min_length=1, max_length=200, description="Program name"
    )

    @validator("degree")
    def validate_degree(cls, v):
        allowed_degrees = ["undergraduate", "graduate", "phd"]
        if v.lower() not in allowed_degrees:
            raise ValueError(f"Degree must be one of: {', '.join(allowed_degrees)}")
        return v.lower()

    @validator("university_id", "program_name")
    def validate_string_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or contain only whitespace")
        return v.strip()


class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class ApplicationInfo(BaseModel):
    degree_level: Optional[str] = None
    application_deadlines: Optional[Any] = None
    requirements: Optional[Any] = None
    undergraduate_programs: Optional[Dict[str, Any]] = None


class UniversityProgramResponse(BaseModel):
    university_name: str
    logo_url: str
    location: Optional[Location] = None
    founded_year: Optional[int] = None
    type: Optional[str] = None
    website: Optional[str] = None
    student: Optional[Any] = None
    ranking: Optional[int] = None
    admission_overview_link: Optional[str] = None
    admission_statistics: Optional[Any] = None
    application_info: Optional[ApplicationInfo] = None


class UniversitiesByMajorRequest(BaseModel):
    country: str = Field(...)
    program_name: str = Field(
        ..., min_length=1, max_length=200, description="Program name"
    )
    degree: str = Field(..., description="Degree type")

    @validator("degree")
    def validate_degree(cls, v):
        allowed_degrees = ["undergraduate", "graduate", "phd"]
        if v.lower() not in allowed_degrees:
            raise ValueError(f"Degree must be one of: {', '.join(allowed_degrees)}")
        return v.lower()

    @validator("program_name")
    def validate_program_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Program name cannot be empty or contain only whitespace")
        return v.strip()


class UniversitiesByMajorResponse(BaseModel):
    university_list: List[Dict[str, Any]]


class UniversitySearchResponse(BaseModel):
    universities: List[Dict[str, Any]]
