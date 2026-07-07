"""Tests for trades repository functions."""

import pytest

from app.db import get_trades, record_trade


class TestTrades:
    def test_record_and_retrieve(self, temp_db):
        trade = record_trade("AAPL", "buy", quantity=10, price=190.0)
        assert trade.side == "buy"
        assert trade.quantity == 10
        assert trade.price == 190.0
        assert trade.id
        assert trade.executed_at
        assert get_trades() == [trade]

    def test_ticker_normalized(self, temp_db):
        trade = record_trade("aapl", "buy", quantity=1, price=1.0)
        assert trade.ticker == "AAPL"

    def test_invalid_side_raises(self, temp_db):
        with pytest.raises(ValueError):
            record_trade("AAPL", "hold", quantity=1, price=1.0)

    def test_most_recent_first(self, temp_db):
        record_trade("AAPL", "buy", quantity=1, price=1.0)
        record_trade("MSFT", "buy", quantity=1, price=2.0)
        record_trade("TSLA", "sell", quantity=1, price=3.0)
        trades = get_trades()
        assert [t.ticker for t in trades] == ["TSLA", "MSFT", "AAPL"]

    def test_limit(self, temp_db):
        for _ in range(5):
            record_trade("AAPL", "buy", quantity=1, price=1.0)
        assert len(get_trades(limit=3)) == 3

    def test_fractional_quantity(self, temp_db):
        trade = record_trade("AAPL", "buy", quantity=2.5, price=190.0)
        assert trade.quantity == 2.5

    def test_isolation_between_users(self, temp_db):
        record_trade("AAPL", "buy", quantity=1, price=1.0, user_id="alice")
        assert len(get_trades(user_id="alice")) == 1
        assert len(get_trades(user_id="default")) == 0
