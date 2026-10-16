"""
SQLAlchemy 2.x declarative base.

All ORM models inherit from this Base.
Using mapped_column / Mapped style (SQLAlchemy 2.0 API).
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
