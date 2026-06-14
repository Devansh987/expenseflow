# Scope and Anomaly Log

This document outlines the anomalies handled by the CSV Anomaly Detection Engine and the database schema used to power the application.

## CSV Anomaly Detection Log

When a user uploads a CSV file of historical expenses, the system parses it and passes it through our Anomaly Engine before committing it to the database. Instead of failing an entire batch because of one bad row, the engine acts as an audit filter: valid rows are imported successfully, and invalid rows are flagged with specific `ImportIssue` records, allowing users to review the "Audit Report" in the UI.

Here is the log of data problems expected and handled by the system:

1. **Inconsistent/Unmapped Usernames**
   - **Problem**: The `Paid By` or `Split With` columns contain typos (e.g., "Rohan" vs "rohan") or reference users who are not registered members of the current group.
   - **Handling**: The engine performs case-insensitive matching. If a name cannot be resolved to an active `Membership` in the group, the row is flagged with `UNKNOWN_PARTICIPANT`.
2. **Duplicate Expenses**
   - **Problem**: The CSV contains the exact same expense twice (same description, amount, date, and payer).
   - **Handling**: The engine checks the database for existing expenses with identical signatures and flags the row as `DUPLICATE_EXPENSE`.
3. **Missing or Invalid Amounts**
   - **Problem**: The `Amount` field is empty, zero, negative, or contains non-numeric characters.
   - **Handling**: The engine strips commas. If the value is `<= 0`, it flags `NEGATIVE_AMOUNT` or `ZERO_AMOUNT`. If it cannot be parsed as a float, it flags `INVALID_PRECISION`.
4. **Settlements Masked as Expenses**
   - **Problem**: A row describes a debt repayment (e.g., "Rohan paid Aisha") rather than a shared group expense.
   - **Handling**: Detected via regex keywords in the description (e.g., "paid", "settled", "owed"). Flagged as `SETTLEMENT_AS_EXPENSE` with an instruction to use the native "Settle Up" feature instead.
5. **Split Percentage Mismatches**
   - **Problem**: When `Split Type` is `Percentage`, the provided percentages do not sum to 100%.
   - **Handling**: The engine calculates the sum. If `abs(sum - 100) > 0.01`, the row is flagged with `SPLIT_TYPE_MISMATCH`.
6. **Ambiguous Dates**
   - **Problem**: Dates are in unexpected formats (e.g., `DD/MM/YYYY` vs `MM/DD/YYYY`).
   - **Handling**: The engine attempts multiple format fallbacks via `dateutil.parser`. If all fail, it flags `AMBIGUOUS_DATE`.
7. **Missing Payer**
   - **Problem**: The `Paid By` column is entirely empty.
   - **Handling**: Flagged as `MISSING_PAYER`.

---

## Database Schema

The database relies on a strongly relational PostgreSQL schema hosted on Supabase.

- **User**: Core entity holding authentication credentials (`email`, `hashed_password`) and profile (`username`).
- **Group**: Represents a shared ledger (e.g., "Flatmates", "Trip to Goa").
- **Membership**: Junction table linking `User` to `Group`. Tracks when users joined and left (`joined_at`, `left_at`).
- **Expense**: Represents a single transaction. Tracks `amount`, `original_currency`, `expense_date`, `split_type` (`EQUAL`, `PERCENTAGE`, `SHARES`), and the `payer_id`.
- **ExpenseSplit**: The exact breakdown of who owes what for a specific `Expense`. Every expense has multiple split records (one per involved user) tracking their specific `share_amount`.
- **Settlement**: Represents a direct payment from one user to another to clear debt (`from_user_id`, `to_user_id`, `amount`).
- **ExchangeRate**: A historical ledger of currency exchange rates (e.g., USD to INR) mapped by `effective_date` to ensure past expenses are calculated accurately without relying on live APIs during imports.
- **ImportSession**: Tracks a CSV upload event (`file_name`, `status`, `total_rows`, `successful_rows`, `failed_rows`).
- **ImportIssue**: Linked to an `ImportSession`. Tracks the specific anomalies found during ingestion (`row_number`, `issue_type`, `description`, `suggested_action`).
