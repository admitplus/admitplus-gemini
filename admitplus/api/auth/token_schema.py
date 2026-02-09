from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The access token string")
    token_type: str = Field("bearer", description="The token type, always 'bearer'")
    expires_in: int = Field(3600, description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token for token renewal"
    )


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., description="The new access token string")
    token_type: str = Field("bearer", description="The token type, always 'bearer'")
    expires_in: int = Field(3600, description="Token expiration time in seconds")
    refresh_token: str = Field(..., description="New refresh token for token renewal")


class RefreshRequest(BaseModel):
    refresh_token: str
