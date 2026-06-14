"""
Pydantic schemas for User authentication and representation.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


# ─── Base ────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    username: str
    email: EmailStr


# ─── Requests ────────────────────────────────────────────────────────
class UserCreate(UserBase):
    """Schema for user registration."""
    password: str


class UserLogin(BaseModel):
    """Schema for JSON login. (Alternatively, OAuth2 password form can be used)"""
    email: EmailStr
    password: str


# ─── Responses ───────────────────────────────────────────────────────
class UserResponse(UserBase):
    """Schema for returning user data (password excluded)."""
    id: uuid.UUID
    created_at: datetime

    # This tells Pydantic to read data even if it's an ORM model
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for returning the JWT token."""
    access_token: str
    token_type: str = "bearer"
