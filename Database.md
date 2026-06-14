



ExpenseFlow Database Design



1\. User



Purpose:

Stores registered users.



Fields:



\* id

\* username

\* email

\* password



\---



2\. Group



Purpose:

Stores expense groups.



Fields:



\* id

\* name

\* created\_by

\* created\_at



Example:



Flatmates Group



\---



3\. Membership



Purpose:

Tracks when a user joins or leaves a group.



Fields:



\* id

\* user\_id

\* group\_id

\* joined\_at

\* left\_at



Examples:



Meera:

joined\_at = 2026-02-01

left\_at = 2026-03-31



Sam:

joined\_at = 2026-04-08

left\_at = NULL



Reason:



Allows historical balance calculations when members leave or join.



\---



4\. Expense



Purpose:

Stores shared expenses.



Fields:



\* id

\* group\_id

\* payer\_id

\* description

\* amount

\* currency

\* expense\_date

\* split\_type

\* notes



Example:



Groceries BigBasket

₹2340



\---



5\. ExpenseSplit



Purpose:

Stores how an expense is divided.



Fields:



\* id

\* expense\_id

\* user\_id

\* share\_amount

\* share\_ratio



Supports:



\* Equal split

\* Percentage split

\* Share-based split



\---



6\. Settlement



Purpose:

Stores repayments between members.



Fields:



\* id

\* payer\_id

\* receiver\_id

\* amount

\* settlement\_date

\* notes



Example:



Rohan paid Aisha back



\---



7\. ImportSession



Purpose:

Tracks CSV imports.



Fields:



\* id

\* uploaded\_by

\* file\_name

\* uploaded\_at

\* status



\---



8\. ImportIssue



Purpose:

Stores anomalies found during import.



Fields:



\* id

\* import\_session\_id

\* row\_number

\* issue\_type

\* description

\* suggested\_action

\* status



Example:



Duplicate Expense

Missing Payer

Settlement Detected



\---



9\. ExchangeRate



Purpose:

Stores currency conversion information.



Fields:



\* id

\* currency

\* exchange\_rate

\* effective\_date



Reason:



Supports USD to INR conversion while preserving auditability.



