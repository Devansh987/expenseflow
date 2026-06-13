# Project Scope



ExpenseFlow is a shared expense management application designed to handle messy real-world financial data. The application supports:



User authentication

Group creation and management

Dynamic group membership (join/leave tracking)

Expense creation and management

Debt settlements

Balance calculations

CSV import with anomaly detection

Import audit reports

Anomaly Log

AN-001 Duplicate Expense

Example



Dinner at Marina Bites



Rows:



08/02/2026 - Dinner at Marina Bites - Dev - ₹3200

08/02/2026 - dinner - marina bites - Dev - ₹3200

Detection Rule

Same payer

Same amount

Same date

Similar description

Action



Flag for review.



Suggested resolution:

Merge duplicate entries after user approval.



AN-002 Missing Payer

Example



House cleaning supplies



Detection Rule



paid\_by field is empty



Action



Manual review required.



Importer will not automatically assign a payer.



AN-003 Settlement Logged as Expense

Example



Rohan paid Aisha back



Detection Rule



Description contains settlement-related keywords:



paid back

reimbursed

settled

Action



Convert to Settlement record after user approval.



AN-004 Name Inconsistency

Examples

Priya

priya

Priya S

Detection Rule



Case-insensitive name comparison.



Action



Suggest merge to existing member.



User confirmation required.



AN-005 Invalid Currency Precision

Example



₹899.995



Detection Rule



More than 2 decimal places.



Action



Round to 2 decimal places.



Store original value in import report.



AN-006 Missing Currency

Example



Groceries DMart - 15/03/2026



Detection Rule



Currency field is blank.



Action



Suggest INR based on surrounding records.

Require confirmation.



AN-007 Negative Expense

Example



Parasailing refund - USD -30



Detection Rule



Amount less than zero.



Action



Treat as refund transaction.

Store separately in audit report.



AN-008 Zero Amount Expense

Example



Dinner order Swiggy



Detection Rule



Amount equals zero.



Action



Flag for review.



May represent correction or duplicate cancellation.



AN-009 Ambiguous Date Format

Example



4/5/2026



Detection Rule



Date format can be interpreted multiple ways.



Action



Require user confirmation.



AN-010 Membership Violation

Example



Expense includes Meera after moving out.



Detection Rule



Expense date falls outside membership period.



Action



Flag and suggest member removal.



AN-011 Unknown Participant

Example



Kabir



Detection Rule



Participant not registered in group.



Action



Create temporary guest participant or require manual mapping.



AN-012 Split Type Mismatch

Example



Split type = equal



Split details contain weighted shares.



Detection Rule



Split type and split details disagree.



Action



Flag for review.



Split type treated as source of truth.





