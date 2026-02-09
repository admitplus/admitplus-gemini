from typing import Literal, Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, model_validator

# Define generic type
T = TypeVar("T")

DegreeLevel = Literal["Undergraduate", "Graduate", "PhD"]
LanguageTestType = Literal["TOEFL", "IELTS"]
RankingType = Literal["QS", "THE", "USNEWS", "ARWU"]
ContinentType = Literal[
    "Asia",
    "Europe",
    "North America",
    "South America",
    "Africa",
    "Oceania",
    "Antarctica",
]


class LanguageScore(BaseModel):
    test: LanguageTestType
    score: float = Field(
        ..., gt=0, description="Language test score (must be greater than 0)"
    )


class CurriculumScore(BaseModel):
    curriculum: str
    score: float


class RankingRange(BaseModel):
    type: RankingType
    min: int = Field(..., ge=1, description="Minimum ranking")
    max: int = Field(..., ge=1, description="Maximum ranking")

    @model_validator(mode="after")
    def validate_max_greater_than_min(self):
        if self.max < self.min:
            raise ValueError("max must be greater than or equal to min")
        return self


class BudgetRange(BaseModel):
    min: Optional[float] = Field(None, ge=0, description="Minimum budget")
    max: Optional[float] = Field(None, ge=0, description="Maximum budget")
    currency: str

    @model_validator(mode="after")
    def validate_max_greater_than_min(self):
        if self.max is not None and self.min is not None:
            if self.max < self.min:
                raise ValueError("max must be greater than or equal to min")
        return self


class UniversitySearchFilter(BaseModel):
    target_continent: Optional[ContinentType] = None
    target_country: Optional[str] = None
    target_degree: DegreeLevel
    gpa: float = Field(..., gt=0, le=4.0, description="Student GPA (0-4.0 scale)")
    major: str = Field(..., min_length=1, description="Target major")
    language: Optional[LanguageScore] = None
    ranking: Optional[RankingRange] = None
    budget: Optional[BudgetRange] = None
    preferred_locations: Optional[str] = None


class MatchingProgram(BaseModel):
    program_id: str
    university_id: str
    university_name: str
    university_logo: Optional[str] = None


class ProgramsResult(BaseModel):
    programs: List[MatchingProgram] = Field(
        ..., description="List of matching programs"
    )


class UniversityWithPrograms(BaseModel):
    university_id: str = Field(..., description="University ID")
    university_name: str = Field(..., description="University name")
    university_logo: Optional[str] = Field(None, description="University logo URL")
    programs: List[MatchingProgram] = Field(
        ..., description="List of programs for this university"
    )


class UniversitiesWithProgramsResult(BaseModel):
    universities: List[UniversityWithPrograms] = Field(
        ..., description="List of universities with their programs"
    )


# Sub-model definitions
class ScoreBreakdown(BaseModel):
    gpa: float = Field(..., ge=0, le=100, description="GPA score (0-100)")
    english: float = Field(..., ge=0, le=100, description="English test score (0-100)")
    standardized: float = Field(
        ..., ge=0, le=100, description="Standardized test score (0-100)"
    )
    curriculum_alignment: float = Field(
        ..., ge=0, le=100, description="Curriculum alignment score (0-100)"
    )
    research_internship: float = Field(
        ..., ge=0, le=100, description="Research/internship score (0-100)"
    )
    ranking_fit: float = Field(
        ..., ge=0, le=100, description="Ranking fit score (0-100)"
    )
    program_constraints: float = Field(
        ..., ge=0, le=100, description="Program constraints score (0-100)"
    )


class RequirementsSnapshot(BaseModel):
    gpa_average: float = Field(..., ge=0, description="Average GPA requirement")
    toefl_min: float = Field(..., ge=0, description="Minimum TOEFL requirement")
    ielts_min: float = Field(..., ge=0, description="Minimum IELTS requirement")
    sat_average: float = Field(..., ge=0, description="Average SAT requirement")
    act_average: float = Field(..., ge=0, description="Average ACT requirement")
    gre_average: float = Field(..., ge=0, description="Average GRE requirement")


class NextRound(BaseModel):
    name: str = Field(..., description="Round name")
    deadline_date: str = Field(..., description="Deadline date in YYYY-MM-DD format")


class ApplicationFee(BaseModel):
    amount: float = Field(..., ge=0, description="Application fee amount")
    currency: str = Field(..., description="Currency code")


# MatchingResult model
class MatchingResult(BaseModel):
    university_id: str = Field(..., description="University ID")
    university_name: str = Field(..., description="University name")
    study_level: str = Field(
        ..., description="Study level (e.g., Bachelor's, Master's, PhD)"
    )
    overall_match: float = Field(
        ..., ge=0, le=100, description="Overall match score (0-100)"
    )
    bucket: str = Field(
        ..., description="Match category: High-Reach|Reach|Match|Target/Strong"
    )
    score_breakdown: ScoreBreakdown = Field(..., description="Detailed score breakdown")
    matching_reason: str = Field(..., description="Concise reason for the match")
    risk_alert: str = Field("", description="Risk alert if any")
    top_positive_factors: List[str] = Field(
        ..., description="List of top positive factors"
    )
    requirement_gaps: List[str] = Field(..., description="List of requirement gaps")
    action_recommendations: List[str] = Field(
        ..., description="List of action recommendations"
    )
    course_overlap_percent: float = Field(
        ..., ge=0, le=100, description="Course overlap percentage"
    )
    requirements_snapshot: RequirementsSnapshot = Field(
        ..., description="Requirements snapshot"
    )
    next_round: NextRound = Field(..., description="Next application round")
    application_fee: ApplicationFee = Field(..., description="Application fee details")
    notes: str = Field("", description="Optional notes")


# Generic response wrapper
class Response(BaseModel, Generic[T]):
    code: int = Field(..., description="Response status code")
    message: str = Field(..., description="Response message")
    data: Optional[T] = Field(None, description="Response data")


# Request model
class MatchingReportRequest(BaseModel):
    university_ids: List[str] = Field(
        ..., min_length=1, max_length=5, description="List of universities IDs (1-5)"
    )
