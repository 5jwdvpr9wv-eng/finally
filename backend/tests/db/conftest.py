"""Fixtures for database tests.

Every test gets a fresh, isolated SQLite file in a temp directory. The db
module is pointed at it via ``configure()``, so lazy init runs against the temp
path and the real ``db/finally.db`` is never touched.
"""

import pytest

from app.db import connection


@pytest.fixture
def temp_db(tmp_path):
    """Configure the db layer to use a fresh temp database for one test.

    Yields the database Path. Init/seed happens lazily on first connection.
    Restores the prior configuration afterward so tests don't leak state.
    """
    db_file = tmp_path / "test_finally.db"
    connection.configure(db_file)
    yield db_file
    # Reset module state so a later test re-inits against its own temp path.
    connection._db_path = None
    connection._initialized_paths.clear()
