"""
Expense router for creating and listing group expenses.
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.services import expense as expense_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Expenses"])


@router.post("/{group_id}/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    group_id: uuid.UUID,
    expense_in: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new expense in a group.
    The split amounts will be automatically calculated based on the split_type.
    """
    # Note: In a full app we'd verify current_user has access to this group
    return await expense_service.create_expense(db, group_id, expense_in)


@router.get("/{group_id}/expenses", response_model=list[ExpenseResponse])
async def list_group_expenses(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all expenses for a specific group."""
    query = (
        select(Expense)
        .options(
            selectinload(Expense.splits).selectinload(ExpenseSplit.user)
        )
        .where(Expense.group_id == group_id)
        .order_by(Expense.expense_date.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
