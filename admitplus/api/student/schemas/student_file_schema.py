from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from admitplus.api.files.file_schema import FileType, FileParseStatus


class StudentFileAttachRequest(BaseModel):
    file_id: str = Field(..., description="File ID from files_storage collection")
    file_type: FileType = Field(..., description="Type of file")


class StudentFileResponse(BaseModel):
    file_id: str = Field(..., description="File ID")
    student_id: str = Field(..., description="Student ID")
    uploader_member_id: str = Field(..., description="Member ID who uploaded the file")
    file_type: FileType = Field(..., description="Type of file")
    original_filename: str = Field(..., description="Original file name")
    storage_path: str = Field(..., description="GCS storage path")
    mime_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    parse_status: FileParseStatus = Field(
        default=FileParseStatus.pending, description="Parse status"
    )
    parsed_text: Optional[str] = Field(None, description="Parsed text content")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StudentFileListResponse(BaseModel):
    file_list: List[StudentFileResponse] = Field(
        ..., description="List of student files"
    )
    total: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
