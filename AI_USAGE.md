# AI Usage Log

This document discloses the AI tools used during the development of this project, the key prompts utilized, and instances where the AI generated incorrect outputs that required manual intervention and debugging.

## AI Tools Used
- **Antigravity (Gemini-powered coding agent)**

## Key Prompts Used
1. *"I need to build a full-stack expense sharing application like Splitwise. Scaffold a FastAPI backend and a React frontend."*
2. *"Create an automated Anomaly Detection Engine that can ingest a CSV of historical expenses, detect missing data or duplicate rows, and generate an audit report without failing the entire batch."*
3. *"Help me deploy this application for free using Supabase, Render, and Vercel. Write a deployment guide."*
4. *"Make the frontend design visually unique and premium so it doesn't look like a generic template. Change it to a Midnight Emerald FinTech theme."*

---

## Concrete Cases of AI Errors & Resolution

Despite the utility of the AI, it hallucinated or produced problematic code in several critical areas related to infrastructure and dependency management.

### Case 1: Alembic Configuration Interpolation Crash
**The Problem**: When setting up the Supabase database, the AI generated a `DATABASE_URL` that included my password containing an `@` symbol. It told me to URL-encode it as `%40`. However, the AI failed to account for `configparser` (used by Alembic to read `alembic.ini` and `env.py`). `configparser` treats the `%` symbol as a string interpolation marker, causing the Render deployment to crash entirely with `ValueError: invalid interpolation syntax` during the `alembic upgrade head` build step.
**How I Caught It**: By inspecting the build logs in the Render dashboard, which clearly showed the traceback originating from `config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)` inside `alembic/env.py`.
**What Changed**: I intervened and modified `alembic/env.py` to programmatically escape the percent symbols before handing the string to Alembic: `settings.DATABASE_URL.replace("%", "%%")`.

### Case 2: Render IPv6 Network Blockade
**The Problem**: The AI initially instructed me to use the "Direct Connection" string provided by Supabase for the database connection on Render. However, the AI failed to warn me that Supabase's direct connection domains resolve to IPv6 addresses, while Render's free-tier build environments are strictly IPv4. This caused a fatal `OSError: [Errno 101] Network is unreachable` during the deployment.
**How I Caught It**: The connection timed out during the Alembic migration step on Render. The trace pointed to an underlying socket failure in `asyncpg`.
**What Changed**: I discarded the AI's instruction to use the Direct Connection URL and manually navigated the Supabase dashboard to retrieve the "Connection Pooler" URL (which acts as an IPv4 proxy). I updated the Render environment variable to use the pooler domain.

### Case 3: Passlib and Modern Bcrypt Incompatibility
**The Problem**: The AI scaffolded the authentication security module using `passlib.context.CryptContext` to hash passwords with `bcrypt`, which has been the standard FastAPI tutorial method for years. However, the AI did not know that modern versions of the `bcrypt` library (`>= 4.0.0`) enforce a strict 72-byte truncation limit. Because `passlib` is unmaintained, it attempts to verify a 73-character dummy password during initialization to test for a wrap bug, which caused the entire FastAPI application to crash on startup with `ValueError: password cannot be longer than 72 bytes`.
**How I Caught It**: The server failed to start locally and on Render, throwing the `ValueError` traceback originating from `passlib/handlers/bcrypt.py`.
**What Changed**: I instructed the AI to completely remove the `passlib` dependency from `requirements.txt` and rewrite the `app/utils/security.py` module to use the raw `bcrypt` library directly (`bcrypt.hashpw` and `bcrypt.checkpw`).
