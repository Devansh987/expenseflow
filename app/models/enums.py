"""
Shared enums used across multiple models.

These are Python enums that SQLAlchemy maps to PostgreSQL enum types.
Defining them separately avoids circular imports and keeps models clean.
"""

import enum


class SplitType(str, enum.Enum):
    """How an expense is divided among participants."""
    EQUAL = "equal"
    PERCENTAGE = "percentage"
    SHARES = "shares"


class ImportStatus(str, enum.Enum):
    """Lifecycle status of a CSV import session."""
    PENDING = "pending"        # Upload received, not yet processed
    PROCESSING = "processing"  # Anomaly detection in progress
    COMPLETED = "completed"    # All rows processed (may have issues)
    FAILED = "failed"          # Import aborted due to critical error


class IssueStatus(str, enum.Enum):
    """Resolution status of an individual import anomaly."""
    PENDING = "pending"        # Awaiting user review
    RESOLVED = "resolved"      # User accepted the suggested fix
    REJECTED = "rejected"      # User dismissed the issue
    AUTO_FIXED = "auto_fixed"  # System applied automatic correction


class IssueType(str, enum.Enum):
    """
    Anomaly categories detected during CSV import.
    Maps directly to AN-001 through AN-012 in Scope.md.
    """
    DUPLICATE_EXPENSE = "duplicate_expense"            # AN-001
    MISSING_PAYER = "missing_payer"                     # AN-002
    SETTLEMENT_AS_EXPENSE = "settlement_as_expense"     # AN-003
    NAME_INCONSISTENCY = "name_inconsistency"           # AN-004
    INVALID_PRECISION = "invalid_precision"             # AN-005
    MISSING_CURRENCY = "missing_currency"               # AN-006
    NEGATIVE_AMOUNT = "negative_amount"                 # AN-007
    ZERO_AMOUNT = "zero_amount"                         # AN-008
    AMBIGUOUS_DATE = "ambiguous_date"                   # AN-009
    MEMBERSHIP_VIOLATION = "membership_violation"       # AN-010
    UNKNOWN_PARTICIPANT = "unknown_participant"         # AN-011
    SPLIT_TYPE_MISMATCH = "split_type_mismatch"         # AN-012
