from __future__ import annotations

DEFAULT_TICKERS = {"AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"}


def test_list_watchlist_default(client):
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    items = response.json()["watchlist"]
    assert {item["ticker"] for item in items} == DEFAULT_TICKERS
    # Simulator seeds the cache synchronously in start(), so prices are live immediately.
    assert all(item["price"] is not None for item in items)


def test_add_ticker(client):
    response = client.post("/api/watchlist", json={"ticker": "pypl"})
    assert response.status_code == 200
    assert response.json()["ticker"] == "PYPL"

    listing = client.get("/api/watchlist").json()["watchlist"]
    tickers = {item["ticker"] for item in listing}
    assert "PYPL" in tickers


def test_add_ticker_idempotent(client):
    client.post("/api/watchlist", json={"ticker": "PYPL"})
    response = client.post("/api/watchlist", json={"ticker": "PYPL"})
    assert response.status_code == 200

    listing = client.get("/api/watchlist").json()["watchlist"]
    assert sum(1 for item in listing if item["ticker"] == "PYPL") == 1


def test_remove_ticker(client):
    response = client.delete("/api/watchlist/AAPL")
    assert response.status_code == 200
    assert response.json() == {"removed": True, "ticker": "AAPL"}

    listing = client.get("/api/watchlist").json()["watchlist"]
    tickers = {item["ticker"] for item in listing}
    assert "AAPL" not in tickers


def test_remove_unknown_ticker_returns_404(client):
    response = client.delete("/api/watchlist/ZZZZ")
    assert response.status_code == 404
