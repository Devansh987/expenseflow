"""
FastAPI routers (API endpoints).

Each router groups related endpoints and is registered
in main.py with a URL prefix.
"""

from app.routers import auth

__all__ = ["auth"]
