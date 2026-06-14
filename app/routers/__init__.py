"""
FastAPI routers (API endpoints).

Each router groups related endpoints and is registered
in main.py with a URL prefix.
"""

from app.routers import auth
from app.routers import group
from app.routers import expense

__all__ = ["auth", "group", "expense"]
