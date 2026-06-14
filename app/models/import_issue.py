"""
ImportIssue model — stores individual anomalies found during CSV import.

Each issue maps to one of the AN-001 through AN-012 anomaly codes
defined in Scope.md. Issues are linked to a specific row number
so the user can locate the problem in their CSV file.

Relationships:
    ImportIssue N──▶ 1 ImportSession
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import IssueType, IssueStatus


class ImportIssue(Base):
    __tablename__ = "import_issues"

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    import_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────
    # The CSV row number where this issue was found (1-indexed)
    row_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Anomaly category (AN-001 to AN-012)
    issue_type: Mapped[IssueType] = mapped_column(
        Enum(IssueType),
        nullable=False,
    )

    # Human-readable description of the problem
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # What the system suggests the user do about it
    suggested_action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Current resolution status
    status: Mapped[IssueStatus] = mapped_column(
        Enum(IssueStatus),
        nullable=False,
        default=IssueStatus.PENDING,
    )

    # Raw data from the CSV row for reference/debugging.
    # Stored as JSON so we don't need to know the CSV schema at model level.
    raw_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    # The original value before any auto-fix (e.g., ₹899.995 before rounding)
    original_value: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────
    import_session: Mapped["ImportSession"] = relationship(
        back_populates="issues",
    )

    def __repr__(self) -> str:
        return f"<ImportIssue row={self.row_number} type={self.issue_type.value}>"
