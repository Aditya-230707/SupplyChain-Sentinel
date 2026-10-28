# SupplyChain Sentinel Test Fixtures
"""
Shared pytest fixtures.

No network access, no real providers, no real database in unit tests.
"""

from __future__ import annotations

import os

# Force test environment settings before any app import
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
