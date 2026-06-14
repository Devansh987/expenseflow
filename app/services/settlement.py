"""
Settlement service handling the business logic for recording debt repayments.
"""

import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.settlement import SettlementCreate


async def create_settlement(db: AsyncSession, group_id: uuid.UUID, settlement_in: SettlementCreate) -> Settlement:
    """Record a debt repayment between two users in a group."""
    
    if settlement_in.payer_id == settlement_in.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payer and receiver cannot be the same person."
        )

    db_settlement = Settlement(
        group_id=group_id,
        payer_id=settlement_in.payer_id,
        receiver_id=settlement_in.receiver_id,
        amount=settlement_in.amount,
        currency=settlement_in.currency,
        settlement_date=settlement_in.settlement_date,
        notes=settlement_in.notes,
    )
    db.add(db_settlement)
    await db.commit()
    
    # Reload with relations to satisfy the response model
    query = select(Settlement).options(
        selectinload(Settlement.payer),
        selectinload(Settlement.receiver)
    ).where(Settlement.id == db_settlement.id)
    
    result = await db.execute(query)
    return result.scalars().first()


async def get_group_settlements(db: AsyncSession, group_id: uuid.UUID) -> list[Settlement]:
    """List all settlements recorded within a group."""
    query = (
        select(Settlement)
        .options(
            selectinload(Settlement.payer),
            selectinload(Settlement.receiver)
        )
        .where(Settlement.group_id == group_id)
        .order_by(Settlement.settlement_date.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
