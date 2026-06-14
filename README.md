# ExpenseFlow

ExpenseFlow is a production-quality shared expense management application designed to handle messy real-world financial data. It allows users to track shared expenses, manage dynamic group memberships, calculate precise financial balances, and import external CSV data while running anomaly detection to flag issues like duplicates, missing data, and type mismatches.

## Tech Stack

* **Framework:** FastAPI
* **Database:** PostgreSQL (with `asyncpg`)
* **ORM:** SQLAlchemy 2.0 (Async)
* **Migrations:** Alembic
* **Validation:** Pydantic
* **Authentication:** JWT (JSON Web Tokens) with Bcrypt password hashing
* **Python Version:** 3.13

## Architecture

The application strictly follows a **Service-Layer Architecture** to keep the codebase modular, testable, and maintainable:

1. **Routers (`app/routers/`):** Handles HTTP requests, validation (via Pydantic), and HTTP responses.
2. **Services (`app/services/`):** Encapsulates core business logic (e.g., calculating splits, detecting anomalies, calculating balances).
3. **Models (`app/models/`):** SQLAlchemy ORM models representing database tables.
4. **Schemas (`app/schemas/`):** Pydantic schemas for data validation and serialization.
5. **Utils (`app/utils/`):** Reusable utilities (e.g., CSV parsing, security, dependency injection).

## Features Implemented

1. **Authentication:** Register, login (OAuth2 Password Bearer), and JWT generation.
2. **Dynamic Membership:** Track when users join and leave groups to maintain historical accuracy in expense calculations.
3. **Expense Management:** Support for Equal, Percentage, and Shares-based splits. Exact precision math using Python `Decimal` to avoid penny-drop errors.
4. **Balance Engine:** DB-level aggregations combined with a greedy debt-simplification algorithm to suggest minimal settlements between members.
5. **Settlements:** Record cash transfers between users to zero out debts.
6. **CSV Importer & Anomaly Engine:** An asynchronous file upload pipeline that parses CSVs and runs them against a 12-rule anomaly detection engine (detecting duplicates, format errors, membership violations, etc.), generating an actionable audit report.

## How to Run Locally

### 1. Prerequisites

* Python 3.13
* PostgreSQL database

### 2. Setup Environment

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/expenseflow
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

Apply the Alembic migrations to create the tables in your PostgreSQL database:

```bash
alembic upgrade head
```

### 5. Start the Application

Run the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 6. Interactive API Documentation

FastAPI automatically generates interactive Swagger documentation. Once the server is running, visit:

`http://localhost:8000/docs`
