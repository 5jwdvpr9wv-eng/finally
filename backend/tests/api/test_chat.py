from __future__ import annotations

from app.llm import ChatResponse, TradeInstruction, WatchlistChangeInstruction


def test_chat_history_starts_empty(client):
    response = client.get("/api/chat/history")
    assert response.status_code == 200
    assert response.json() == {"messages": []}


def test_chat_without_key_or_mock_returns_503(client, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MOCK", raising=False)

    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 503
    assert "OPENROUTER_API_KEY" in response.json()["detail"]

    # The user's message should not be persisted if we bail out before calling the LLM.
    history = client.get("/api/chat/history").json()["messages"]
    assert history == []


def test_chat_mock_mode_returns_canonical_response_and_persists_history(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    response = client.post("/api/chat", json={"message": "hi there"})
    assert response.status_code == 200
    body = response.json()
    assert "cash" in body["message"].lower()
    assert body["actions"] == {"trades": [], "watchlist_changes": []}

    history = client.get("/api/chat/history").json()["messages"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hi there"
    assert history[1]["role"] == "assistant"
    assert history[1]["actions"] == {"trades": [], "watchlist_changes": []}


def test_chat_executes_llm_trade_and_watchlist_change(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    async def fake_get_chat_response(user_message, portfolio_context, history):
        return ChatResponse(
            message="Bought 1 share of AAPL and added TSLA to your watchlist.",
            trades=[TradeInstruction(ticker="AAPL", side="buy", quantity=1)],
            watchlist_changes=[WatchlistChangeInstruction(ticker="tsla", action="add")],
        )

    monkeypatch.setattr("app.api.chat.get_chat_response", fake_get_chat_response)

    response = client.post("/api/chat", json={"message": "buy 1 AAPL and watch TSLA"})
    assert response.status_code == 200
    actions = response.json()["actions"]

    assert len(actions["trades"]) == 1
    assert actions["trades"][0]["status"] == "executed"
    assert actions["trades"][0]["ticker"] == "AAPL"

    assert actions["watchlist_changes"] == [
        {"status": "executed", "ticker": "TSLA", "action": "add"}
    ]

    portfolio = client.get("/api/portfolio").json()
    assert portfolio["positions"][0]["ticker"] == "AAPL"
    assert portfolio["positions"][0]["quantity"] == 1


def test_chat_reports_failed_llm_trade_without_raising(client, monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")

    async def fake_get_chat_response(user_message, portfolio_context, history):
        return ChatResponse(
            message="Tried to buy more NVDA than you can afford.",
            trades=[TradeInstruction(ticker="NVDA", side="buy", quantity=1000)],
            watchlist_changes=[],
        )

    monkeypatch.setattr("app.api.chat.get_chat_response", fake_get_chat_response)

    response = client.post("/api/chat", json={"message": "buy 1000 NVDA"})
    assert response.status_code == 200
    trade_result = response.json()["actions"]["trades"][0]
    assert trade_result["status"] == "failed"
    assert "insufficient cash" in trade_result["error"].lower()

    portfolio = client.get("/api/portfolio").json()
    assert portfolio["positions"] == []
