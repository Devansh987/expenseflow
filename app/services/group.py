"""
Group service handling business logic for groups and dynamic membership tracking.
"""

import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.group import Group
from app.models.membership import Membership
from app.models.user import User
from app.schemas.group import GroupCreate


async def create_group(db: AsyncSession, group_in: GroupCreate, creator: User) -> Group:
    """
    Create a new group. The creator is automatically added as the first active member.
    """
    db_group = Group(
        name=group_in.name,
        created_by=creator.id,
    )
    db.add(db_group)
    await db.flush()  # Flush to get the generated group ID

    # Automatically make the creator a member
    initial_membership = Membership(
        user_id=creator.id,
        group_id=db_group.id,
    )
    db.add(initial_membership)
    
    await db.commit()
    await db.refresh(db_group)
    return db_group


async def get_user_groups(db: AsyncSession, user_id: uuid.UUID) -> list[Group]:
    """Get all groups the user is currently an active member of."""
    query = (
        select(Group)
        .join(Membership)
        .where(
            (Membership.user_id == user_id) & 
            (Membership.left_at.is_(None))
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_group_details(db: AsyncSession, group_id: uuid.UUID) -> Group | None:
    """Get group with all its memberships (historical and active) eagerly loaded."""
    query = (
        select(Group)
        .options(
            selectinload(Group.memberships).selectinload(Membership.user)
        )
        .where(Group.id == group_id)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def is_active_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if a user is currently an active member of a group."""
    query = select(Membership).where(
        (Membership.group_id == group_id) &
        (Membership.user_id == user_id) &
        (Membership.left_at.is_(None))
    )
    result = await db.execute(query)
    return result.scalars().first() is not None


async def add_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, added_by: User) -> Membership:
    """
    Add a user to a group. Requires the requester (added_by) to be an active member.
    """
    # 1. Verify group exists
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # 2. Verify requester is an active member
    if not await is_active_member(db, group_id, added_by.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You must be an active member to add others"
        )
        
    # 3. Verify target user exists
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 4. Check if already an active member
    if await is_active_member(db, group_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User is already an active member of this group"
        )

    # 5. Create new membership record (dynamic tracking)
    new_membership = Membership(
        user_id=user_id,
        group_id=group_id,
    )
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership)
    return new_membership


async def remove_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, requested_by: User) -> None:
    """
    Remove a member from a group by setting left_at (Dynamic Membership Tracking).
    A user can leave themselves, or be removed by an active member.
    """
    # 1. Permission check
    if requested_by.id != user_id and not await is_active_member(db, group_id, requested_by.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You don't have permission to remove members from this group"
        )

    # 2. Find active membership
    query = select(Membership).where(
        (Membership.group_id == group_id) &
        (Membership.user_id == user_id) &
        (Membership.left_at.is_(None))
    )
    result = await db.execute(query)
    membership = result.scalars().first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User is not currently an active member of this group"
        )

    # 3. Terminate membership (don't delete the record!)
    membership.left_at = datetime.now(timezone.utc)
    await db.commit()
