from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class EssayDraftCreateRequest(BaseModel):
    text: str
    generated_by: str  # llm / teacher / student
    model: Optional[str] = None


class EssayDraftResponse(BaseModel):
    draft_id: str
    essay_id: str
    version: int  # 自动增加
    text: str
    generated_by: str
    model: Optional[str] = None
    author_member_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EssayDraftListResponse(BaseModel):
    items: List[EssayDraftResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
