"""
Expense service handling business logic for expense creation and split calculation.
"""

import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.membership import Membership
from app.models.enums import SplitType
from app.schemas.expense import ExpenseCreate


async def _verify_active_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, expense_date) -> bool:
    """
    Check if a user was an active member of the group on the expense_date.
    A user is active if joined_at <= expense_date and (left_at is NULL or left_at >= expense_date).
    """
    # Convert expense_date to a timezone-aware datetime at midnight for comparison
    exp_dt = datetime.combine(expense_date, datetime.min.time(), tzinfo=timezone.utc)
    
    query = select(Membership).where(
        (Membership.group_id == group_id) &
        (Membership.user_id == user_id) &
        (Membership.joined_at <= exp_dt) &
        ((Membership.left_at.is_(None)) | (Membership.left_at >= exp_dt))
    )
    result = await db.execute(query)
    return result.scalars().first() is not None


def _calculate_share_amounts(expense_amount: float, splits: list, split_type: SplitType) -> list[float]:
    """
    Calculate the exact monetary share for each split.
    Uses Decimal to avoid floating point precision issues and ensures the sum 
    matches the total expense amount exactly.
    """
    total = Decimal(str(expense_amount))
    amounts = []
    
    if split_type == SplitType.EQUAL:
        num_participants = len(splits)
        # Calculate base share and remainder
        # e.g. 100 / 3 = 33.33 with 0.01 left over
        base_share = (total / Decimal(num_participants)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        amounts = [base_share] * num_participants
        
        # Adjust the first person's share with the penny difference to ensure exact sum
        difference = total - sum(amounts)
        amounts[0] += difference

    elif split_type == SplitType.PERCENTAGE:
        for split in splits:
            pct = Decimal(str(split.share_percentage)) / Decimal('100')
            amt = (total * pct).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            amounts.append(amt)
            
        # Adjust for rounding errors
        difference = total - sum(amounts)
        amounts[0] += difference

    elif split_type == SplitType.SHARES:
        total_shares = Decimal(str(sum(s.share_ratio for s in splits)))
        if total_shares == 0:
            raise ValueError("Total shares cannot be zero")
            
        for split in splits:
            ratio = Decimal(str(split.share_ratio))
            amt = (total * (ratio / total_shares)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            amounts.append(amt)
            
        difference = total - sum(amounts)
        amounts[0] += difference

    return [float(a) for a in amounts]


async def create_expense(db: AsyncSession, group_id: uuid.UUID, expense_in: ExpenseCreate) -> Expense:
    """
    Create a new expense and calculate split amounts based on the split type.
    Enforces membership validation at the time of the expense.
    """
    # 1. Validate payer membership at expense_date
    if not await _verify_active_member(db, group_id, expense_in.payer_id, expense_in.expense_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Payer must be an active member on the expense date."
        )

    # 2. Validate all split participants membership
    for split in expense_in.splits:
        if not await _verify_active_member(db, group_id, split.user_id, expense_in.expense_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"User {split.user_id} was not an active member on the expense date."
            )

    # 3. Calculate share amounts
    try:
        share_amounts = _calculate_share_amounts(expense_in.amount, expense_in.splits, expense_in.split_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 4. Create the Expense record
    db_expense = Expense(
        group_id=group_id,
        payer_id=expense_in.payer_id,
        description=expense_in.description,
        amount=expense_in.amount,
        currency=expense_in.currency,
        original_amount=expense_in.original_amount,
        original_currency=expense_in.original_currency,
        expense_date=expense_in.expense_date,
        split_type=expense_in.split_type,
        notes=expense_in.notes,
    )
    db.add(db_expense)
    await db.flush() # Get the expense ID

    # 5. Create the ExpenseSplit records
    for split_data, share_amt in zip(expense_in.splits, share_amounts):
        db_split = ExpenseSplit(
            expense_id=db_expense.id,
            user_id=split_data.user_id,
            share_amount=share_amt,
            share_percentage=split_data.share_percentage,
            share_ratio=split_data.share_ratio,
        )
        db.add(db_split)

    await db.commit()
    # Using selectinload to eagerly load the relationships for the response
    from sqlalchemy.orm import selectinload
    query = select(Expense).options(
        selectinload(Expense.splits).selectinload(ExpenseSplit.user)
    ).where(Expense.id == db_expense.id)
    result = await db.execute(query)
    
    return result.scalars().first()
