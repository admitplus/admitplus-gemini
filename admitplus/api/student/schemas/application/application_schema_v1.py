from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    """Application status enumeration"""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"
    DEFERRED = "deferred"
    WITHDRAWN = "withdrawn"


class ApplicationEventType(str, Enum):
    """Application event type enumeration"""

    CREATED = "created"
    UPDATED = "updated"
    SUBMITTED = "submitted"
    STATUS_CHANGED = "status_changed"
    COUNSELOR_ASSIGNED = "counselor_assigned"
    COUNSELOR_CHANGED = "counselor_changed"
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_REMOVED = "document_removed"
    NOTE_ADDED = "note_added"
    DEADLINE_EXTENDED = "deadline_extended"
    WITHDRAWN = "withdrawn"


class Application(BaseModel):
    """Main applications object"""

    application_id: str = Field(..., description="Application ID")
    student_id: str = Field(..., description="Student ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    degree_level: str = Field(..., description="Degree level")
    status: ApplicationStatus = Field(..., description="Application status")
    owner_uid: str = Field(..., description="Owner users ID")
    counselor_uid: Optional[str] = Field(
        None, description="Assigned counselor users ID"
    )
    due_date: Optional[datetime] = Field(None, description="Application due date")
    submitted_at: Optional[datetime] = Field(
        None, description="When applications was submitted"
    )
    notes: Optional[str] = Field(None, description="Application notes")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime = Field(..., description="When applications was created")
    updated_at: datetime = Field(..., description="When applications was last updated")


class ApplicationEvent(BaseModel):
    """Application event for timeline/audit"""

    event_id: str = Field(..., description="Event ID")
    application_id: str = Field(..., description="Application ID")
    event_type: ApplicationEventType = Field(..., description="Event type")
    description: str = Field(..., description="Event description")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    created_by: str = Field(..., description="User who created the event")
    created_at: datetime = Field(..., description="When event was created")


class ApplicationResponse(BaseModel):
    """Response model for applications operations"""

    application: Application = Field(..., description="Application data")
    message: str = Field(..., description="Response message")


class ApplicationListResponse(BaseModel):
    """Response model for applications list"""

    applications: List[Application] = Field(..., description="List of applications")
    total: int = Field(..., description="Total number of applications")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of items per page")
    has_next: Optional[bool] = Field(None, description="Whether there are more pages")
    has_prev: Optional[bool] = Field(
        None, description="Whether there are previous pages"
    )


class ApplicationQueryRequest(BaseModel):
    """Request model for applications queries"""

    status: Optional[ApplicationStatus] = Field(None, description="Filter by status")
    owner_uid: Optional[str] = Field(None, description="Filter by owner")
    counselor_uid: Optional[str] = Field(None, description="Filter by counselor")
    due_before: Optional[datetime] = Field(None, description="Filter by due date")
    university_name: Optional[str] = Field(
        None, description="Filter by universities name"
    )
    program_name: Optional[str] = Field(None, description="Filter by program name")
    search: Optional[str] = Field(None, description="Search term")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")


class CreateApplicationRequest(BaseModel):
    """Request model for creating an applications"""

    student_id: str = Field(..., description="Student ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    degree_level: str = Field(..., description="Degree level")
    due_date: Optional[datetime] = Field(None, description="Application due date")
    notes: Optional[str] = Field(None, description="Application notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateApplicationRequest(BaseModel):
    """Request model for updating an applications"""

    university_name: Optional[str] = Field(None, description="University name")
    program_name: Optional[str] = Field(None, description="Program name")
    degree_level: Optional[str] = Field(None, description="Degree level")
    due_date: Optional[datetime] = Field(None, description="Application due date")
    notes: Optional[str] = Field(None, description="Application notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AssignCounselorRequest(BaseModel):
    """Request model for assigning a counselor"""

    counselor_uid: str = Field(..., description="Counselor users ID to assign")


class ChangeStatusRequest(BaseModel):
    """Request model for changing applications status"""

    status: ApplicationStatus = Field(..., description="New applications status")
    notes: Optional[str] = Field(None, description="Notes about the status change")


class SubmitApplicationRequest(BaseModel):
    """Request model for submitting an applications"""

    notes: Optional[str] = Field(None, description="Submission notes")


class ApplicationEventListResponse(BaseModel):
    """Response model for applications event list"""

    events: List[ApplicationEvent] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of items per page")
    has_next: Optional[bool] = Field(None, description="Whether there are more pages")
    has_prev: Optional[bool] = Field(
        None, description="Whether there are previous pages"
    )


class ApplicationEventQueryRequest(BaseModel):
    """Request model for applications event queries"""

    event_type: Optional[ApplicationEventType] = Field(
        None, description="Filter by event type"
    )
    created_by: Optional[str] = Field(None, description="Filter by creator")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")


class CreateEventRequest(BaseModel):
    """Request model for creating an applications event"""

    event_type: ApplicationEventType = Field(..., description="Event type")
    description: str = Field(..., description="Event description")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")


class ApplicationStatsResponse(BaseModel):
    """Response model for applications statistics"""

    total_applications: int = Field(..., description="Total number of applications")
    applications_by_status: Dict[str, int] = Field(
        ..., description="Applications grouped by status"
    )
    applications_by_university: Dict[str, int] = Field(
        ..., description="Applications grouped by universities"
    )
    applications_by_program: Dict[str, int] = Field(
        ..., description="Applications grouped by program"
    )
    recent_applications: List[Application] = Field(
        ..., description="Recent applications"
    )
    upcoming_deadlines: List[Application] = Field(
        ..., description="Applications with upcoming deadlines"
    )
