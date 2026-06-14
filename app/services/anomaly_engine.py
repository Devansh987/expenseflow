"""
Anomaly Detection Engine.

Processes parsed CSV rows and detects anomalies (AN-001 to AN-012)
defined in the project scope. Generates ImportIssue records.
"""

import uuid
import re
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.import_issue import ImportIssue
from app.models.enums import IssueType, IssueStatus
from app.models.user import User
from app.models.membership import Membership
from app.models.expense import Expense


def parse_csv_date(date_str: str) -> date | None:
    """Robustly parse a CSV date string into a datetime.date object."""
    date_str = str(date_str or "").strip()
    if not date_str:
        return None

    # Try standard formats with year
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    # Try formats with month name and day (like Mar-14)
    for fmt in ("%b-%d", "%d-%b", "%b/%d", "%d/%b"):
        try:
            dt = datetime.strptime(date_str, fmt)
            # Default to year 2026 as per our spreadsheet timeline
            return dt.replace(year=2026).date()
        except ValueError:
            pass

    # Try formats with month name, day and year (like 14-Mar-2026)
    for fmt in ("%d-%b-%Y", "%d/%b/%Y", "%b-%d-%Y", "%b/%d-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    return None


def find_user_by_name(name_str: str, user_by_name: dict[str, User]) -> User | None:
    """Helper to find user in group case-insensitively, supporting partial/spacing differences."""
    name_lower = name_str.strip().lower()
    if not name_lower:
        return None
    # Direct match
    if name_lower in user_by_name:
        return user_by_name[name_lower]
    # Check partial match (like "priya s" -> "priya")
    for k, u in user_by_name.items():
        if name_lower in k or k in name_lower:
            return u
    return None


async def detect_anomalies(
    db: AsyncSession, 
    session_id: uuid.UUID, 
    group_id: uuid.UUID, 
    parsed_rows: list[dict]
) -> list[ImportIssue]:
    """
    Run anomaly detection rules across all parsed CSV rows.
    Returns a list of ImportIssue records (not yet committed to the DB).
    """
    issues = []
    
    # Pre-fetch all group memberships (active and past) with their users
    query = (
        select(Membership)
        .options(selectinload(Membership.user))
        .where(Membership.group_id == group_id)
    )
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    # Map name/email to User, and User ID to their memberships
    user_by_name = {}
    memberships_by_user_id = {}
    for m in memberships:
        u = m.user
        user_by_name[u.username.lower()] = u
        user_by_name[u.email.lower()] = u
        memberships_by_user_id.setdefault(u.id, []).append(m)
        
    def is_user_active_on(user_id: uuid.UUID, target_date: date) -> bool:
        m_list = memberships_by_user_id.get(user_id, [])
        for m in m_list:
            joined_date = m.joined_at.date()
            left_date = m.left_at.date() if m.left_at else None
            if joined_date <= target_date and (left_date is None or left_date >= target_date):
                return True
        return False
    
    # For duplicate checking against existing expenses
    existing_expenses_query = select(Expense).where(Expense.group_id == group_id)
    result = await db.execute(existing_expenses_query)
    existing_expenses = result.scalars().all()
    
    # Keywords for AN-003
    settlement_keywords = ["reimbursed", "reimburse", "settled", "settle", "repaid", "repay", "paid back"]

    for idx, row in enumerate(parsed_rows):
        row_number = idx + 1  # 1-indexed for the user
        
        # Extract fields robustly
        raw_desc = str(row.get("description", "") or "").strip()
        raw_amount_str = str(row.get("amount", "") or "").strip()
        raw_currency = str(row.get("currency", "") or "").strip()
        raw_payer = str(row.get("payer", row.get("paid_by", "")) or "").strip()
        raw_date_str = str(row.get("date", row.get("expense_date", "")) or "").strip()
        raw_split_type = str(row.get("split_type", "") or "").strip().lower()
        
        # Parse Amount (clean commas first!)
        clean_amount_str = raw_amount_str.replace(",", "")
        amount = None
        try:
            if clean_amount_str:
                amount = float(clean_amount_str)
        except ValueError:
            pass

        # Parse Date
        expense_date = parse_csv_date(raw_date_str)

        # ─── AN-002: Missing Payer ──────────────────────────────────────
        if not raw_payer:
            issues.append(ImportIssue(
                import_session_id=session_id,
                row_number=row_number,
                issue_type=IssueType.MISSING_PAYER,
                description="The payer field is empty.",
                suggested_action="Manual review required to assign a payer.",
                raw_data=row
            ))

        # ─── AN-003: Settlement Logged as Expense ────────────────────────
        desc_lower = raw_desc.lower()
        is_settlement_desc = any(kw in desc_lower for kw in settlement_keywords) or ("paid" in desc_lower and "back" in desc_lower)
        if raw_desc and is_settlement_desc:
            issues.append(ImportIssue(
                import_session_id=session_id,
                row_number=row_number,
                issue_type=IssueType.SETTLEMENT_AS_EXPENSE,
                description=f"Description '{raw_desc}' looks like a settlement.",
                suggested_action="Convert this record to a Settlement after user approval.",
                raw_data=row
            ))

        if amount is not None:
            # ─── AN-007: Negative Expense ───────────────────────────────
            if amount < 0:
                issues.append(ImportIssue(
                    import_session_id=session_id,
                    row_number=row_number,
                    issue_type=IssueType.NEGATIVE_AMOUNT,
                    description=f"Amount is negative ({amount}).",
                    suggested_action="Treat as a refund transaction. Store separately in audit report.",
                    raw_data=row
                ))
            
            # ─── AN-008: Zero Amount Expense ────────────────────────────
            elif amount == 0:
                issues.append(ImportIssue(
                    import_session_id=session_id,
                    row_number=row_number,
                    issue_type=IssueType.ZERO_AMOUNT,
                    description="Amount is exactly zero.",
                    suggested_action="Flag for review. May represent correction or duplicate cancellation.",
                    raw_data=row
                ))

            # ─── AN-005: Invalid Currency Precision ──────────────────────
            # Check representation for > 2 decimal places (without commas)
            if "." in clean_amount_str and len(clean_amount_str.split(".")[1]) > 2:
                issues.append(ImportIssue(
                    import_session_id=session_id,
                    row_number=row_number,
                    issue_type=IssueType.INVALID_PRECISION,
                    description=f"Amount {raw_amount_str} has more than 2 decimal places.",
                    suggested_action="Round to 2 decimal places. Store original value in import report.",
                    original_value=raw_amount_str,
                    raw_data=row
                ))

        # ─── AN-006: Missing Currency ────────────────────────────────────
        if not raw_currency and amount is not None:
            issues.append(ImportIssue(
                import_session_id=session_id,
                row_number=row_number,
                issue_type=IssueType.MISSING_CURRENCY,
                description="Currency field is blank.",
                suggested_action="Suggest INR based on surrounding records. Require confirmation.",
                raw_data=row
            ))

        # ─── AN-009: Ambiguous Date Format ──────────────────────────────
        if raw_date_str:
            # Look for patterns like X/Y/YYYY where X <= 12 and Y <= 12
            # because 4/5/2026 could be April 5 or May 4.
            match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/]\d{4}$", raw_date_str)
            if match:
                p1, p2 = int(match.group(1)), int(match.group(2))
                if p1 <= 12 and p2 <= 12 and p1 != p2:
                    issues.append(ImportIssue(
                        import_session_id=session_id,
                        row_number=row_number,
                        issue_type=IssueType.AMBIGUOUS_DATE,
                        description=f"Date '{raw_date_str}' is ambiguous (could be MM/DD or DD/MM).",
                        suggested_action="Require user confirmation on date format.",
                        original_value=raw_date_str,
                        raw_data=row
                    ))

        # ─── AN-004: Name Inconsistency & AN-011: Unknown Participant ─────
        if raw_payer:
            payer_lower = raw_payer.lower()
            if payer_lower not in user_by_name:
                # Is there a partial match?
                partial_match = next((m for k, m in user_by_name.items() if payer_lower in k or k in payer_lower), None)
                if partial_match:
                    issues.append(ImportIssue(
                        import_session_id=session_id,
                        row_number=row_number,
                        issue_type=IssueType.NAME_INCONSISTENCY,
                        description=f"Payer name '{raw_payer}' differs in casing/spacing from existing member '{partial_match.username}'.",
                        suggested_action="Suggest merge to existing member. User confirmation required.",
                        raw_data=row
                    ))
                else:
                    issues.append(ImportIssue(
                        import_session_id=session_id,
                        row_number=row_number,
                        issue_type=IssueType.UNKNOWN_PARTICIPANT,
                        description=f"Payer '{raw_payer}' is not registered in the group.",
                        suggested_action="Create temporary guest participant or require manual mapping.",
                        raw_data=row
                    ))

        # Check split_with participants for AN-004 and AN-011
        split_with_str = str(row.get("split_with", "") or "").strip()
        if split_with_str:
            participants = [name.strip() for name in split_with_str.split(";") if name.strip()]
            for p_name in participants:
                p_lower = p_name.lower()
                if p_lower not in user_by_name:
                    partial_match = next((m for k, m in user_by_name.items() if p_lower in k or k in p_lower), None)
                    if partial_match:
                        issues.append(ImportIssue(
                            import_session_id=session_id,
                            row_number=row_number,
                            issue_type=IssueType.NAME_INCONSISTENCY,
                            description=f"Participant name '{p_name}' differs in casing/spacing from existing member '{partial_match.username}'.",
                            suggested_action="Suggest merge to existing member. User confirmation required.",
                            raw_data=row
                        ))
                    else:
                        issues.append(ImportIssue(
                            import_session_id=session_id,
                            row_number=row_number,
                            issue_type=IssueType.UNKNOWN_PARTICIPANT,
                            description=f"Participant '{p_name}' is not registered in the group.",
                            suggested_action="Create temporary guest participant or require manual mapping.",
                            raw_data=row
                        ))

        # ─── AN-010: Membership Violation ─────────────────────────────────
        if expense_date is not None:
            # 1. Payer check
            if raw_payer:
                payer_user = find_user_by_name(raw_payer, user_by_name)
                if payer_user:
                    if not is_user_active_on(payer_user.id, expense_date):
                        issues.append(ImportIssue(
                            import_session_id=session_id,
                            row_number=row_number,
                            issue_type=IssueType.MEMBERSHIP_VIOLATION,
                            description=f"Payer '{raw_payer}' was not an active member on {expense_date.isoformat()}.",
                            suggested_action="Flag and suggest member removal.",
                            raw_data=row
                        ))
            
            # 2. Participants check
            if split_with_str:
                participants = [name.strip() for name in split_with_str.split(";") if name.strip()]
                for p_name in participants:
                    p_user = find_user_by_name(p_name, user_by_name)
                    if p_user:
                        if not is_user_active_on(p_user.id, expense_date):
                            issues.append(ImportIssue(
                                import_session_id=session_id,
                                row_number=row_number,
                                issue_type=IssueType.MEMBERSHIP_VIOLATION,
                                description=f"Participant '{p_name}' was not an active member on {expense_date.isoformat()}.",
                                suggested_action="Flag and suggest member removal.",
                                raw_data=row
                            ))

        # ─── AN-012: Split Type Mismatch ─────────────────────────────────
        raw_split_details = str(row.get("split_details", "") or "").strip()
        if raw_split_type == "equal" and raw_split_details:
            if any(char.isdigit() for char in raw_split_details):
                issues.append(ImportIssue(
                    import_session_id=session_id,
                    row_number=row_number,
                    issue_type=IssueType.SPLIT_TYPE_MISMATCH,
                    description="Split type is 'equal', but split details contain weighted shares/numbers.",
                    suggested_action="Flag for review. Split type treated as source of truth.",
                    raw_data=row
                ))

        # ─── AN-001: Duplicate Expense ───────────────────────────────────
        if amount is not None and raw_desc:
            for ex in existing_expenses:
                if abs(float(ex.amount) - amount) < 0.01:
                    if raw_desc.lower() in ex.description.lower() or ex.description.lower() in raw_desc.lower():
                        issues.append(ImportIssue(
                            import_session_id=session_id,
                            row_number=row_number,
                            issue_type=IssueType.DUPLICATE_EXPENSE,
                            description=f"Similar expense found in database (ID: {ex.id}).",
                            suggested_action="Merge duplicate entries after user approval.",
                            raw_data=row
                        ))
                        break

    return issues
