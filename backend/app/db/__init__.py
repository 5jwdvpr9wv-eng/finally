"""Database subsystem for FinAlly.

SQLite with lazy init-on-first-use. Import the repository functions and row
models from here; do not write SQL elsewhere in the codebase.

    from app.db import (
        get_user_profile, set_cash_balance,
        get_watchlist, add_to_watchlist, remove_from_watchlist,
        get_positions, upsert_position, record_trade,
        save_chat_message, get_recent_chat_messages,
    )

Tests point at a temp database with ``configure(path)`` before calling any
repository function.
"""

from .connection import configure, get_connection
from .models import (
    ChatMessage,
    PortfolioSnapshot,
    Position,
    Trade,
    UserProfile,
    WatchlistEntry,
)
from .repository import (
    DEFAULT_USER_ID,
    add_to_watchlist,
    delete_position,
    get_position,
    get_positions,
    get_recent_chat_messages,
    get_snapshots,
    get_trades,
    get_user_profile,
    get_watchlist,
    is_watched,
    record_snapshot,
    record_trade,
    remove_from_watchlist,
    save_chat_message,
    set_cash_balance,
    upsert_position,
)

__all__ = [
    # connection / config
    "configure",
    "get_connection",
    # constants
    "DEFAULT_USER_ID",
    # models
    "UserProfile",
    "WatchlistEntry",
    "Position",
    "Trade",
    "PortfolioSnapshot",
    "ChatMessage",
    # users_profile
    "get_user_profile",
    "set_cash_balance",
    # watchlist
    "get_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "is_watched",
    # positions
    "get_positions",
    "get_position",
    "upsert_position",
    "delete_position",
    # trades
    "record_trade",
    "get_trades",
    # snapshots
    "record_snapshot",
    "get_snapshots",
    # chat
    "save_chat_message",
    "get_recent_chat_messages",
]
