# Decision Log

This document outlines the significant architectural and technical decisions made during the development of ExpenseFlow.

## 1. Choice of Backend Framework: FastAPI
**Options Considered**: Django, Flask, FastAPI.
**Decision**: FastAPI.
**Reasoning**: Building a scalable expense API requires high performance and modern asynchronous capabilities. FastAPI provides built-in Pydantic validation (which is excellent for strictly parsing incoming CSV fields and split combinations), native `async/await` support, and automatic OpenAPI documentation. Django felt too heavy for an API-first approach, and Flask lacks native async and typing support.

## 2. Choice of Database: PostgreSQL (via Supabase)
**Options Considered**: SQLite, MongoDB, PostgreSQL.
**Decision**: PostgreSQL hosted on Supabase.
**Reasoning**: Financial ledgers require strict ACID compliance, relational integrity (ensuring an `ExpenseSplit` cannot exist without an `Expense`), and transactions. This ruled out MongoDB. While SQLite is great for local development, deploying to serverless environments (like Render) requires a detached, persistent database. Supabase provides an excellent, free-tier managed PostgreSQL instance. 

## 3. Handling Anomaly Detection in CSV Imports
**Options Considered**: 
1. "All-or-Nothing" transaction (if one row fails, reject the entire CSV).
2. "Audit Filter" (import valid rows, reject bad rows, generate report).
**Decision**: Audit Filter.
**Reasoning**: In the real world, a user uploading a 200-row CSV does not want the entire process to fail because Row 184 has a typo in a name. By implementing an Audit Filter, the system imports the 199 valid rows and creates an `ImportIssue` record for the 1 bad row. The frontend then displays an elegant "Audit Report" letting the user know exactly what needs to be fixed manually.

## 4. Currency Conversion (USD to INR)
**Options Considered**: 
1. Fetch live rates from an external API during import.
2. Store an internal ExchangeRate ledger.
**Decision**: Internal ExchangeRate ledger.
**Reasoning**: Financial imports must be idempotent. If a user imports a CSV of expenses from 2023 today, using today's live exchange rate would result in completely inaccurate debts. By storing historical rates mapped to `effective_date`, the system ensures accurate historical conversions without relying on flaky third-party APIs during ingestion.

## 5. Deployment Architecture
**Options Considered**: AWS EC2, Heroku, Render + Vercel.
**Decision**: Render (Backend) + Vercel (Frontend).
**Reasoning**: Vercel is the industry standard for hosting Vite/React frontends with zero-config CI/CD. Render was chosen for the FastAPI backend because it offers a generous free tier with Docker/Python support and integrates perfectly with Supabase's IPv4 Connection Poolers. This split architecture ensures the frontend is distributed globally via CDN while the backend scales independently.

## 6. Authentication Mechanism
**Options Considered**: Stateful Session Cookies, JWT (JSON Web Tokens).
**Decision**: JWT stored in localStorage.
**Reasoning**: To support a decoupled frontend/backend architecture, stateless JWTs are significantly easier to implement than configuring cross-origin CORS session cookies. The tokens include an expiration time, and the frontend Axios interceptors automatically attach the token as a Bearer header to secure API endpoints.
