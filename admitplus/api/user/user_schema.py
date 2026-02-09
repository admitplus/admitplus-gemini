from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum


class Membership(BaseModel):
    """User membership in an agency or organization"""

    role: str = Field(..., description="User role (e.g., student, admin, etc.)")
    status: str = Field(..., description="Membership status (e.g., active, inactive)")
    agency_id: str = Field(..., description="Agency ID for this membership")


class UserProfile(BaseModel):
    """User profile for settings/account management"""

    user_id: str = Field(..., description="User ID")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    status: str = Field(
        "active", description="User account status (e.g., active, inactive)"
    )
    is_verified: bool = Field(False, description="Whether user email is verified")
    memberships: List[Membership] = Field(
        default_factory=list, description="List of user memberships"
    )
    created_at: Optional[datetime] = Field(
        None, description="Account creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class UserUpdateRequest(BaseModel):
    """Request model for updating users information"""

    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")


class PasswordUpdateRequest(BaseModel):
    """Request model for updating users password"""

    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password (8-128 characters)"
    )
    confirm_password: str = Field(..., description="Confirm new password")


class PasswordUpdateResponse(BaseModel):
    """Response model for password update"""

    success: bool = Field(..., description="Whether password was updated successfully")
    message: str = Field(..., description="Response message")
    updated_at: datetime = Field(..., description="When password was updated")


# ==================== Account Settings Schemas ====================


class NotificationSettings(BaseModel):
    """Notification settings model"""

    email_notifications: bool = Field(True, description="Enable email notifications")
    push_notifications: bool = Field(True, description="Enable push notifications")
    sms_notifications: bool = Field(False, description="Enable SMS notifications")
    marketing_emails: bool = Field(False, description="Enable marketing emails")
    security_alerts: bool = Field(True, description="Enable security alerts")
    application_updates: bool = Field(True, description="Enable applications updates")


class PrivacySettings(BaseModel):
    """Privacy settings model"""

    profile_visibility: str = Field(
        "private", description="Profile visibility (public/private)"
    )
    show_email: bool = Field(False, description="Show email in profile")
    show_phone: bool = Field(False, description="Show phone in profile")
    data_sharing: bool = Field(False, description="Allow data sharing with partners")
    analytics_tracking: bool = Field(True, description="Allow analytics tracking")


class UserSettings(BaseModel):
    """User settings model"""

    language: str = Field("en", description="Preferred language")
    timezone: str = Field("UTC", description="User's timezone")
    date_format: str = Field("YYYY-MM-DD", description="Preferred date format")
    theme: str = Field("light", description="UI theme preference")
    notifications: NotificationSettings = Field(
        default_factory=NotificationSettings, description="Notification settings"
    )
    privacy: PrivacySettings = Field(
        default_factory=PrivacySettings, description="Privacy settings"
    )


class UserSettingsUpdateRequest(BaseModel):
    """Request model for updating users settings"""

    language: Optional[str] = Field(None, description="Preferred language")
    timezone: Optional[str] = Field(None, description="User's timezone")
    date_format: Optional[str] = Field(None, description="Preferred date format")
    theme: Optional[str] = Field(None, description="UI theme preference")
    notifications: Optional[NotificationSettings] = Field(
        None, description="Notification settings"
    )
    privacy: Optional[PrivacySettings] = Field(None, description="Privacy settings")


class SecurityInfo(BaseModel):
    """Security information model"""

    two_factor_enabled: bool = Field(
        False, description="Whether two-factor authentication is enabled"
    )
    last_password_change: Optional[datetime] = Field(
        None, description="Last password change date"
    )
    last_login: Optional[datetime] = Field(None, description="Last login date")
    login_attempts: int = Field(0, description="Number of failed login attempts")
    account_locked: bool = Field(False, description="Whether account is locked")
    email_verified: bool = Field(False, description="Whether email is verified")
    phone_verified: bool = Field(False, description="Whether phone is verified")
    trusted_devices: int = Field(0, description="Number of trusted devices")
