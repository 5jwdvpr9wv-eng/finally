# FinAlly Database Contract

The database layer (`backend/app/db/`) is the **only** sanctioned way to touch
SQLite. Do not write raw SQL in routes, the LLM module, or anywhere else —
import and call these repository functions.

```python
from app.db import (
    get_user_profile, set_cash_balance,
    get_watchlist, add_to_watchlist, remove_from_watchlist, is_watched,
    get_positions, get_position, upsert_position, delete_position,
    record_trade, get_trades,
    record_snapshot, get_snapshots,
    save_chat_message, get_recent_chat_messages,
)
```

All functions are **synchronous** (`sqlite3` stdlib). Each opens its own
connection, runs one operation, commits, and closes. Safe to call from FastAPI
route handlers. For heavy call sites in async code, wrap in
`await asyncio.to_thread(...)` if you find blocking matters (individual calls are
sub-millisecond, so usually not needed).

Every function takes an optional `user_id: str = "default"` last parameter. The
app is single-user today (`"default"`); the parameter exists so multi-user works
later without schema changes. **Omit it** unless you specifically need another
user.

Tickers passed to watchlist/position/trade functions are normalized to
UPPERCASE and stripped, so `"aapl"`, `" AAPL "`, and `"AAPL"` are equivalent.

---

## Setup & lazy init

- The DB is created and seeded **on first use** — no migration step, no manual
  init call. The first repository call creates all tables and, if the DB is
  empty, seeds the default profile ($10,000 cash) and 10 watchlist tickers
  (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX).
- Runtime DB path: `<project_root>/db/finally.db`, overridable via the
  `FINALLY_DB_PATH` environment variable (set this to the volume mount path in
  Docker).
- **Tests / programmatic path override:** `from app.db import configure;
  configure(path)` before any repository call. Point it at a temp file. See
  `backend/tests/db/conftest.py` for the fixture pattern (`temp_db`).

---

## Row models (`app.db.models`)

All are frozen dataclasses with a `.to_dict()` for JSON/API serialization.

| Model | Fields |
|---|---|
| `UserProfile` | `id: str`, `cash_balance: float`, `created_at: str` |
| `WatchlistEntry` | `user_id: str`, `ticker: str`, `added_at: str` |
| `Position` | `id: str`, `user_id: str`, `ticker: str`, `quantity: float`, `avg_cost: float`, `updated_at: str` |
| `Trade` | `id: str`, `user_id: str`, `ticker: str`, `side: str`, `quantity: float`, `price: float`, `executed_at: str` |
| `PortfolioSnapshot` | `id: str`, `user_id: str`, `total_value: float`, `recorded_at: str` |
| `ChatMessage` | `id: str`, `user_id: str`, `role: str`, `content: str`, `actions: dict \| list \| None`, `created_at: str` |

All timestamps are ISO-8601 UTC strings, e.g. `"2026-07-06T12:34:56Z"`. All
`id` fields (except `UserProfile.id` which is the user_id, and `WatchlistEntry`
which has no id) are UUID4 strings.

---

## users_profile

### `get_user_profile(user_id="default") -> UserProfile`
Returns the user's profile. If the row doesn't exist, creates it with the
default `$10,000` cash balance first. Never returns None.

### `set_cash_balance(cash_balance: float, user_id="default") -> UserProfile`
Sets cash to an **absolute** value (not a delta). Creates the profile row first
if missing. Returns the updated `UserProfile`. Trade logic computes the new
balance and passes it here.

---

## watchlist

### `get_watchlist(user_id="default") -> list[WatchlistEntry]`
All watched tickers, ordered oldest-added first (then alphabetical).

### `add_to_watchlist(ticker: str, user_id="default") -> WatchlistEntry`
Idempotent. Adds the ticker if absent; returns the existing or newly-created
entry either way. Ticker uppercased/stripped.

### `remove_from_watchlist(ticker: str, user_id="default") -> bool`
Removes the ticker. Returns `True` if a row was deleted, `False` if it wasn't on
the list.

### `is_watched(ticker: str, user_id="default") -> bool`
Whether the ticker is currently on the watchlist.

---

## positions

One row per `(user_id, ticker)` — enforced by a `UNIQUE` constraint.

### `get_positions(user_id="default") -> list[Position]`
All open positions, alphabetical by ticker. Empty list if none.

### `get_position(ticker: str, user_id="default") -> Position | None`
The position for one ticker, or `None` if not held.

### `upsert_position(ticker: str, quantity: float, avg_cost: float, user_id="default") -> Position`
Insert-or-update with **absolute** values. This does **no trade math** — the
caller computes the post-trade `quantity` and `avg_cost` and passes them in.
On an existing position the row `id` is preserved. Returns the resulting
`Position`. (For a full sell, call `delete_position` instead of upserting
quantity 0.)

### `delete_position(ticker: str, user_id="default") -> bool`
Deletes the position (e.g. fully sold). Returns `True` if a row was deleted.

**Typical buy flow (caller's responsibility):**
```python
pos = get_position("AAPL")
if pos is None:
    upsert_position("AAPL", qty, price)
else:
    new_qty = pos.quantity + qty
    new_cost = (pos.quantity * pos.avg_cost + qty * price) / new_qty
    upsert_position("AAPL", new_qty, new_cost)
record_trade("AAPL", "buy", qty, price)
set_cash_balance(profile.cash_balance - qty * price)
```

---

## trades (append-only log)

### `record_trade(ticker: str, side: str, quantity: float, price: float, user_id="default") -> Trade`
Appends one trade. `side` **must** be `"buy"` or `"sell"` (raises `ValueError`
otherwise). `quantity` may be fractional. Returns the created `Trade`. This only
logs the trade — it does not update positions or cash; do those via
`upsert_position`/`delete_position` and `set_cash_balance`.

### `get_trades(user_id="default", limit: int | None = None) -> list[Trade]`
Trades **most-recent-first**. `limit` caps the count (returns the newest N).

---

## portfolio_snapshots (for the P&L chart)

### `record_snapshot(total_value: float, user_id="default") -> PortfolioSnapshot`
Appends a total-portfolio-value data point. Call every ~30s from a background
task and immediately after each trade (per PLAN §7). Returns the snapshot.

### `get_snapshots(user_id="default", limit: int | None = None) -> list[PortfolioSnapshot]`
Snapshots in **chronological order (oldest first)** — ready to plot. With
`limit`, returns the most recent N, still oldest-first.

---

## chat_messages

### `save_chat_message(role: str, content: str, actions: dict | list | None = None, user_id="default") -> ChatMessage`
Persists one message. `role` **must** be `"user"` or `"assistant"` (raises
`ValueError` otherwise). `actions` (executed trades / watchlist changes for
assistant turns) is JSON-serialized for storage and returned parsed on the
model; pass `None` for user messages. Returns the created `ChatMessage`.

### `get_recent_chat_messages(user_id="default", limit: int = 20) -> list[ChatMessage]`
The most recent `limit` messages in **chronological order (oldest first)**, so
they read top-to-bottom as a conversation. Use `limit=20` for LLM context (the
default, per PLAN §9) and `limit=50` for the `/api/chat/history` endpoint (PLAN
§8). `actions` comes back as the parsed dict/list (or `None`).

---

## Notes for integrators

- **No confirmation / no validation of business rules here.** The repository
  stores what you give it. Cash-sufficiency, share-sufficiency, and trade math
  live in the Backend Engineer's portfolio/trade service, which orchestrates
  these functions.
- **Constraints that will raise `sqlite3.IntegrityError`:** duplicate
  `(user_id, ticker)` in `positions`, bad `side`/`role` values (also guarded by
  `ValueError` in the functions). Let these surface as 4xx/5xx in routes as
  appropriate.
- **Thread-safety:** connections are opened per-call with
  `check_same_thread=False` and closed immediately, so concurrent route handlers
  and the background snapshot task are safe. SQLite's own write lock serializes
  writers.
