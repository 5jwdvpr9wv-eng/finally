from __future__ import annotations


def _get_price(client, ticker: str) -> float:
    response = client.get("/api/watchlist")
    items = response.json()["watchlist"]
    match = next(item for item in items if item["ticker"] == ticker)
    assert match["price"] is not None
    return match["price"]


def test_get_portfolio_starts_empty_with_seed_cash(client):
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] == 10000.0
    assert body["positions"] == []
    assert body["total_value"] == 10000.0


def test_buy_trade_success(client):
    price = _get_price(client, "AAPL")

    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["trade"]["ticker"] == "AAPL"
    assert body["trade"]["side"] == "buy"
    assert body["trade"]["quantity"] == 10

    portfolio = body["portfolio"]
    assert portfolio["cash_balance"] == round(10000.0 - 10 * price, 2)
    assert len(portfolio["positions"]) == 1
    position = portfolio["positions"][0]
    assert position["ticker"] == "AAPL"
    assert position["quantity"] == 10
    assert position["avg_cost"] == price


def test_buy_averages_cost_on_second_buy(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"}
    )
    assert response.status_code == 200
    position = response.json()["portfolio"]["positions"][0]
    assert position["quantity"] == 20


def test_sell_full_position_removes_it(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "buy"})
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "sell"}
    )
    assert response.status_code == 200
    portfolio = response.json()["portfolio"]
    assert portfolio["positions"] == []
    assert portfolio["cash_balance"] == 10000.0


def test_sell_partial_position_keeps_avg_cost(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 4, "side": "sell"}
    )
    assert response.status_code == 200
    position = response.json()["portfolio"]["positions"][0]
    assert position["quantity"] == 6


def test_buy_insufficient_cash_returns_400(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "NVDA", "quantity": 100, "side": "buy"}
    )
    assert response.status_code == 400
    assert "insufficient cash" in response.json()["detail"].lower()


def test_sell_insufficient_shares_returns_400(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "sell"}
    )
    assert response.status_code == 400
    assert "insufficient shares" in response.json()["detail"].lower()


def test_trade_invalid_side_returns_422(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "hold"}
    )
    assert response.status_code == 422


def test_trade_fractional_quantity_returns_422(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1.5, "side": "buy"}
    )
    assert response.status_code == 422


def test_trade_unknown_ticker_returns_400(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "ZZZZ", "quantity": 1, "side": "buy"}
    )
    assert response.status_code == 400
    assert "no live price" in response.json()["detail"].lower()


def test_history_starts_empty_and_grows_after_trade(client):
    empty = client.get("/api/portfolio/history").json()["snapshots"]
    assert empty == []

    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})

    snapshots = client.get("/api/portfolio/history").json()["snapshots"]
    assert len(snapshots) == 1
