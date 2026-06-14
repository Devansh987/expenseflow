from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ─── Engine ──────────────────────────────────────────────────────────
# create_async_engine creates a connection pool to PostgreSQL.
# echo=False in production; set True to see generated SQL during debugging.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,       # Max persistent connections in the pool
    max_overflow=10,   # Extra connections allowed beyond pool_size under load
)


# ─── Session Factory ────────────────────────────────────────────────
# async_sessionmaker produces AsyncSession instances.
# expire_on_commit=False prevents lazy-load issues after commit
# (SQLAlchemy would otherwise try to re-fetch attributes synchronously).
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── Base Model ─────────────────────────────────────────────────────
# All ORM models inherit from this base class.
# DeclarativeBase is the modern SQLAlchemy 2.0 approach (replaces declarative_base()).
class Base(DeclarativeBase):
    pass


# ─── Dependency ─────────────────────────────────────────────────────
# FastAPI dependency that yields a session per request.
# The 'async with' block ensures the session is closed after the request,
# even if an exception occurs.
async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session per request.

    Usage in a router:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        yield session
