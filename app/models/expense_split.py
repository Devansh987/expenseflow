"""
ExpenseSplit model — stores how an expense is divided among participants.

Each row represents one participant's share of a single expense.
The interpretation depends on the parent Expense's split_type:

    EQUAL:      share_amount = expense.amount / num_splits
    PERCENTAGE: share_percentage is set (must sum to 100), share_amount is computed
    SHARES:     share_ratio is set (e.g., 2:1:1), share_amount is computed

Relationships:
    ExpenseSplit N──▶ 1 Expense
    ExpenseSplit N──▶ 1 User
"""

import uuid

from sqlalchemy import Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    expense_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────
    # The computed amount this user owes for this expense.
    # Always populated regardless of split_type.
    share_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    # Used only when split_type = PERCENTAGE.
    # Example: 33.33 means this user pays 33.33% of the total.
    share_percentage: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Used only when split_type = SHARES.
    # Example: in a 2:1:1 split, ratios are 2, 1, 1.
    share_ratio: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    expense: Mapped["Expense"] = relationship(
        back_populates="splits",
    )

    user: Mapped["User"] = relationship(
        back_populates="expense_splits",
    )

    def __repr__(self) -> str:
        return f"<ExpenseSplit user={self.user_id} amount={self.share_amount}>"
