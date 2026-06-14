"""
Pydantic schemas for recording and viewing debt settlements.
"""

import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.user import UserResponse


class SettlementBase(BaseModel):
    receiver_id: uuid.UUID
    amount: float = Field(gt=0, description="Amount paid to settle debt")
    currency: str = "INR"
    settlement_date: date
    notes: Optional[str] = None


class SettlementCreate(SettlementBase):
    """Schema for recording a new settlement."""
    payer_id: uuid.UUID


class SettlementResponse(SettlementBase):
    """Schema for viewing a settlement record."""
    id: uuid.UUID
    group_id: uuid.UUID
    payer_id: uuid.UUID
    created_at: datetime
    
    # Eagerly loaded user details for frontend display
    payer: UserResponse
    receiver: UserResponse

    model_config = ConfigDict(from_attributes=True)
