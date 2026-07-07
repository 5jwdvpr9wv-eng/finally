"""Tests for prompt construction: portfolio context, history, and message shape."""

from app.db.models import ChatMessage
from app.llm.models import PortfolioContext
from app.llm.prompts import build_messages, format_portfolio_context


class TestPortfolioContextFromSnapshot:
    def test_builds_from_backend_snapshot_shape(self):
        snapshot = {
            "cash_balance": 5000.0,
            "total_value": 6000.0,
            "positions": [
                {
                    "ticker": "AAPL",
                    "quantity": 5,
                    "avg_cost": 190.0,
                    "current_price": 200.0,
                    "market_value": 1000.0,
                    "unrealized_pl": 50.0,
                    "unrealized_pl_percent": 5.26,
                }
            ],
            "watchlist": [{"ticker": "AAPL", "price": 200.0}, {"ticker": "NFLX", "price": None}],
        }
        context = PortfolioContext.from_snapshot(snapshot)
        assert context.cash == 5000.0
        assert context.total_value == 6000.0
        assert context.positions[0].ticker == "AAPL"
        assert context.positions[0].unrealized_pnl == 50.0
        assert context.positions[0].unrealized_pnl_percent == 5.26
        assert context.watchlist[1].ticker == "NFLX"
        assert context.watchlist[1].price is None


class TestFormatPortfolioContext:
    def test_empty_portfolio(self, empty_portfolio):
        text = format_portfolio_context(empty_portfolio)
        assert "$10,000.00" in text
        assert "Positions: none" in text
        assert "Watchlist: empty" in text

    def test_positions_and_watchlist_included(self, sample_portfolio):
        text = format_portfolio_context(sample_portfolio)
        assert "AAPL" in text
        assert "5" in text
        assert "$190.00" in text
        assert "$200.00" in text
        assert "50.00" in text
        assert "5.26" in text
        assert "NFLX" in text
        assert "unavailable" in text


class TestBuildMessages:
    def test_system_message_includes_portfolio_context(self, sample_portfolio):
        messages = build_messages(sample_portfolio, [], "how am I doing?")
        assert messages[0]["role"] == "system"
        assert "AAPL" in messages[0]["content"]
        assert "FinAlly" in messages[0]["content"]

    def test_history_and_new_message_appended_in_order(self, empty_portfolio):
        history = [
            ChatMessage(
                id="1", user_id="default", role="user", content="hi", actions=None,
                created_at="2026-01-01T00:00:00Z",
            ),
            ChatMessage(
                id="2", user_id="default", role="assistant", content="hello there",
                actions=None, created_at="2026-01-01T00:00:01Z",
            ),
        ]
        messages = build_messages(empty_portfolio, history, "buy 5 aapl")

        assert messages[1] == {"role": "user", "content": "hi"}
        assert messages[2] == {"role": "assistant", "content": "hello there"}
        assert messages[3] == {"role": "user", "content": "buy 5 aapl"}

    def test_history_truncated_to_last_20(self, empty_portfolio):
        history = [
            ChatMessage(
                id=str(i), user_id="default", role="user" if i % 2 == 0 else "assistant",
                content=f"msg{i}", actions=None, created_at="2026-01-01T00:00:00Z",
            )
            for i in range(30)
        ]
        messages = build_messages(empty_portfolio, history, "new message")
        # system + 20 history + new user message
        assert len(messages) == 22
        assert messages[1]["content"] == "msg10"
        assert messages[-2]["content"] == "msg29"
        assert messages[-1]["content"] == "new message"
