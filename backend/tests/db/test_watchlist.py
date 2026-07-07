"""Tests for watchlist repository functions."""

from app.db import (
    add_to_watchlist,
    get_watchlist,
    is_watched,
    remove_from_watchlist,
)


class TestWatchlist:
    def test_seeded_watchlist_has_ten(self, temp_db):
        assert len(get_watchlist()) == 10

    def test_add_new_ticker(self, temp_db):
        entry = add_to_watchlist("PYPL")
        assert entry.ticker == "PYPL"
        assert entry.user_id == "default"
        assert is_watched("PYPL")
        assert len(get_watchlist()) == 11

    def test_add_is_idempotent(self, temp_db):
        add_to_watchlist("PYPL")
        add_to_watchlist("PYPL")
        assert len(get_watchlist()) == 11

    def test_add_normalizes_to_uppercase(self, temp_db):
        entry = add_to_watchlist("  pypl ")
        assert entry.ticker == "PYPL"
        assert is_watched("pypl")

    def test_remove_existing(self, temp_db):
        assert remove_from_watchlist("AAPL") is True
        assert not is_watched("AAPL")
        assert len(get_watchlist()) == 9

    def test_remove_missing_returns_false(self, temp_db):
        assert remove_from_watchlist("ZZZZ") is False

    def test_isolation_between_users(self, temp_db):
        add_to_watchlist("PYPL", user_id="alice")
        assert is_watched("PYPL", user_id="alice")
        assert not is_watched("PYPL", user_id="default")
