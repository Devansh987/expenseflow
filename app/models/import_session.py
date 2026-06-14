"""
ImportSession model — tracks CSV file uploads and their processing status.

Each CSV upload creates one ImportSession. As the file is parsed,
anomalies are stored as ImportIssue records linked to this session.

Relationships:
    ImportSession N──▶ 1 User         (who uploaded)
    ImportSession N──▶ 1 Group        (target group for import)
    ImportSession 1──▶ N ImportIssue  (anomalies detected)
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ImportStatus


class ImportSession(Base):
    __tablename__ = "import_sessions"

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus),
        nullable=False,
        default=ImportStatus.PENDING,
    )

    # Statistics populated after processing
    total_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    successful_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    failed_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    uploader: Mapped["User"] = relationship(
        back_populates="import_sessions",
    )

    issues: Mapped[list["ImportIssue"]] = relationship(
        back_populates="import_session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ImportSession {self.file_name} [{self.status.value}]>"
