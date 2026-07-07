"""Tests for get_chat_response: mock mode, structured parsing, graceful failure."""

import json

import pytest

from app.llm import get_chat_response
from app.llm.models import ChatResponse
from app.llm.service import MOCK_RESPONSE


class TestMockMode:
    async def test_mock_mode_returns_canonical_response(self, monkeypatch, empty_portfolio):
        monkeypatch.setenv("LLM_MOCK", "true")
        result = await get_chat_response("hi", empty_portfolio, [])
        assert result == MOCK_RESPONSE

    async def test_mock_mode_exact_verbatim_text(self, monkeypatch, empty_portfolio):
        monkeypatch.setenv("LLM_MOCK", "true")
        result = await get_chat_response("hi", empty_portfolio, [])
        assert result.message == (
            "I've analyzed your portfolio. You have $10,000 in cash and no open "
            "positions. I recommend starting with a diversified position — shall "
            "I buy 5 shares of AAPL?"
        )
        assert result.trades == []
        assert result.watchlist_changes == []

    async def test_mock_mode_case_insensitive(self, monkeypatch, empty_portfolio):
        monkeypatch.setenv("LLM_MOCK", "True")
        result = await get_chat_response("hi", empty_portfolio, [])
        assert result == MOCK_RESPONSE

    async def test_mock_mode_skips_network_call(self, monkeypatch, empty_portfolio):
        monkeypatch.setenv("LLM_MOCK", "true")

        def boom(*args, **kwargs):
            raise AssertionError("network call should not happen in mock mode")

        monkeypatch.setattr("app.llm.service.call_llm", boom)
        result = await get_chat_response("hi", empty_portfolio, [])
        assert result == MOCK_RESPONSE


class TestStructuredParsing:
    async def test_well_formed_response_parses(self, monkeypatch, empty_portfolio):
        monkeypatch.delenv("LLM_MOCK", raising=False)
        payload = {
            "message": "Buying 10 shares of AAPL for you.",
            "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
            "watchlist_changes": [{"ticker": "PYPL", "action": "add"}],
        }
        monkeypatch.setattr(
            "app.llm.service.call_llm", lambda messages: json.dumps(payload)
        )

        result = await get_chat_response("buy 10 aapl", empty_portfolio, [])

        assert isinstance(result, ChatResponse)
        assert result.message == "Buying 10 shares of AAPL for you."
        assert len(result.trades) == 1
        assert result.trades[0].ticker == "AAPL"
        assert result.trades[0].side == "buy"
        assert result.trades[0].quantity == 10
        assert len(result.watchlist_changes) == 1
        assert result.watchlist_changes[0].ticker == "PYPL"
        assert result.watchlist_changes[0].action == "add"

    async def test_well_formed_response_no_actions(self, monkeypatch, empty_portfolio):
        monkeypatch.delenv("LLM_MOCK", raising=False)
        payload = {"message": "You have no positions.", "trades": [], "watchlist_changes": []}
        monkeypatch.setattr(
            "app.llm.service.call_llm", lambda messages: json.dumps(payload)
        )

        result = await get_chat_response("how am I doing?", empty_portfolio, [])

        assert result.message == "You have no positions."
        assert result.trades == []
        assert result.watchlist_changes == []

    @pytest.mark.parametrize(
        "bad_payload",
        [
            "not json at all",
            "{}",
            json.dumps({"trades": []}),
            json.dumps({"message": "hi", "trades": [{"ticker": "AAPL", "side": "hold", "quantity": 1}]}),
            json.dumps({"message": "hi", "trades": [{"ticker": "AAPL", "side": "buy", "quantity": -5}]}),
            json.dumps(
                {"message": "hi", "watchlist_changes": [{"ticker": "AAPL", "action": "delete"}]}
            ),
        ],
    )
    async def test_malformed_response_returns_apologetic_fallback(
        self, monkeypatch, empty_portfolio, bad_payload
    ):
        monkeypatch.delenv("LLM_MOCK", raising=False)
        monkeypatch.setattr("app.llm.service.call_llm", lambda messages: bad_payload)

        result = await get_chat_response("do something", empty_portfolio, [])

        assert isinstance(result, ChatResponse)
        assert result.trades == []
        assert result.watchlist_changes == []
        assert result.message
        assert result.message != ""

    async def test_llm_call_raising_returns_apologetic_fallback(
        self, monkeypatch, empty_portfolio
    ):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        def boom(messages):
            raise RuntimeError("network is down")

        monkeypatch.setattr("app.llm.service.call_llm", boom)

        result = await get_chat_response("do something", empty_portfolio, [])

        assert isinstance(result, ChatResponse)
        assert result.trades == []
        assert result.watchlist_changes == []
        assert result.message
