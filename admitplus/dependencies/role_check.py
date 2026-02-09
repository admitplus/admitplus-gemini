from typing import List, Optional
from enum import Enum
import json
from datetime import datetime
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel
import jwt

from admitplus.config import settings
from admitplus.database.redis import BaseRedisCRUD
from admitplus.utils.jwt_utils import decode_token


async def get_current_user(
    request: Request,
):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = token.split("Bearer ")[1]
    data = await BaseRedisCRUD().get(f"token:{token}")
    if not data:
        raise HTTPException(status_code=401, detail="Token expired or is invalid")
    return json.loads(data)


async def get_current_token(
    request: Request,
):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = token.split("Bearer ")[1]
    data = await BaseRedisCRUD().get(f"token:{token}")
    if not data:
        raise HTTPException(status_code=401, detail="Token expired or is invalid")
    return token


async def guest_rate_limit(user=Depends(get_current_user)):
    if user["role"] != settings.USER_ROLE_GUEST:
        return user

    redis_repo = BaseRedisCRUD()
    key = f"guest_limit:{user['user_id']}"
    count = await redis_repo.get(key)
    if count is None:
        await redis_repo.set(key, "1", expire=86400)
    elif int(count) >= 3:
        raise HTTPException(status_code=429, detail="Daily guest usage limit exceeded")
    else:
        await redis_repo.increment(key)
    return user


class CurrentUser(BaseModel):
    user_id: str
    email: str
    role: str
    exp: Optional[datetime] = None


class Role(str, Enum):
    ADMIN = settings.USER_ROLE_ADMIN
    AGENCY_ADMIN = settings.USER_ROLE_AGENCY_ADMIN
    AGENCY_MEMBER = settings.USER_ROLE_AGENCY_MEMBER
    COUNSELORS = settings.USER_ROLE_COUNSELORS
    TEACHER = settings.USER_ROLE_TEACHER
    STUDENT = settings.USER_ROLE_STUDENT


class RoleChecker:
    def __init__(self, *, role: List[Role]):
        self.role = role

    async def __call__(self, request: Request) -> CurrentUser:
        _current_user = await get_current_user(request)
        if _current_user["role"] not in [role.value.lower() for role in self.role]:
            raise HTTPException(
                status_code=403,
                detail=f"{', '.join([role.value for role in self.role])} role required",
            )
        return CurrentUser(**_current_user)
