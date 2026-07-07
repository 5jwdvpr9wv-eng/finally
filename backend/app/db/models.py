"""Typed row models for the FinAlly database.

Each dataclass mirrors one table. Repository functions return these instead of
raw sqlite3.Row objects so callers get attribute access and type hints. All
carry a ``to_dict()`` for JSON / API serialization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserProfile:
    """A row of users_profile — the user's cash balance and creation time."""

    id: str
    cash_balance: float
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cash_balance": self.cash_balance,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class WatchlistEntry:
    """A row of watchlist — one ticker the user is watching."""

    user_id: str
    ticker: str
    added_at: str

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "ticker": self.ticker,
            "added_at": self.added_at,
        }


@dataclass(frozen=True, slots=True)
class Position:
    """A row of positions — a current holding for one ticker."""

    id: str
    user_id: str
    ticker: str
    quantity: float
    avg_cost: float
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True, slots=True)
class Trade:
    """A row of trades — one executed buy or sell in the append-only log."""

    id: str
    user_id: str
    ticker: str
    side: str  # "buy" or "sell"
    quantity: float
    price: float
    executed_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "executed_at": self.executed_at,
        }


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """A row of portfolio_snapshots — total portfolio value at a point in time."""

    id: str
    user_id: str
    total_value: float
    recorded_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_value": self.total_value,
            "recorded_at": self.recorded_at,
        }


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A row of chat_messages — one turn of the LLM conversation.

    ``actions`` is the parsed JSON stored in the table (typically a dict of
    executed trades / watchlist changes), or None for user messages.
    """

    id: str
    user_id: str
    role: str  # "user" or "assistant"
    content: str
    actions: dict | list | None
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "actions": self.actions,
            "created_at": self.created_at,
        }
