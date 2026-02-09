from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


UsageType = Literal["resume", "sop", "lor", "optional", "writing_sample"]


class ApplicationDocumentCreateRequest(BaseModel):
    file_id: str = Field(..., min_length=1, description="File ID")
    usage: UsageType = Field(..., description="Document usage type")
    note: Optional[str] = Field(None, description="Optional note")


class ApplicationDocumentResponse(BaseModel):
    app_doc_id: str
    application_id: str
    file_id: str
    usage: str
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ApplicationDocumentListResponse(BaseModel):
    items: List[ApplicationDocumentResponse]
