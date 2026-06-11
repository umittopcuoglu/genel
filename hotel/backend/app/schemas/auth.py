"""
Auth endpoint'leri için Pydantic schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="superadmin@hotelops.com")
    password: str = Field(..., min_length=6, example="StrongPass123")


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True


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
