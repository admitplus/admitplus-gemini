from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class EssayConfig(BaseModel):
    tone: Optional[str] = None
    voice: Optional[str] = None
    length_words: Optional[int] = None
    highlight_ids: List[str] = []


class EssayCreateRequest(BaseModel):
    student_id: str
    essay_type: str
    prompt_text: str
    config: Optional[EssayConfig] = None


class EssayUpdateRequest(BaseModel):
    essay_type: Optional[str] = None
    prompt_text: Optional[str] = None
    config: Optional[EssayConfig] = None
    status: Optional[str] = None
    final_draft_id: Optional[str] = None


class EssayDetailResponse(BaseModel):
    essay_id: str
    student_id: str
    application_id: str
    essay_type: str
    prompt_text: str
    config: EssayConfig
    status: str
    final_draft_id: Optional[str] = None
    created_by_member_id: Optional[str] = None
    university_logo: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EssayListResponse(BaseModel):
    items: List[EssayDetailResponse]


class EssayFinalizeRequest(BaseModel):
    final_draft_id: str


class EssayGenerateRequest(BaseModel):
    pass


class EssayRecordListResponse(BaseModel):
    pass


class EssayRecordDetailResponse(BaseModel):
    pass


class EssayChatRequest(BaseModel):
    pass


class EssayChatResponse(BaseModel):
    pass


class EssayMessageListResponse(BaseModel):
    pass


class GenerateEssayQuestionRequest(BaseModel):
    university_name: str
    degree: str
    title: str
    description: str


class EssayQuestionUpdateRequest(BaseModel):
    question: str


class EssayQuestionResponse(BaseModel):
    question_id: str
    student_id: str
    essay_id: str
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime


class EssayQuestionListResponse(BaseModel):
    items: List[EssayQuestionResponse]
