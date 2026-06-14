"""
Import Session service.

Handles the creation of import sessions, parsing CSVs, running
anomaly detection, and importing valid rows into the database.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, date
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.import_session import ImportSession
from app.models.import_issue import ImportIssue
from app.models.user import User
from app.models.membership import Membership
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.exchange_rate import ExchangeRate
from app.models.enums import ImportStatus, SplitType
from app.utils.csv_parser import parse_csv_file
from app.services.anomaly_engine import parse_csv_date, find_user_by_name
from app.services.expense import _calculate_share_amounts


def parse_split_details(split_details_str: str) -> dict[str, float]:
    """
    Parses a string like 'Aisha 30%; Rohan 30%' or 'Aisha 1; Rohan 2'
    and returns a dict of lowercase name -> float.
    """
    if not split_details_str:
        return {}
    res = {}
    parts = split_details_str.split(";")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        tokens = part.rsplit(None, 1)
        if len(tokens) == 2:
            name, val_str = tokens
            name = name.strip().lower()
            val_str = val_str.replace("%", "").strip()
            try:
                res[name] = float(val_str)
            except ValueError:
                res[name] = 1.0
        else:
            name = part.strip().lower()
            res[name] = 1.0
    return res


async def get_active_members_on_date(db: AsyncSession, group_id: uuid.UUID, target_date: date) -> list[User]:
    """Get all active members of the group on a specific date."""
    dt = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    query = (
        select(User)
        .join(Membership)
        .where(
            (Membership.group_id == group_id) &
            (Membership.joined_at <= dt) &
            ((Membership.left_at.is_(None)) | (Membership.left_at >= dt))
        )
    )
    res = await db.execute(query)
    return list(res.scalars().all())


async def resolve_usd_rate(db: AsyncSession, expense_date: date) -> float:
    """Find the exchange rate for USD on or before the expense date, or return 83.0 default."""
    query = (
        select(ExchangeRate)
        .where(ExchangeRate.currency == "USD")
        .where(ExchangeRate.effective_date <= expense_date)
        .order_by(ExchangeRate.effective_date.desc())
        .limit(1)
    )
    res = await db.execute(query)
    rate_record = res.scalars().first()
    if rate_record:
        return float(rate_record.rate_to_inr)
    
    # If no rate exists at all in the database, seed a default USD rate for this date
    fallback_rate = 83.0
    try:
        new_rate = ExchangeRate(
            currency="USD",
            rate_to_inr=fallback_rate,
            effective_date=expense_date
        )
        db.add(new_rate)
        await db.flush()
    except Exception:
        # Ignore uniqueness constraint violations under concurrency
        pass
    return fallback_rate


class DummySplit:
    """Dummy class to interface with the split calculation helper."""
    def __init__(self, user_id: uuid.UUID, share_percentage: float | None = None, share_ratio: float | None = None):
        self.user_id = user_id
        self.share_percentage = share_percentage
        self.share_ratio = share_ratio


async def start_import(db: AsyncSession, group_id: uuid.UUID, file: UploadFile, uploader: User) -> ImportSession:
    """
    Initialize a CSV import session, parse the file, detect anomalies,
    and save all non-anomalous rows into the database.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are supported."
        )

    # 1. Create the Import Session record
    db_session = ImportSession(
        group_id=group_id,
        uploaded_by=uploader.id,
        file_name=file.filename,
        status=ImportStatus.PENDING,
    )
    db.add(db_session)
    await db.flush()  # Flush to get the ID

    # 2. Read and parse the CSV
    content = await file.read()
    try:
        parsed_rows = parse_csv_file(content)
    except ValueError as e:
        db_session.status = ImportStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {str(e)}"
        )

    # 3. Update session with initial row count and status
    db_session.total_rows = len(parsed_rows)
    db_session.status = ImportStatus.PROCESSING
    await db.commit()
    await db.refresh(db_session)

    # 4. Run Anomaly Detection Engine
    from app.services.anomaly_engine import detect_anomalies
    issues = await detect_anomalies(db, db_session.id, group_id, parsed_rows)

    if issues:
        db.add_all(issues)
        db_session.failed_rows = len({issue.row_number for issue in issues})
        db_session.successful_rows = db_session.total_rows - db_session.failed_rows
    else:
        db_session.failed_rows = 0
        db_session.successful_rows = db_session.total_rows

    # 5. Insert valid rows
    failed_row_numbers = {issue.row_number for issue in issues}
    
    if db_session.successful_rows > 0:
        # Pre-fetch memberships to map names to users
        query = (
            select(Membership)
            .options(selectinload(Membership.user))
            .where(Membership.group_id == group_id)
        )
        result = await db.execute(query)
        memberships = result.scalars().all()
        
        user_by_name = {}
        for m in memberships:
            u = m.user
            user_by_name[u.username.lower()] = u
            user_by_name[u.email.lower()] = u
            
        for idx, row in enumerate(parsed_rows):
            row_number = idx + 1
            if row_number in failed_row_numbers:
                continue  # Skip anomalous rows
                
            # Extract fields
            raw_desc = str(row.get("description", "") or "").strip()
            raw_amount_str = str(row.get("amount", "") or "").strip()
            raw_currency = str(row.get("currency", "") or "").strip().upper()
            raw_payer = str(row.get("payer", row.get("paid_by", "")) or "").strip()
            raw_date_str = str(row.get("date", row.get("expense_date", "")) or "").strip()
            raw_split_type = str(row.get("split_type", "") or "").strip().lower()
            raw_split_with = str(row.get("split_with", "") or "").strip()
            raw_split_details = str(row.get("split_details", "") or "").strip()
            raw_notes = str(row.get("notes", "") or "").strip()
            
            # Clean and parse amount
            clean_amount_str = raw_amount_str.replace(",", "")
            amount = float(clean_amount_str)
            
            # Parse Date
            expense_date = parse_csv_date(raw_date_str)
            if not expense_date:
                continue  # Fallback safety (should be caught by validation, but just in case)
            
            # Map Payer
            payer_user = find_user_by_name(raw_payer, user_by_name)
            if not payer_user:
                continue
            payer_id = payer_user.id
            
            # Handle Currency Conversion
            original_amount = amount
            original_currency = raw_currency if raw_currency else "INR"
            
            if original_currency == "USD":
                rate = await resolve_usd_rate(db, expense_date)
                converted_amount = round(amount * rate, 2)
            else:
                converted_amount = amount
                
            # Map Split Type
            if raw_split_type == "equal" or not raw_split_type:
                split_type = SplitType.EQUAL
            elif raw_split_type == "percentage":
                split_type = SplitType.PERCENTAGE
            elif raw_split_type in ("share", "shares", "unequal"):
                split_type = SplitType.SHARES
            else:
                split_type = SplitType.EQUAL
                
            # Determine Split Participants
            if raw_split_with:
                participants_names = [n.strip() for n in raw_split_with.split(";") if n.strip()]
                participants = []
                for p_name in participants_names:
                    p_user = find_user_by_name(p_name, user_by_name)
                    if p_user:
                        participants.append(p_user)
            else:
                # Default to all active members on the expense date
                participants = await get_active_members_on_date(db, group_id, expense_date)
                
            if not participants:
                continue
                
            # Parse Split Details if any
            details_map = parse_split_details(raw_split_details)
            
            # Build dummy splits list for calculating exact shares
            dummy_splits = []
            for p in participants:
                p_lower = p.username.lower()
                val = details_map.get(p_lower, details_map.get(p.email.lower(), 1.0))
                
                if split_type == SplitType.PERCENTAGE:
                    dummy_splits.append(DummySplit(p.id, share_percentage=val))
                elif split_type == SplitType.SHARES:
                    dummy_splits.append(DummySplit(p.id, share_ratio=val))
                else:
                    dummy_splits.append(DummySplit(p.id))
                    
            # Calculate exact share amounts using core Decimal utility
            try:
                share_amounts = _calculate_share_amounts(converted_amount, dummy_splits, split_type)
            except ValueError:
                # If ratio/percentage sum is zero or invalid, skip or default
                continue
            
            # Create the Expense record
            db_expense = Expense(
                group_id=group_id,
                payer_id=payer_id,
                description=raw_desc,
                amount=converted_amount,
                currency="INR",
                original_amount=original_amount,
                original_currency=original_currency,
                expense_date=expense_date,
                split_type=split_type,
                notes=raw_notes or f"Imported row {row_number} from CSV",
            )
            db.add(db_expense)
            await db.flush()
            
            # Create the ExpenseSplit records
            for d_split, share_amt in zip(dummy_splits, share_amounts):
                db_split = ExpenseSplit(
                    expense_id=db_expense.id,
                    user_id=d_split.user_id,
                    share_amount=share_amt,
                    share_percentage=d_split.share_percentage,
                    share_ratio=d_split.share_ratio,
                )
                db.add(db_split)

    # 6. Mark as completed (processing finished, but issues may need review)
    db_session.status = ImportStatus.COMPLETED
    db_session.completed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(db_session)

    return db_session


async def get_import_sessions(db: AsyncSession, group_id: uuid.UUID) -> list[ImportSession]:
    """List all import sessions for a group."""
    query = (
        select(ImportSession)
        .where(ImportSession.group_id == group_id)
        .order_by(ImportSession.uploaded_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
