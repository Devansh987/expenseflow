# Decision Log

This document outlines the significant product and engineering decisions made during the development of ExpenseFlow.

### 1. Architectural Choice: Service-Layer Pattern
**Options Considered:**
- **Fat Routers:** Put all database logic directly inside FastAPI router endpoints.
- **Service-Layer Architecture:** Separate HTTP routing (routers) from business logic (services) and database representation (models).

**Decision:** Service-Layer Architecture.
**Why:** To ensure the codebase is testable and maintainable. It allows the business logic (like complex expense splits and the greedy balance simplification algorithm) to be decoupled from HTTP requests. This was critical to confidently answer interview questions about tracing the code.

### 2. Handling Member Churn (Sam joining, Meera leaving)
**Options Considered:**
- **Hard Deletion:** Delete Meera's user record or membership record when she leaves.
- **Snapshotting:** Copy the user data into the expense record permanently.
- **Dynamic Temporal Memberships:** Add `joined_at` and `left_at` timestamps to the `Membership` table.

**Decision:** Dynamic Temporal Memberships.
**Why:** Sam asked: *"Why would March electricity affect my balance?"* By tracking the exact datetime a user is active in a group, the expense service validates that users were active members on the `expense_date` before allowing them to be added to a split. When Meera left, we simply set her `left_at` timestamp. This preserves her historical debts without charging her for new ones.

### 3. Financial Precision & "Magic Numbers"
**Options Considered:**
- **Floats:** Standard Python floating-point math.
- **Integer Cents:** Store everything multiplied by 100 as integers.
- **Python `Decimal`:** Use the decimal module with exact rounding rules.

**Decision:** Python `Decimal` with `ROUND_HALF_UP`.
**Why:** Rohan asked: *"No magic numbers."* Floating point math leads to penny-drop errors (e.g., 100 / 3 = 33.333333). The `Decimal` library allows us to calculate exact shares. To ensure the splits perfectly equal the total expense, any remaining pennies are added to the first split. 

### 4. Handling Currency (Priya's Dollars)
**Options Considered:**
- **Single Currency Database:** Force all expenses into INR at the API layer.
- **Dual-Column Tracking:** Store the `amount`/`currency` (normalized) and `original_amount`/`original_currency` for auditing.

**Decision:** Dual-Column Tracking.
**Why:** Priya noted the spreadsheet treats dollars as rupees. The database schema includes `original_amount` and `original_currency`. When an expense is imported in USD, the app flags it, converts the main `amount` to INR based on a standardized rate, but retains the `original_amount` in USD for audit purposes, satisfying Priya's concern.

### 5. Anomaly Handling Strategy (Meera's Edits)
**Options Considered:**
- **Silent Fixing:** The importer automatically guesses and fixes data.
- **Hard Crash:** The importer rejects the entire CSV if one row is bad.
- **Pre-flight Audit (Stateless Classification):** The importer parses the rows, detects issues, and generates `ImportIssue` records for human review.

**Decision:** Pre-flight Audit (Stateless Classification).
**Why:** Meera asked: *"I want to approve anything the app deletes or changes."* And the assignment strictly forbids silent guesses. The anomaly engine flags issues (like negative amounts or missing payers) and saves them to the DB as `ImportIssues` tied to an `ImportSession`, exposing an Audit Report endpoint to the user.

### 6. Debt Simplification
**Options Considered:**
- **Bipartite Graph Matching:** Complex max-flow min-cut algorithm.
- **Greedy Matching:** Sort debtors and creditors, match largest to largest.

**Decision:** Greedy Matching.
**Why:** Aisha asked: *"I just want one number per person. Who pays whom, how much, done."* The greedy algorithm efficiently minimizes the total number of transactions required to settle a group's debts.
