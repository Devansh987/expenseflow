from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, group, expense, balance, settlement, import_session, import_report

# ─── Application Factory ────────────────────────────────────────────
# We create the FastAPI instance here and register routers.
# Routers are added incrementally as we build each phase.

app = FastAPI(
    title="ExpenseFlow",
    description="Shared expense management API with CSV import and anomaly detection",
    version="0.1.0",
)

# ─── CORS Middleware ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        settings.FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(group.router)
app.include_router(expense.router)
app.include_router(balance.router)
app.include_router(settlement.router)
app.include_router(import_session.router)
app.include_router(import_report.router)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.

    Returns a 200 OK response to verify the service is running.
    Useful for container orchestrators (Docker, K8s) and uptime monitors.
    """
    return {"status": "healthy", "version": "0.1.0"}
