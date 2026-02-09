from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr


# ---------------- Enums ----------------
class StudentStage(str, Enum):
    high_school = "high_school"
    undergraduate = "undergraduate"
    graduate = "graduate"
    phd = "phd"
    unknown = "unknown"


class EducationLevel(str, Enum):
    high_school = "high_school"
    bachelor = "bachelor"
    master = "master"
    phd = "phd"
    other = "other"


# ---------------- Sub-models ----------------
class StudentBasicInfo(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class StudentEducationSummary(BaseModel):
    current_school: Optional[str] = None
    grade: Optional[str] = None
    curriculum: Optional[str] = None
    gpa: Optional[float] = None


class StudentTestScores(BaseModel):
    ielts: Optional[str] = None
    toefl: Optional[str] = None
    sat: Optional[str] = None
    act: Optional[str] = None
    gre: Optional[str] = None
    gmat: Optional[str] = None


class EducationRecord(BaseModel):
    level: EducationLevel
    school_name: str
    major: Optional[str] = None
    curriculum: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[float] = None
    is_current: bool = False


class StudentBackground(BaseModel):
    activities: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    volunteer: List[str] = Field(default_factory=list)
    research: List[str] = Field(default_factory=list)
    internship: List[str] = Field(default_factory=list)
    competitions: List[str] = Field(default_factory=list)
    budget: Optional[float] = None
    purpose: Optional[str] = None
    location_preference: Optional[str] = None
    target_major: Optional[str] = None
    education_history: List[EducationRecord] = Field(default_factory=list)


# ---------------- Main Stored Profile ----------------
class StudentProfile(BaseModel):
    """MongoDB student_profiles 文档的实际结构"""

    student_id: str  # UUID
    stage: StudentStage = StudentStage.unknown
    source: Literal["agency", "self", "other"] = "agency"

    basic_info: StudentBasicInfo
    education: Optional[StudentEducationSummary] = None
    test_scores: Optional[StudentTestScores] = None
    background: Optional[StudentBackground] = None

    created_by_member_id: Optional[str] = None
    applications_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
