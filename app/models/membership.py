"""
Membership model — tracks when users join and leave groups.

This is the key model for dynamic membership (Decision 1 in DECISIONS.md).
A NULL `left_at` means the member is still active.
An expense should only include members whose membership period
covers the expense date.

Relationships:
    Membership N──▶ 1 User
    Membership N──▶ 1 Group

Unique constraint: (user_id, group_id, joined_at) prevents the same user
from having duplicate active membership records.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Membership(Base):
    __tablename__ = "memberships"

    # Composite uniqueness: a user can rejoin a group, but not twice at the same instant
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", "joined_at", name="uq_membership"),
    )

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # NULL = still active member; set to a date when the user leaves.
    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # ── Relationships ────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        back_populates="memberships",
    )

    group: Mapped["Group"] = relationship(
        back_populates="memberships",
    )

    def __repr__(self) -> str:
        status = "active" if self.left_at is None else f"left {self.left_at}"
        return f"<Membership user={self.user_id} group={self.group_id} {status}>"
