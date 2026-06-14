"""
User model — stores registered users.

Relationships:
    User 1──▶ N Membership   (groups the user belongs to)
    User 1──▶ N Expense      (expenses the user paid for)
    User 1──▶ N ExpenseSplit  (the user's share of expenses)
    User 1──▶ N Settlement    (settlements as payer or receiver)
    User 1──▶ N Group         (groups created by the user)
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    # ── Primary Key ──────────────────────────────────────────────
    # UUID avoids sequential ID guessing and is safe for public APIs.
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Fields ───────────────────────────────────────────────────
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Stores bcrypt hash, never the plaintext password.
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # server_default=func.now() ensures the DB sets this even for raw SQL inserts.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────
    # 'back_populates' creates an explicit two-way link.
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    created_groups: Mapped[list["Group"]] = relationship(
        back_populates="creator",
        lazy="selectin",
    )

    expenses_paid: Mapped[list["Expense"]] = relationship(
        back_populates="payer",
        lazy="selectin",
    )

    expense_splits: Mapped[list["ExpenseSplit"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    # Settlements where this user paid someone
    settlements_made: Mapped[list["Settlement"]] = relationship(
        back_populates="payer",
        foreign_keys="Settlement.payer_id",
        lazy="selectin",
    )

    # Settlements where this user received money
    settlements_received: Mapped[list["Settlement"]] = relationship(
        back_populates="receiver",
        foreign_keys="Settlement.receiver_id",
        lazy="selectin",
    )

    import_sessions: Mapped[list["ImportSession"]] = relationship(
        back_populates="uploader",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
