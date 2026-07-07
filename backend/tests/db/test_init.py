"""Tests for lazy database initialization and seeding."""

from app.db import connection
from app.db.connection import get_connection

DEFAULT_TICKERS = {
    "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
    "NVDA", "META", "JPM", "V", "NFLX",
}
EXPECTED_TABLES = {
    "users_profile", "watchlist", "positions",
    "trades", "portfolio_snapshots", "chat_messages",
}


class TestLazyInit:
    """Fresh-DB init creates all tables and seed data."""

    def test_file_created_on_first_connection(self, temp_db):
        assert not temp_db.exists()
        with get_connection():
            pass
        assert temp_db.exists()

    def test_all_tables_created(self, temp_db):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        names = {r["name"] for r in rows}
        assert EXPECTED_TABLES.issubset(names)

    def test_seed_user_profile(self, temp_db):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users_profile WHERE id = 'default'"
            ).fetchone()
        assert row is not None
        assert row["cash_balance"] == 10000.0
        assert row["created_at"]

    def test_seed_watchlist(self, temp_db):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = 'default'"
            ).fetchall()
        assert {r["ticker"] for r in rows} == DEFAULT_TICKERS

    def test_init_runs_once_per_path(self, temp_db):
        # Multiple connections must not duplicate seed rows.
        with get_connection():
            pass
        with get_connection():
            pass
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM watchlist").fetchone()["c"]
        assert count == len(DEFAULT_TICKERS)

    def test_seed_not_reapplied_after_user_edit(self, temp_db):
        # Simulate a user clearing their watchlist, then forcing a re-init.
        with get_connection() as conn:
            conn.execute("DELETE FROM watchlist")
        # Force lazy-init to run again by clearing the initialized cache but
        # keeping the same populated (non-empty users_profile) DB file.
        connection._initialized_paths.clear()
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM watchlist").fetchone()["c"]
        # users_profile is non-empty, so seed is skipped — user's edit persists.
        assert count == 0
