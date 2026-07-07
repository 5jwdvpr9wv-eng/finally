"""Data models for the LLM chat module.

``ChatResponse`` (and its nested trade/watchlist-change models) mirror the
structured output schema in PLAN.md §9 and are what the LLM is asked to
produce. ``PortfolioContext`` and friends are plain input dataclasses the
caller builds to describe portfolio state for the prompt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


class TradeInstruction(BaseModel):
    """One trade the LLM wants auto-executed."""

    ticker: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)


class WatchlistChangeInstruction(BaseModel):
    """One watchlist modification the LLM wants auto-executed."""

    ticker: str
    action: Literal["add", "remove"]


class ChatResponse(BaseModel):
    """The complete structured response returned by ``get_chat_response``."""

    message: str
    trades: list[TradeInstruction] = Field(default_factory=list)
    watchlist_changes: list[WatchlistChangeInstruction] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PositionContext:
    """One open position, with P&L computed against the current price."""

    ticker: str
    quantity: float
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


@dataclass(frozen=True, slots=True)
class WatchlistItemContext:
    """One watchlist ticker with its latest known price."""

    ticker: str
    price: float | None


@dataclass(frozen=True, slots=True)
class PortfolioContext:
    """Everything the prompt needs to know about the user's portfolio."""

    cash: float
    total_value: float
    positions: list[PositionContext] = field(default_factory=list)
    watchlist: list[WatchlistItemContext] = field(default_factory=list)

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> PortfolioContext:
        """Build from the dict shape produced by ``get_portfolio_snapshot`` (plus a
        ``"watchlist"`` key), e.g. ``{**get_portfolio_snapshot(cache), "watchlist": [...]}``.

        Accepts either ``cash`` or ``cash_balance``, and either
        ``unrealized_pl``/``unrealized_pl_percent`` or
        ``unrealized_pnl``/``unrealized_pnl_percent`` on each position, so callers
        don't need to rename keys first.
        """
        positions = [
            PositionContext(
                ticker=p["ticker"],
                quantity=p["quantity"],
                avg_cost=p["avg_cost"],
                current_price=p["current_price"],
                unrealized_pnl=p.get("unrealized_pl", p.get("unrealized_pnl")),
                unrealized_pnl_percent=p.get(
                    "unrealized_pl_percent", p.get("unrealized_pnl_percent")
                ),
            )
            for p in snapshot.get("positions", [])
        ]
        watchlist = [
            WatchlistItemContext(ticker=w["ticker"], price=w.get("price"))
            for w in snapshot.get("watchlist", [])
        ]
        return cls(
            cash=snapshot.get("cash", snapshot.get("cash_balance")),
            total_value=snapshot["total_value"],
            positions=positions,
            watchlist=watchlist,
        )
