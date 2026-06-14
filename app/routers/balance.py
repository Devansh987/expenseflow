"""
Balance router for fetching group and individual balances.
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.balance import GroupBalanceReport
from app.services import balance as balance_service
from app.utils.dependencies import get_current_user

router = APIRouter(tags=["Balances"])


@router.get("/groups/{group_id}/balances", response_model=GroupBalanceReport)
async def get_group_balances(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete balance report for a group, 
    including net balances for each user and suggested debt settlements.
    """
    return await balance_service.get_group_balances(db, group_id)


@router.get("/users/me/balance")
async def get_my_overall_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get your overall net balance across all groups."""
    return await balance_service.get_user_overall_balance(db, current_user.id)
