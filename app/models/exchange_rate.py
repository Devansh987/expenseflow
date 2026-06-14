"""
ExchangeRate model — stores currency conversion rates.

Used to convert USD (or other currencies) to INR.
The effective_date allows historical lookups so that
an expense from March uses the March exchange rate,
not today's rate.

This supports Decision 3 (store both original and converted values).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import String, Numeric, Date, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    # One rate per currency per date
    __table_args__ = (
        UniqueConstraint("currency", "effective_date", name="uq_currency_date"),
    )

    # ── Primary Key ──────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Fields ───────────────────────────────────────────────────
    # ISO 4217 currency code (e.g., "USD", "EUR")
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        index=True,
    )

    # Rate relative to INR. Example: USD rate = 83.50 means 1 USD = 83.50 INR
    rate_to_inr: Mapped[float] = mapped_column(
        Numeric(12, 6),
        nullable=False,
    )

    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.currency}={self.rate_to_inr} on {self.effective_date}>"
