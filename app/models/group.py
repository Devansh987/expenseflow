"""
Group model — stores expense-sharing groups.

Relationships:
    Group N──▶ 1 User         (creator)
    Group 1──▶ N Membership   (members with join/leave history)
    Group 1──▶ N Expense      (expenses recorded in this group)
    Group 1──▶ N Settlement   (settlements within this group)
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Fields ───────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Foreign key to the user who created this group.
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────
    creator: Mapped["User"] = relationship(
        back_populates="created_groups",
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="group",
        lazy="selectin",
    )

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="group",
        lazy="selectin",
    )

    settlements: Mapped[list["Settlement"]] = relationship(
        back_populates="group",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Group {self.name}>"
