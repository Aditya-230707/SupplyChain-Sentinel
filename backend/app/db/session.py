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

    # Seed initial demo suppliers if DB is freshly created and not in test mode
    settings = get_settings()
    if settings.app_env != "test":
        factory = get_session_factory()
        async with factory() as session:
            from decimal import Decimal

        from sqlalchemy import select

        from app.db.models import Supplier as SupplierModel
        from app.db.models import SupplierPart as SupplierPartModel

        stmt = select(SupplierModel).limit(1)
        existing = (await session.execute(stmt)).first()
        if not existing:
            s1 = SupplierModel(
                name="Silicon Foundry Dresden GmbH",
                aliases=["SFD", "Dresden Fab"],
                country_or_region="Germany",
                official_domains=["silicon-dresden.de"],
                criticality="high",
            )
            s1.parts.append(
                SupplierPartModel(
                    part_name="Automotive Microcontroller MCU-4",
                    part_number="MCU-4-DRESDEN",
                    inventory_coverage_days=Decimal("14"),
                    typical_lead_time_days=Decimal("60"),
                    recovery_duration_days=Decimal("45"),
                )
            )

            s2 = SupplierModel(
                name="Titan Energy Solutions",
                aliases=["Titan Energy"],
                country_or_region="United States",
                official_domains=["titan-energy.com"],
                criticality="medium",
            )
            s2.parts.append(
                SupplierPartModel(
                    part_name="Industrial Battery Module Pack-B",
                    part_number="BAT-MOD-B",
                    inventory_coverage_days=Decimal("30"),
                    typical_lead_time_days=Decimal("45"),
                    recovery_duration_days=Decimal("0"),
                )
            )

            s3 = SupplierModel(
                name="Vertex Components Ltd",
                aliases=["Vertex UK"],
                country_or_region="United Kingdom",
                official_domains=["vertex-components.co.uk"],
                criticality="high",
            )
            s3.parts.append(
                SupplierPartModel(
                    part_name="Aerospace Titanium Fastener",
                    part_number="AERO-FAST-9",
                    inventory_coverage_days=Decimal("45"),
                    typical_lead_time_days=Decimal("90"),
                )
            )

            session.add_all([s1, s2, s3])
            await session.commit()
            log.info("demo_suppliers_seeded")


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
