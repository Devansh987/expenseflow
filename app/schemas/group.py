"""
Pydantic schemas for Group and Membership representation.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


# ─── Membership Schemas ──────────────────────────────────────────────

class MembershipBase(BaseModel):
    user_id: uuid.UUID
    group_id: uuid.UUID


class MembershipResponse(MembershipBase):
    """Schema for membership details, including join/leave history."""
    id: uuid.UUID
    joined_at: datetime
    left_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MembershipWithUserResponse(MembershipResponse):
    """Includes full user details for the member."""
    user: UserResponse


# ─── Group Schemas ───────────────────────────────────────────────────

class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    """Schema for creating a new group."""
    pass


class GroupResponse(GroupBase):
    """Basic group details."""
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupDetailResponse(GroupResponse):
    """Detailed group view including active/historical members."""
    memberships: list[MembershipWithUserResponse]
