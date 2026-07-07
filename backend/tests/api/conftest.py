"""Fixtures for API tests: isolated temp DB + a fresh FastAPI app per test."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import connection


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_finally.db"
    connection.configure(db_file)
    yield db_file
    connection._db_path = None
    connection._initialized_paths.clear()


@pytest.fixture
def client(temp_db, monkeypatch):
    # Force the GBM simulator regardless of the ambient shell environment, so
    # API tests are deterministic and don't depend on network access to Massive.
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
