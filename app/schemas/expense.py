"""
Pydantic schemas for Expense and ExpenseSplit representation.
"""

import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import SplitType
from app.schemas.user import UserResponse


# ─── Expense Split Schemas ───────────────────────────────────────────

class ExpenseSplitBase(BaseModel):
    user_id: uuid.UUID
    
    # Used only for PERCENTAGE
    share_percentage: Optional[float] = Field(None, ge=0, le=100)
    
    # Used only for SHARES
    share_ratio: Optional[float] = Field(None, ge=0)


class ExpenseSplitCreate(ExpenseSplitBase):
    pass


class ExpenseSplitResponse(ExpenseSplitBase):
    id: uuid.UUID
    share_amount: float
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)


# ─── Expense Schemas ─────────────────────────────────────────────────

class ExpenseBase(BaseModel):
    description: str
    amount: float = Field(gt=0, description="The total amount of the expense")
    currency: str = "INR"
    expense_date: date
    split_type: SplitType
    notes: Optional[str] = None
    
    # Fields to preserve pre-conversion values (Decision 3)
    original_amount: Optional[float] = None
    original_currency: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    payer_id: uuid.UUID
    splits: list[ExpenseSplitCreate]

    @model_validator(mode='after')
    def validate_splits(self) -> 'ExpenseCreate':
        if self.split_type == SplitType.PERCENTAGE:
            total_percentage = sum(s.share_percentage or 0 for s in self.splits)
            # Use a small tolerance for floating point errors
            if abs(total_percentage - 100.0) > 0.01:
                raise ValueError(f"Percentages must sum to 100, got {total_percentage}")
            for split in self.splits:
                if split.share_percentage is None:
                    raise ValueError("share_percentage is required for PERCENTAGE split")
                    
        elif self.split_type == SplitType.SHARES:
            for split in self.splits:
                if split.share_ratio is None:
                    raise ValueError("share_ratio is required for SHARES split")
        
        return self


class ExpenseResponse(ExpenseBase):
    id: uuid.UUID
    group_id: uuid.UUID
    payer_id: uuid.UUID
    created_at: datetime
    splits: list[ExpenseSplitResponse]

    model_config = ConfigDict(from_attributes=True)
