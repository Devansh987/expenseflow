# ExpenseFlow

A production-quality shared expense management API built with FastAPI, PostgreSQL, and SQLAlchemy.

## Features

- User authentication (JWT)
- Group creation and management
- Dynamic membership tracking (join/leave history)
- Expense management with equal, percentage, and share-based splits
- Group-wise and individual balance calculations
- Settlement recording
- CSV import with anomaly detection
- Import audit reports

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (async via asyncpg)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Auth:** JWT (python-jose) + bcrypt (passlib)

## Project Structure

```
app/
├── main.py          # FastAPI application entry point
├── config.py        # Pydantic Settings (env vars)
├── database.py      # SQLAlchemy engine, session, Base
├── models/          # ORM models (User, Group, Expense, etc.)
├── schemas/         # Pydantic request/response schemas
├── routers/         # API endpoint handlers
├── services/        # Business logic layer
└── utils/           # Shared helpers (security, CSV, dates)
```

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env with your database credentials

# 4. Run the server
uvicorn app.main:app --reload
```

## API Docs

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
