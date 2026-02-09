from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class FileType(str, Enum):
    """
    File type enumeration
    """

    resume = "resume"  # Resume
    transcript = "transcript"  # Transcript
    personal_statement = "personal_statement"  # Personal Statement
    recommendation = "recommendation"  # Recommendation Letter
    language_test = "language_test"  # Language Test Score
    degree_certificate = "degree_certificate"  # Degree Certificate
    portfolio = "portfolio"  # Portfolio
    passport = "passport"  # Passport
    avatar = "avatar"  # Avatar
    other = "other"  # Other Materials


class FileParseStatus(str, Enum):
    """
    File parsing status
    """

    pending = "pending"
    parsing = "parsing"
    parsed = "parsed"
    failed = "failed"


class FileStatus(str, Enum):
    """
    File status enumeration
    """

    active = "active"
    deleted = "deleted"


class FileMetadata(BaseModel):
    """
    File metadata model
    """

    file_id: str
    file_name: str
    content_type: str
    size: int
    file_type: FileType
    student_id: Optional[str] = None
    description: Optional[str] = Field(None, description="File description")
    status: FileStatus = Field(..., description="File status")
    created_at: datetime
    uploaded_by: str
    storage_path: str = Field(..., description="GCS storage path")
    file_url: str = Field(..., description="Public access URL")


class FileUploadResponse(BaseModel):
    """
    File upload response model - matches API spec for bare file uploads
    """

    file_id: str = Field(..., description="File ID")
    storage_path: str = Field(..., description="GCS storage path")
    original_filename: str = Field(..., description="Original file name")
    mime_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")


class FileMetadataResponse(FileMetadata):
    """
    File metadata response model
    Inherits from FileMetadata, can be extended with metadata-specific fields if needed
    """

    pass


class FileStorageInfoResponse(BaseModel):
    """
    File storage info response model - matches API spec for file metadata retrieval
    """

    file_id: str = Field(..., description="File ID")
    storage_path: str = Field(..., description="GCS storage path")
    bucket: str = Field(..., description="GCS bucket name")
    mime_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    status: FileStatus = Field(..., description="File status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class FileListRequest(BaseModel):
    """
    File list request model
    """

    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    student_id: Optional[str] = None  # 过滤条件，可选


class FileListResponse(BaseModel):
    """
    File list response model
    """

    files: List[FileMetadata] = Field(..., description="File list")
    total: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there is a next page")


class FileAnalyzeRequest(BaseModel):
    """
    File analysis request model
    """

    mode: Optional[str] = Field(
        default="standard", description="Analysis mode: standard, detailed, etc."
    )


class FileAnalyzeResultResponse(BaseModel):
    """
    File analysis result response model
    """

    file_id: str = Field(..., description="File ID")
    parse_status: FileParseStatus = Field(..., description="Parse status")
    extracted_text_length: int = Field(..., description="Length of extracted text")
    new_highlights_created: int = Field(..., description="Number of highlights created")
    student_profile: Optional[Dict[str, Any]] = Field(
        None, description="Updated student profile information"
    )
    highlights: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of created highlights"
    )
