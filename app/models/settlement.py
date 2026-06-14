"""
Settlement model — records debt repayments between group members.

A settlement reduces the balance between two users.
Example: "Rohan paid Aisha back ₹500"

Relationships:
    Settlement N──▶ 1 Group   (which group this settlement belongs to)
    Settlement N──▶ 1 User    (payer — the person who pays)
    Settlement N──▶ 1 User    (receiver — the person who gets paid)
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Numeric, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Settlement(Base):
    __tablename__ = "settlements"

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

    # The person paying back the debt
    payer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # The person receiving the payment
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    settlement_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
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
        back_populates="settlements",
    )

    payer: Mapped["User"] = relationship(
        back_populates="settlements_made",
        foreign_keys=[payer_id],
    )

    receiver: Mapped["User"] = relationship(
        back_populates="settlements_received",
        foreign_keys=[receiver_id],
    )

    def __repr__(self) -> str:
        return f"<Settlement {self.payer_id} → {self.receiver_id} ₹{self.amount}>"
