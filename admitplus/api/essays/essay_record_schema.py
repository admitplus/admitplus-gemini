from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EssayGenerateRequest(BaseModel):
    base_draft_id: Optional[str] = None
    instructions: Optional[str] = None


class EssayRecordDetailResponse(BaseModel):
    record_id: str
    essay_id: str
    draft_id: str
    action: str
    request_payload: Dict[str, Any]
    response_payload: Dict[str, Any]
    created_by_member_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EssayRecordListResponse(BaseModel):
    items: List[EssayRecordDetailResponse]
