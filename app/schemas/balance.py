"""
Pydantic schemas for balance summaries and debt resolution.
"""

import uuid
from pydantic import BaseModel

from app.schemas.user import UserResponse


class UserBalanceSummary(BaseModel):
    """A user's net balance within a specific group or overall."""
    user: UserResponse
    net_balance: float
    # If net_balance > 0, the user is owed money.
    # If net_balance < 0, the user owes money.


class Debt(BaseModel):
    """Represents a simplified debt from one user to another."""
    from_user: UserResponse
    to_user: UserResponse
    amount: float


class GroupBalanceReport(BaseModel):
    """Complete balance report for a group."""
    group_id: uuid.UUID
    balances: list[UserBalanceSummary]
    suggested_settlements: list[Debt]
