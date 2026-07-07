"""Trade execution and portfolio valuation logic.

Shared by the manual trade route (``POST /api/portfolio/trade``) and the LLM
chat route (``POST /api/chat``) so both paths validate and record trades
identically.
"""

from __future__ import annotations

from app.db import (
    delete_position,
    get_position,
    get_positions,
    get_user_profile,
    record_trade,
    set_cash_balance,
    upsert_position,
)
from app.market import PriceCache

_QUANTITY_EPSILON = 1e-9


class TradeError(Exception):
    """Raised when a trade fails validation (bad input, insufficient cash/shares)."""


def execute_trade(ticker: str, side: str, quantity: float, price_cache: PriceCache) -> dict:
    """Validate and execute a single market order, updating positions/cash/trade log.

    Returns the recorded trade as a dict. Raises TradeError on any validation
    failure (bad side, non-positive quantity, no live price, insufficient
    cash/shares) — callers turn this into an HTTP 400 or a chat-visible error.
    """
    ticker = ticker.strip().upper()
    if side not in ("buy", "sell"):
        raise TradeError(f"Invalid side '{side}'; must be 'buy' or 'sell'")
    if quantity <= 0:
        raise TradeError("Quantity must be positive")

    price = price_cache.get_price(ticker)
    if price is None:
        raise TradeError(f"No live price available for {ticker}")

    profile = get_user_profile()
    position = get_position(ticker)

    if side == "buy":
        cost = quantity * price
        if cost > profile.cash_balance + _QUANTITY_EPSILON:
            raise TradeError(
                f"Insufficient cash: need ${cost:.2f}, have ${profile.cash_balance:.2f}"
            )
        if position is None:
            new_quantity = quantity
            new_avg_cost = price
        else:
            new_quantity = position.quantity + quantity
            new_avg_cost = (
                position.quantity * position.avg_cost + quantity * price
            ) / new_quantity
        upsert_position(ticker, new_quantity, new_avg_cost)
        set_cash_balance(profile.cash_balance - cost)
    else:
        held = position.quantity if position else 0.0
        if position is None or quantity > held + _QUANTITY_EPSILON:
            raise TradeError(
                f"Insufficient shares: trying to sell {quantity}, hold {held} of {ticker}"
            )
        proceeds = quantity * price
        remaining = held - quantity
        if remaining <= _QUANTITY_EPSILON:
            delete_position(ticker)
        else:
            upsert_position(ticker, remaining, position.avg_cost)
        set_cash_balance(profile.cash_balance + proceeds)

    trade = record_trade(ticker, side, quantity, price)
    return trade.to_dict()


def get_portfolio_snapshot(price_cache: PriceCache) -> dict:
    """Assemble the full portfolio view: cash, positions with live P&L, total value."""
    profile = get_user_profile()
    positions = get_positions()

    position_dicts = []
    positions_value = 0.0
    for pos in positions:
        current_price = price_cache.get_price(pos.ticker)
        if current_price is None:
            current_price = pos.avg_cost

        market_value = pos.quantity * current_price
        cost_basis = pos.quantity * pos.avg_cost
        unrealized_pl = market_value - cost_basis
        unrealized_pl_percent = (unrealized_pl / cost_basis * 100) if cost_basis else 0.0

        positions_value += market_value
        position_dicts.append(
            {
                "ticker": pos.ticker,
                "quantity": pos.quantity,
                "avg_cost": round(pos.avg_cost, 4),
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_pl_percent": round(unrealized_pl_percent, 2),
            }
        )

    total_value = profile.cash_balance + positions_value
    return {
        "cash_balance": round(profile.cash_balance, 2),
        "positions": position_dicts,
        "total_value": round(total_value, 2),
    }


def compute_total_value(price_cache: PriceCache) -> float:
    """Cash + market value of all positions, for the periodic snapshot task."""
    profile = get_user_profile()
    positions = get_positions()
    positions_value = sum(
        pos.quantity * (price_cache.get_price(pos.ticker) or pos.avg_cost) for pos in positions
    )
    return round(profile.cash_balance + positions_value, 2)
