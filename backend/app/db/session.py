"""
Database session and engine management.

Uses SQLAlchemy 2.x async engine with aiosqlite for local development.
The DATABASE_URL in .env controls the backend; switching to PostgreSQL
(asyncpg) requires only an env-var change — no code edits.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.base import Base

log = structlog.get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, object] = {}
        if "sqlite" in settings.database_url:
            # SQLite requires check_same_thread=False for async
            connect_args["check_same_thread"] = False

        _engine = create_async_engine(
            settings.database_url,
            connect_args=connect_args,
            echo=settings.app_env == "development" and settings.log_level == "DEBUG",
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def init_db() -> None:
    """Create all tables if they do not exist.

    In production use Alembic migrations instead of create_all.
    For the hackathon MVP this is sufficient for local SQLite.
    """
    engine = _get_engine()
    # Import models so their metadata is registered on Base
    import app.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    log.info("db_tables_created_or_verified")


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session per request."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
