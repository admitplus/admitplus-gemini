from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum


class InviteStatus(str, Enum):
    """Invite status enumeration"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class InviteType(str, Enum):
    """Invite type enumeration"""

    AGENCY = "agencies"
    STUDENT = "students"


class InviteRequest(BaseModel):
    """Invite request model"""

    email: EmailStr = Field(..., description="Email to send invite to")
    agency_id: str = Field(..., description="Agency ID to invite users to")
    invite_type: InviteType = Field(InviteType.AGENCY, description="Type of invite")
    message: Optional[str] = Field(None, description="Optional message for the invite")
    # Agency-specific fields
    role: Optional[str] = Field(
        None, description="Role assigned to the invited user (for agency invites)"
    )
    permissions: Optional[List[str]] = Field(
        None, description="Permissions for the invited user (for agency invites)"
    )
    # Student-specific fields
    student_id: Optional[str] = Field(
        None, description="Student ID (for students invites)"
    )
    teacher_id: Optional[str] = Field(
        None, description="Teacher ID (for students invites)"
    )


class InviteResponse(BaseModel):
    """Invite response model"""

    invite_id: str = Field(..., description="Invite ID")
    email: EmailStr = Field(..., description="Email the invite was sent to")
    role: Optional[str] = Field(
        None, description="Role assigned to the invited user (for agency invites)"
    )
    agency_id: str = Field(..., description="Agency ID")
    status: InviteStatus = Field(..., description="Invite status")
    message: Optional[str] = Field(None, description="Optional message for the invite")
    token: str = Field(
        ...,
        description="Invite token (32-character alphanumeric string, e.g., 'aB3dEf9GhIjKlMnOpQrStUvWxYz1234')",
    )
    created_at: datetime = Field(..., description="When invite was created")
    expires_at: datetime = Field(..., description="When invite expires")
    accepted_at: Optional[datetime] = Field(
        None, description="When invite was accepted"
    )


class AcceptInviteRequest(BaseModel):
    """Accept invite request model"""

    token: str = Field(..., description="Invite token")
    user_id: Optional[str] = Field(None, description="User ID (if creating new users)")


class AcceptInviteResponse(BaseModel):
    """Accept invite response model"""

    success: bool = Field(..., description="Whether invite was accepted successfully")
    message: str = Field(..., description="Response message")
    user_id: Optional[str] = Field(
        None, description="User ID (if new users was created)"
    )
    invite_type: InviteType = Field(..., description="Type of invite that was accepted")
    # Agency-specific fields
    agency_id: Optional[str] = Field(
        None, description="Agency ID (for agencies invites)"
    )
    role: Optional[str] = Field(
        None, description="Role assigned to the user (for agencies invites)"
    )
    # Student-specific fields
    student_id: Optional[str] = Field(
        None, description="Student ID (for students invites)"
    )
