"""SQLite connection handling and lazy initialization.

The database is created and seeded on first use — no separate migration step.
The first time a connection is opened for a given path, the schema is applied
(idempotent CREATE TABLE IF NOT EXISTS) and, if the database is empty, the
default seed data is inserted. Subsequent connections skip straight to the
query.

Callers never touch this module directly; they go through the repository
functions in ``app.db.repository``, which use ``get_connection()`` internally.
Tests call ``configure()`` to point at a temp database.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

# schema/ lives at backend/schema; this file is backend/app/db/connection.py.
_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schema"
_SCHEMA_SQL = _SCHEMA_DIR / "schema.sql"
_SEED_SQL = _SCHEMA_DIR / "seed.sql"

# Default runtime location: <project_root>/db/finally.db. Overridable via the
# FINALLY_DB_PATH environment variable (set in Docker to the volume mount).
_DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "db" / "finally.db"

_lock = Lock()
_db_path: Path | None = None
_initialized_paths: set[str] = set()


def _resolve_db_path() -> Path:
    """Determine the active database path (explicit config > env > default)."""
    global _db_path
    if _db_path is not None:
        return _db_path
    env_path = os.environ.get("FINALLY_DB_PATH", "").strip()
    return Path(env_path) if env_path else _DEFAULT_DB_PATH


def configure(db_path: str | Path) -> None:
    """Set the database path explicitly and reset init state.

    Intended for tests (point at a temp file) and for app startup if the path
    needs to be chosen programmatically. Clears the initialized-path cache so
    the next connection re-runs lazy init against the new path.
    """
    global _db_path
    with _lock:
        _db_path = Path(db_path)
        _initialized_paths.clear()


def _apply_script(conn: sqlite3.Connection, path: Path) -> None:
    conn.executescript(path.read_text())


def _ensure_initialized(conn: sqlite3.Connection, path: Path) -> None:
    """Create tables (if missing) and seed default data (if the DB is empty)."""
    key = str(path)
    with _lock:
        if key in _initialized_paths:
            return
        _apply_script(conn, _SCHEMA_SQL)
        row = conn.execute("SELECT COUNT(*) FROM users_profile").fetchone()
        if row[0] == 0:
            _apply_script(conn, _SEED_SQL)
        conn.commit()
        _initialized_paths.add(key)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a ready-to-use SQLite connection, committing on clean exit.

    Runs lazy init on first use for the active path. Rows come back as
    ``sqlite3.Row`` (mapping + index access). Commits on success, rolls back on
    exception, and always closes the connection.
    """
    path = _resolve_db_path()
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        _ensure_initialized(conn, path)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
