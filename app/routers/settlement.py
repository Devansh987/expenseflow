"""
Settlement router for API endpoints.
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.settlement import SettlementCreate, SettlementResponse
from app.services import settlement as settlement_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Settlements"])


@router.post("/{group_id}/settlements", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def record_settlement(
    group_id: uuid.UUID,
    settlement_in: SettlementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a debt repayment (settlement) between two users.
    This effectively alters their net balance in the group.
    """
    return await settlement_service.create_settlement(db, group_id, settlement_in)


@router.get("/{group_id}/settlements", response_model=list[SettlementResponse])
async def list_settlements(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all settlements recorded in a specific group."""
    return await settlement_service.get_group_settlements(db, group_id)
