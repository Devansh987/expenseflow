# CSV Import Audit Report
**Import Session ID**: `550e8400-e29b-41d4-a716-446655440000`
**Timestamp**: 2026-06-15 09:12:45 UTC
**File Processed**: `Expenses Export.csv`

## Import Summary
- **Total Rows Processed**: 154
- **Rows Imported Successfully**: 147
- **Rows Failed (Anomalies Detected)**: 7
- **Status**: COMPLETED (with issues)

---

## Detected Anomalies Log

The following rows contained anomalies and were skipped by the Anomaly Detection Engine to preserve database integrity.

### 1. Row 14
- **Anomaly Type**: `NAME_INCONSISTENCY` (UNKNOWN_PARTICIPANT)
- **Description**: The Payer 'Rohit' could not be mapped to any active member in the group.
- **Action Taken**: Row skipped. 
- **Suggested Resolution**: Verify the spelling of 'Rohit' or add them to the group via the Members tab before re-importing.

### 2. Row 28
- **Anomaly Type**: `DUPLICATE_EXPENSE`
- **Description**: An exact match for this expense ('Dinner at CyberHub', INR 4500, paid by Aisha on 2023-11-04) already exists in the database.
- **Action Taken**: Row skipped to prevent double-charging.
- **Suggested Resolution**: No action needed if this was already recorded. Otherwise, modify the description if it's a separate transaction.

### 3. Row 56
- **Anomaly Type**: `NEGATIVE_AMOUNT`
- **Description**: Amount '-500' is invalid. Expenses cannot be negative.
- **Action Taken**: Row skipped.
- **Suggested Resolution**: If this is a refund, treat it as a settlement or reduce the original expense amount.

### 4. Row 89
- **Anomaly Type**: `SETTLEMENT_AS_EXPENSE`
- **Description**: Description 'Rohan paid Aisha for rent' matches a settlement pattern, not a shared expense.
- **Action Taken**: Row skipped.
- **Suggested Resolution**: Use the 'Settle Up' feature in the Balances tab instead of importing this as an expense.

### 5. Row 102
- **Anomaly Type**: `SPLIT_TYPE_MISMATCH`
- **Description**: Split type is 'Percentage', but the provided split values (Aisha: 50%, Rohan: 40%) sum to 90%, not 100%.
- **Action Taken**: Row skipped.
- **Suggested Resolution**: Ensure percentages in the Split Details column equal exactly 100%.

### 6. Row 134
- **Anomaly Type**: `INVALID_PRECISION`
- **Description**: Amount '1450.456' has too many decimal places.
- **Action Taken**: Row skipped.
- **Suggested Resolution**: Round the amount to 2 decimal places maximum.

### 7. Row 150
- **Anomaly Type**: `AMBIGUOUS_DATE`
- **Description**: Date '14/15/2023' could not be parsed into a valid calendar date.
- **Action Taken**: Row skipped.
- **Suggested Resolution**: Use a standard date format like YYYY-MM-DD.
