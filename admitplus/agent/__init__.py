from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends
from admitplus.agent.service.services import AgentService
from admitplus.dependencies.role_check import get_current_user, get_current_token

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


class ChatRequest(BaseModel):
    message: str


@router.post("/process")
async def process_handler(
    msg: ChatRequest,
    user=Depends(get_current_user),
    token=Depends(get_current_token),
):
    return StreamingResponse(
        AgentService().stream_request(
            user_id=user["user_id"],
            session_id=f"adk:sessions:root_agent:{user['user_id']}:{token}",
            message=msg.message,
        ),
        media_type="text/event-stream",
    )


class ScoreRequest(BaseModel):
    question: str
    answer: str
