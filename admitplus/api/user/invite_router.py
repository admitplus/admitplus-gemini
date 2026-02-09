from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from admitplus.common.response_schema import Response
from .user_service import UserService
from .invite_service import InviteService


user_service = UserService()
invite_service = InviteService()

router = APIRouter(prefix="", tags=["Users"])


@router.get("/invites/{token}", response_model=Response[dict])
async def redirect_invites(
    token: str,
    request: Request,
):
    invite = await invite_service.invite_repo.find_invite_by_token(token)
    if not invite or invite["status"] != "pending":
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite["expires_at"] < datetime.now():
        raise HTTPException(status_code=403, detail="Invite expired")

    query_string = urlencode(
        {
            "invite_id": invite["invite_id"],
            "email": invite["email"],
            "role": invite["role"],
            "agency_id": invite["agency_id"],
            "invite_type": invite["invite_type"],
        }
    )
    base_url = str(request.base_url).rstrip("/")
    redirect_url = f"{base_url}/login?{query_string}"
    return RedirectResponse(url=redirect_url, status_code=302)
