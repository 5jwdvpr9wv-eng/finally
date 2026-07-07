"""Tests for positions repository functions, including the UNIQUE constraint."""

import sqlite3
import uuid

import pytest

from app.db import (
    delete_position,
    get_position,
    get_positions,
    upsert_position,
)
from app.db.connection import get_connection


class TestPositions:
    def test_no_positions_initially(self, temp_db):
        assert get_positions() == []
        assert get_position("AAPL") is None

    def test_insert_position(self, temp_db):
        pos = upsert_position("AAPL", quantity=10, avg_cost=190.0)
        assert pos.ticker == "AAPL"
        assert pos.quantity == 10
        assert pos.avg_cost == 190.0
        assert pos.id
        assert get_position("AAPL") == pos

    def test_upsert_updates_in_place(self, temp_db):
        first = upsert_position("AAPL", quantity=10, avg_cost=190.0)
        second = upsert_position("AAPL", quantity=15, avg_cost=192.5)
        # Same row (id preserved), new values.
        assert second.id == first.id
        assert second.quantity == 15
        assert second.avg_cost == 192.5
        assert len(get_positions()) == 1

    def test_ticker_normalized(self, temp_db):
        upsert_position("aapl", quantity=5, avg_cost=100.0)
        assert get_position("AAPL") is not None

    def test_delete_position(self, temp_db):
        upsert_position("AAPL", quantity=10, avg_cost=190.0)
        assert delete_position("AAPL") is True
        assert get_position("AAPL") is None

    def test_delete_missing_returns_false(self, temp_db):
        assert delete_position("AAPL") is False

    def test_positions_sorted_by_ticker(self, temp_db):
        upsert_position("TSLA", quantity=1, avg_cost=250.0)
        upsert_position("AAPL", quantity=1, avg_cost=190.0)
        upsert_position("MSFT", quantity=1, avg_cost=420.0)
        assert [p.ticker for p in get_positions()] == ["AAPL", "MSFT", "TSLA"]

    def test_unique_user_ticker_constraint(self, temp_db):
        # A raw duplicate insert (bypassing upsert) must violate UNIQUE.
        upsert_position("AAPL", quantity=10, avg_cost=190.0)
        with pytest.raises(sqlite3.IntegrityError):
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO positions "
                    "(id, user_id, ticker, quantity, avg_cost, updated_at) "
                    "VALUES (?, 'default', 'AAPL', 5, 1.0, '2026-01-01T00:00:00Z')",
                    (str(uuid.uuid4()),),
                )

    def test_isolation_between_users(self, temp_db):
        upsert_position("AAPL", quantity=10, avg_cost=190.0, user_id="alice")
        assert get_position("AAPL", user_id="alice") is not None
        assert get_position("AAPL", user_id="default") is None
