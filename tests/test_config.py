import os

import pytest

from app.core.config import Settings, _to_asyncpg_url, _to_sync_pg_url


def test_render_postgres_url_converts_to_asyncpg():
    """Render injects postgresql:// — must become postgresql+asyncpg://"""
    os.environ["DATABASE_URL"] = "postgresql://user:pass@host/db"
    os.environ["DATABASE_URL_SYNC"] = ""
    os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"
    os.environ["APP_ENV"] = "development"

    settings = Settings()
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert settings.DATABASE_URL_SYNC.startswith("postgresql://")

    del os.environ["DATABASE_URL"]


def test_postgres_scheme_converts():
    url = _to_asyncpg_url("postgres://user:pass@host/db")
    assert url == "postgresql+asyncpg://user:pass@host/db"


def test_sync_url_from_async():
    url = _to_sync_pg_url("postgresql+asyncpg://user:pass@host/db")
    assert url == "postgresql://user:pass@host/db"
