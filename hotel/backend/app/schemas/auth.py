"""
Auth endpoint'leri için Pydantic schemas.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "superadmin@hotelops.com"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "StrongPass123"})


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str
