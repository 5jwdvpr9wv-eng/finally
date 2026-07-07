"""Tests for portfolio_snapshots repository functions."""

from app.db import get_snapshots, record_snapshot


class TestSnapshots:
    def test_record_and_retrieve(self, temp_db):
        snap = record_snapshot(10000.0)
        assert snap.total_value == 10000.0
        assert snap.id
        assert snap.recorded_at
        assert get_snapshots() == [snap]

    def test_chronological_order(self, temp_db):
        record_snapshot(100.0)
        record_snapshot(200.0)
        record_snapshot(300.0)
        values = [s.total_value for s in get_snapshots()]
        assert values == [100.0, 200.0, 300.0]

    def test_limit_returns_most_recent_chronological(self, temp_db):
        for v in [100.0, 200.0, 300.0, 400.0]:
            record_snapshot(v)
        # Most recent 2, still oldest-first.
        assert [s.total_value for s in get_snapshots(limit=2)] == [300.0, 400.0]

    def test_isolation_between_users(self, temp_db):
        record_snapshot(1.0, user_id="alice")
        assert len(get_snapshots(user_id="alice")) == 1
        assert len(get_snapshots(user_id="default")) == 0
