# ExpenseFlow

A full-stack expense sharing application built for the Spreetail assignment. It allows users to create groups, add members, manually add expenses (with equal, percentage, or exact share splits), and upload CSV files of historical expenses with an automated **Anomaly Detection Engine**.

## Live Links
- **Frontend (Vercel)**: https://expenseflow.vercel.app/ (Replace with your actual Vercel URL)
- **Backend (Render)**: https://expenseflow-backend-tb8p.onrender.com

## Tech Stack
- **Backend**: FastAPI (Python), SQLAlchemy (Async), asyncpg, Alembic.
- **Frontend**: React, Vite, React Router, Axios.
- **Database**: PostgreSQL (hosted on Supabase).
- **Authentication**: JWT (JSON Web Tokens).

## Local Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- A PostgreSQL database URL

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Devansh987/expenseflow.git
cd expenseflow

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
# Create a .env file in the root directory:
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
SECRET_KEY=your_secret_key_here
FRONTEND_URL=http://localhost:5173

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# Open a new terminal and navigate to the frontend folder
cd frontend

# Install dependencies
npm install

# Configure Environment Variables
# Create a .env file in the frontend directory:
VITE_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

## AI Usage Disclosure
This project was developed with the assistance of an AI coding agent (Gemini). For full details on the prompts used, the challenges faced with AI hallucinations, and how they were resolved, please refer to `AI_USAGE.md`.
