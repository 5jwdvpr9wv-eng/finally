"""Typed repository functions — the only sanctioned way to touch the database.

Every function opens a connection via ``get_connection()``, runs one logical
operation, and returns dataclass models (or plain values). No SQL lives outside
this module; routes and the LLM layer call these functions instead.

All functions accept ``user_id`` (default ``"default"``) so the schema is
multi-user-ready even though the app is single-user today.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from .connection import get_connection
from .models import (
    ChatMessage,
    PortfolioSnapshot,
    Position,
    Trade,
    UserProfile,
    WatchlistEntry,
)

DEFAULT_USER_ID = "default"


def _now_iso() -> str:
    """Current UTC time as ISO-8601 (e.g. '2026-07-06T12:34:56Z')."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id() -> str:
    return str(uuid.uuid4())


# --------------------------------------------------------------------------- #
# Row -> model mappers
# --------------------------------------------------------------------------- #


def _to_user_profile(row: sqlite3.Row) -> UserProfile:
    return UserProfile(
        id=row["id"],
        cash_balance=row["cash_balance"],
        created_at=row["created_at"],
    )


def _to_watchlist_entry(row: sqlite3.Row) -> WatchlistEntry:
    return WatchlistEntry(
        user_id=row["user_id"],
        ticker=row["ticker"],
        added_at=row["added_at"],
    )


def _to_position(row: sqlite3.Row) -> Position:
    return Position(
        id=row["id"],
        user_id=row["user_id"],
        ticker=row["ticker"],
        quantity=row["quantity"],
        avg_cost=row["avg_cost"],
        updated_at=row["updated_at"],
    )


def _to_trade(row: sqlite3.Row) -> Trade:
    return Trade(
        id=row["id"],
        user_id=row["user_id"],
        ticker=row["ticker"],
        side=row["side"],
        quantity=row["quantity"],
        price=row["price"],
        executed_at=row["executed_at"],
    )


def _to_snapshot(row: sqlite3.Row) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        id=row["id"],
        user_id=row["user_id"],
        total_value=row["total_value"],
        recorded_at=row["recorded_at"],
    )


def _to_chat_message(row: sqlite3.Row) -> ChatMessage:
    raw = row["actions"]
    return ChatMessage(
        id=row["id"],
        user_id=row["user_id"],
        role=row["role"],
        content=row["content"],
        actions=json.loads(raw) if raw is not None else None,
        created_at=row["created_at"],
    )


# --------------------------------------------------------------------------- #
# users_profile
# --------------------------------------------------------------------------- #


def get_user_profile(user_id: str = DEFAULT_USER_ID) -> UserProfile:
    """Return the user's profile, creating it with default cash if absent."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
                (user_id, 10000.0, _now_iso()),
            )
            row = conn.execute(
                "SELECT * FROM users_profile WHERE id = ?", (user_id,)
            ).fetchone()
        return _to_user_profile(row)


def set_cash_balance(cash_balance: float, user_id: str = DEFAULT_USER_ID) -> UserProfile:
    """Set the user's cash balance to an absolute value. Returns the updated profile."""
    get_user_profile(user_id)  # ensure the row exists
    with get_connection() as conn:
        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
            (cash_balance, user_id),
        )
        row = conn.execute(
            "SELECT * FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        return _to_user_profile(row)


# --------------------------------------------------------------------------- #
# watchlist
# --------------------------------------------------------------------------- #


def get_watchlist(user_id: str = DEFAULT_USER_ID) -> list[WatchlistEntry]:
    """Return the user's watchlist entries, oldest-added first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? ORDER BY added_at ASC, ticker ASC",
            (user_id,),
        ).fetchall()
        return [_to_watchlist_entry(r) for r in rows]


def add_to_watchlist(ticker: str, user_id: str = DEFAULT_USER_ID) -> WatchlistEntry:
    """Add a ticker to the watchlist. Idempotent — returns the existing or new entry.

    Tickers are normalized to uppercase.
    """
    ticker = ticker.upper().strip()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, ticker, added_at) VALUES (?, ?, ?)",
            (user_id, ticker, _now_iso()),
        )
        row = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return _to_watchlist_entry(row)


def remove_from_watchlist(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Remove a ticker from the watchlist. Returns True if a row was deleted."""
    ticker = ticker.upper().strip()
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        return cur.rowcount > 0


def is_watched(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Return True if the ticker is on the user's watchlist."""
    ticker = ticker.upper().strip()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return row is not None


# --------------------------------------------------------------------------- #
# positions
# --------------------------------------------------------------------------- #


def get_positions(user_id: str = DEFAULT_USER_ID) -> list[Position]:
    """Return all of the user's open positions, alphabetical by ticker."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM positions WHERE user_id = ? ORDER BY ticker ASC",
            (user_id,),
        ).fetchall()
        return [_to_position(r) for r in rows]


def get_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> Position | None:
    """Return the user's position for a ticker, or None if not held."""
    ticker = ticker.upper().strip()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return _to_position(row) if row else None


def upsert_position(
    ticker: str,
    quantity: float,
    avg_cost: float,
    user_id: str = DEFAULT_USER_ID,
) -> Position:
    """Insert or update the position for a ticker, setting absolute values.

    This does not do trade math — it stores the given quantity and avg_cost as
    the new truth. Callers compute the post-trade quantity/cost and pass them in.
    Returns the resulting Position.
    """
    ticker = ticker.upper().strip()
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id, ticker) DO UPDATE SET
                quantity = excluded.quantity,
                avg_cost = excluded.avg_cost,
                updated_at = excluded.updated_at
            """,
            (_new_id(), user_id, ticker, quantity, avg_cost, now),
        )
        row = conn.execute(
            "SELECT * FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return _to_position(row)


def delete_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Delete a position (e.g. when fully sold). Returns True if a row was deleted."""
    ticker = ticker.upper().strip()
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        return cur.rowcount > 0


# --------------------------------------------------------------------------- #
# trades
# --------------------------------------------------------------------------- #


def record_trade(
    ticker: str,
    side: str,
    quantity: float,
    price: float,
    user_id: str = DEFAULT_USER_ID,
) -> Trade:
    """Append a trade to the log. ``side`` must be 'buy' or 'sell'. Returns the Trade."""
    ticker = ticker.upper().strip()
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    trade = Trade(
        id=_new_id(),
        user_id=user_id,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=price,
        executed_at=_now_iso(),
    )
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.id,
                trade.user_id,
                trade.ticker,
                trade.side,
                trade.quantity,
                trade.price,
                trade.executed_at,
            ),
        )
        return trade


def get_trades(
    user_id: str = DEFAULT_USER_ID,
    limit: int | None = None,
) -> list[Trade]:
    """Return the user's trades, most recent first. ``limit`` caps the count."""
    sql = "SELECT * FROM trades WHERE user_id = ? ORDER BY executed_at DESC, rowid DESC"
    params: tuple = (user_id,)
    if limit is not None:
        sql += " LIMIT ?"
        params = (user_id, limit)
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_to_trade(r) for r in rows]


# --------------------------------------------------------------------------- #
# portfolio_snapshots
# --------------------------------------------------------------------------- #


def record_snapshot(
    total_value: float,
    user_id: str = DEFAULT_USER_ID,
) -> PortfolioSnapshot:
    """Append a portfolio-value snapshot. Returns the created snapshot."""
    snapshot = PortfolioSnapshot(
        id=_new_id(),
        user_id=user_id,
        total_value=total_value,
        recorded_at=_now_iso(),
    )
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (snapshot.id, snapshot.user_id, snapshot.total_value, snapshot.recorded_at),
        )
        return snapshot


def get_snapshots(
    user_id: str = DEFAULT_USER_ID,
    limit: int | None = None,
) -> list[PortfolioSnapshot]:
    """Return portfolio snapshots in chronological order (oldest first) for charting.

    When ``limit`` is given, the most recent ``limit`` snapshots are returned,
    still in chronological order.
    """
    with get_connection() as conn:
        if limit is None:
            rows = conn.execute(
                "SELECT * FROM portfolio_snapshots WHERE user_id = ? "
                "ORDER BY recorded_at ASC, rowid ASC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ("
                "  SELECT *, rowid AS _rid FROM portfolio_snapshots WHERE user_id = ? "
                "  ORDER BY recorded_at DESC, _rid DESC LIMIT ?"
                ") ORDER BY recorded_at ASC, _rid ASC",
                (user_id, limit),
            ).fetchall()
        return [_to_snapshot(r) for r in rows]


# --------------------------------------------------------------------------- #
# chat_messages
# --------------------------------------------------------------------------- #


def save_chat_message(
    role: str,
    content: str,
    actions: dict | list | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> ChatMessage:
    """Persist a chat message. ``role`` must be 'user' or 'assistant'.

    ``actions`` (executed trades / watchlist changes) is JSON-serialized for
    storage and returned parsed on the resulting model.
    """
    if role not in ("user", "assistant"):
        raise ValueError(f"role must be 'user' or 'assistant', got {role!r}")
    message = ChatMessage(
        id=_new_id(),
        user_id=user_id,
        role=role,
        content=content,
        actions=actions,
        created_at=_now_iso(),
    )
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.user_id,
                message.role,
                message.content,
                json.dumps(actions) if actions is not None else None,
                message.created_at,
            ),
        )
        return message


def get_recent_chat_messages(
    user_id: str = DEFAULT_USER_ID,
    limit: int = 20,
) -> list[ChatMessage]:
    """Return the most recent ``limit`` chat messages in chronological order.

    The newest ``limit`` rows are selected, then returned oldest-first so they
    read top-to-bottom as a conversation. Used both for LLM context (limit=20)
    and the chat-history endpoint (limit=50).
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ("
            "  SELECT *, rowid AS _rid FROM chat_messages WHERE user_id = ? "
            "  ORDER BY created_at DESC, _rid DESC LIMIT ?"
            ") ORDER BY created_at ASC, _rid ASC",
            (user_id, limit),
        ).fetchall()
        return [_to_chat_message(r) for r in rows]
