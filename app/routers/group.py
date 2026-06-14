"""
Group router exposing endpoints for creating groups and managing memberships.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse, GroupDetailResponse, MembershipResponse
from app.services import group as group_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_in: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new group. You are automatically added as the first member."""
    return await group_service.create_group(db, group_in, current_user)


@router.get("", response_model=list[GroupResponse])
async def list_my_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all groups you are currently an active member of."""
    return await group_service.get_user_groups(db, current_user.id)


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a group, including all past and present members."""
    # Note: Depending on privacy rules, we might want to ensure the user is an active/past member
    # before returning details. We'll allow it for now if they have the ID.
    group = await group_service.get_group_details(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.post("/{group_id}/members/{user_id}", response_model=MembershipResponse)
async def add_member_to_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a user to a group. You must be an active member to do this."""
    return await group_service.add_member(db, group_id, user_id, current_user)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a user from a group.
    This does not delete their record. It marks their 'left_at' timestamp
    so historical balances remain accurate.
    """
    await group_service.remove_member(db, group_id, user_id, current_user)
    return None
