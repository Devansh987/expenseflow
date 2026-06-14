"""
Expense model — stores shared expenses within a group.

Relationships:
    Expense N──▶ 1 Group      (which group this expense belongs to)
    Expense N──▶ 1 User       (who paid — the payer)
    Expense 1──▶ N ExpenseSplit (how the expense is divided)

The split_type field determines how ExpenseSplit records are interpreted:
    - EQUAL: share_amount = total / num_participants
    - PERCENTAGE: share_percentage is used, share_amount is computed
    - SHARES: share_ratio is used, share_amount is computed

original_amount / original_currency preserve the raw imported value
when currency conversion is applied (Decision 3 in DECISIONS.md).
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    String, Numeric, Date, DateTime, Text,
    ForeignKey, Enum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SplitType


class Expense(Base):
    __tablename__ = "expenses"

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"),
        nullable=False,
    )

    # The user who paid for this expense
    payer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Numeric(12, 2) supports values up to 9,999,999,999.99
    # This is the amount in the base currency (INR)
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    # Original values preserved for audit trail (Decision 3)
    original_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 4),  # 4 decimal places to capture pre-rounding values
        nullable=True,
    )

    original_currency: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
    )

    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Enum stored as a PostgreSQL enum type
    split_type: Mapped[SplitType] = mapped_column(
        Enum(SplitType),
        nullable=False,
        default=SplitType.EQUAL,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────
    group: Mapped["Group"] = relationship(
        back_populates="expenses",
    )

    payer: Mapped["User"] = relationship(
        back_populates="expenses_paid",
    )

    splits: Mapped[list["ExpenseSplit"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",  # Deleting an expense removes its splits
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Expense {self.description} ₹{self.amount}>"
