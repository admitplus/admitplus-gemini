from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Level(str, Enum):
    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    PHD = "phd"


class TestType(str, Enum):
    TOEFL = "TOEFL"
    GRE = "GRE"
    GMAT = "GMAT"
    IELTS = "IELTS"
    SAT = "SAT"
    ACT = "ACT"


class EssayStatus(str, Enum):
    NOT_STARTED = "Not Started"
    DRAFT = "Draft"
    FINALIZED = "Finalized"


class DegreeType(str, Enum):
    BACHELORS = "Bachelor's"
    MASTERS = "Master's"
    PHD = "PhD"


# 基础信息 Schema
class BasicInfoSchema(BaseModel):
    name: str
    gender: Gender
    email: EmailStr
    phone: Optional[str] = None
    wechat: Optional[str] = None
    birth_date: Optional[datetime] = None
    nationality: Optional[str] = None


# 学术记录 Schema
class AcademicRecordSchema(BaseModel):
    level: Level
    school_name: str
    country: str
    curriculum: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    start_date: datetime
    end_date: Optional[datetime] = None


# 考试成绩 Schema
class TestScoreSchema(BaseModel):
    type: TestType
    score: float
    test_date: datetime


# 成就 Schema
class AchievementSchema(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    selected: bool = False
    tags: List[str] = []
    date: Optional[datetime] = None


# 成就分类 Schema
class AchievementsSchema(BaseModel):
    research: List[AchievementSchema] = []
    volunteer: List[AchievementSchema] = []
    work_experience: List[AchievementSchema] = []
    awards: List[AchievementSchema] = []
    other: List[AchievementSchema] = []


# 大学信息 Schema
class UniversityInfoSchema(BaseModel):
    name: str
    country: str


# 建议 Schema
class EssaySuggestionsSchema(BaseModel):
    academic_strengths: Optional[str] = None
    extracurricular_summary: Optional[str] = None
    essay_strategy: Optional[str] = None


# 文章 Schema
class EssaySchema(BaseModel):
    essay_id: str
    question: str
    status: EssayStatus = EssayStatus.NOT_STARTED
    ai_generated: bool = False
    content: Optional[str] = None
    suggestions: Optional[EssaySuggestionsSchema] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# 申请 Schema
class ApplicationSchema(BaseModel):
    university: UniversityInfoSchema
    degree: DegreeType
    major: str
    status: str = "Planning"
    essays: List[EssaySchema] = []


# 学生信息请求 Schema
class StudentInfoRequest(BaseModel):
    agency_id: str
    teacher_id: str
    student_id: str
    created_by: str
    target_degree: Optional[str] = None
    stage: Optional[str] = "incomplete"
    basic: BasicInfoSchema
    academic_records: List[AcademicRecordSchema] = []
    test_scores: List[TestScoreSchema] = []
    achievements: AchievementsSchema = Field(default_factory=AchievementsSchema)
    applications: List[ApplicationSchema] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# 其他已有的 Schema
class AnalysisCreate(BaseModel):
    university: UniversityInfoSchema
    degree: DegreeType
    major: str
    essays: List[EssaySchema] = []

    class Config:
        json_schema_extra = {
            "example": {
                "universities": {"name": "University of Pennsylvania", "country": "US"},
                "degree": "Master's",
                "major": "Computer Science",
                "essays": [
                    {
                        "essay_id": "upenn_q1",
                        "question": "Why UPenn aligns with my academic aspirations?",
                        "status": "Not Started",
                        "ai_generated": False,
                        "last_updated": "2025-10-26T10:00:00Z",
                    }
                ],
            }
        }


class CreateStudentProfileRequest(BaseModel):
    agency_id: str
    teacher_id: str
    target_degree: str
    name: str


class CreateStudentProfileResponse(BaseModel):
    document_id: Optional[str] = None
    success: bool
    message: str
