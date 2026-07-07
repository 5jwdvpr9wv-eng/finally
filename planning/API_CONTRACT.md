# FinAlly API Contract

Final request/response shapes for every backend endpoint, as implemented in
`backend/app/api/` and `backend/app/main.py`. All endpoints are same-origin
(`/api/*`); no CORS needed. All amounts are plain JSON numbers (floats),
already rounded to 2dp server-side except `quantity`/`avg_cost` which may
carry more precision for fractional (LLM-initiated) trades.

---

## System

### `GET /api/health`

```json
{ "status": "ok" }
```

---

## Market Data (built by Market Data Engineer, mounted in `main.py`)

### `GET /api/stream/prices` (SSE)

`text/event-stream`. Each event's `data:` payload is a JSON object keyed by
ticker:

```json
{
  "AAPL": {
    "ticker": "AAPL",
    "price": 190.5,
    "previous_price": 190.2,
    "timestamp": 1751000000.123,
    "change": 0.3,
    "change_percent": 0.1577,
    "direction": "up"
  }
}
```

---

## Portfolio

### `GET /api/portfolio`

```json
{
  "cash_balance": 8100.0,
  "positions": [
    {
      "ticker": "AAPL",
      "quantity": 10.0,
      "avg_cost": 190.0,
      "current_price": 192.5,
      "market_value": 1925.0,
      "unrealized_pl": 25.0,
      "unrealized_pl_percent": 1.32
    }
  ],
  "total_value": 10025.0
}
```

- `positions` is `[]` when flat. `current_price` falls back to `avg_cost` if
  the ticker has no live price yet (should not normally happen for held
  positions since a trade requires a live price to execute).
- `total_value = cash_balance + sum(market_value)`.

### `POST /api/portfolio/trade`

Request:

```json
{ "ticker": "AAPL", "quantity": 10, "side": "buy" }
```

- `quantity` must be a **positive whole number** here (manual trade bar).
  Fractional quantities are only accepted via the internal trade service used
  by `/api/chat` (LLM-initiated trades), not this endpoint.
- `side` must be `"buy"` or `"sell"`; anything else is a 422.

Success response (`200`) — the executed trade plus the fresh portfolio view;
a `portfolio_snapshots` row is recorded immediately after execution:

```json
{
  "trade": {
    "id": "5b3e...uuid",
    "user_id": "default",
    "ticker": "AAPL",
    "side": "buy",
    "quantity": 10.0,
    "price": 190.0,
    "executed_at": "2026-07-06T12:34:56Z"
  },
  "portfolio": { "...": "same shape as GET /api/portfolio" }
}
```

Failure response (`400`) — validation error, `detail` is a human-readable
string safe to surface directly to the user or relay through the LLM:

```json
{ "detail": "Insufficient cash: need $1900.00, have $500.00" }
```

Other 400 messages: `"Insufficient shares: trying to sell 5, hold 2 of AAPL"`,
`"No live price available for ZZZZ"`. A malformed request body (bad `side`,
non-integer/non-positive `quantity`) is a `422` from FastAPI's own validation.

### `GET /api/portfolio/history`

```json
{
  "snapshots": [
    { "id": "uuid", "user_id": "default", "total_value": 10000.0, "recorded_at": "2026-07-06T12:00:00Z" },
    { "id": "uuid", "user_id": "default", "total_value": 10025.0, "recorded_at": "2026-07-06T12:00:30Z" }
  ]
}
```

Chronological order (oldest first), ready to plot directly. `[]` when no
snapshot has been recorded yet.

---

## Watchlist

### `GET /api/watchlist`

```json
{
  "watchlist": [
    {
      "ticker": "AAPL",
      "added_at": "2026-07-06T00:00:00Z",
      "price": 190.5,
      "previous_price": 190.2,
      "change": 0.3,
      "change_percent": 0.16,
      "direction": "up"
    }
  ]
}
```

- Price fields are `null` if the ticker has no cache entry yet (e.g. just
  added, before the next simulator/poll tick — normally sub-second).

### `POST /api/watchlist`

Request: `{ "ticker": "pypl" }` (case-insensitive, whitespace-trimmed).

Response (`200`, idempotent — adding an already-watched ticker returns the
existing entry rather than erroring):

```json
{ "ticker": "PYPL", "added_at": "2026-07-06T12:34:56Z" }
```

Also registers the ticker with the live market data source
(`market_source.add_ticker`) so it starts streaming immediately.

### `DELETE /api/watchlist/{ticker}`

Response (`200`):

```json
{ "removed": true, "ticker": "AAPL" }
```

`404` if the ticker wasn't on the watchlist:
`{ "detail": "ZZZZ is not on the watchlist" }`.

---

## Chat

### `GET /api/chat/history`

Last 50 messages, chronological (oldest first):

```json
{
  "messages": [
    { "id": "uuid", "user_id": "default", "role": "user", "content": "buy 5 AAPL", "actions": null, "created_at": "..." },
    { "id": "uuid", "user_id": "default", "role": "assistant", "content": "Done — bought 5 shares of AAPL at $190.00.", "actions": { "trades": [...], "watchlist_changes": [...] }, "created_at": "..." }
  ]
}
```

### `POST /api/chat`

Request: `{ "message": "buy 5 shares of AAPL" }`

- If `OPENROUTER_API_KEY` is unset/empty and `LLM_MOCK` is not `"true"` →
  `503 { "detail": "OPENROUTER_API_KEY is not configured" }` (checked before
  the user message is persisted).
- Otherwise the user message is saved, portfolio + watchlist context and the
  last 20 messages are assembled, and the LLM (or, if `LLM_MOCK=true`, the
  canonical mock response from PLAN.md §9) is called.
- Any `trades`/`watchlist_changes` the LLM returns are executed through the
  **same** `app.services.trading.execute_trade` / watchlist repository calls
  used by the manual endpoints above — same validation, same errors.

Response (`200`):

```json
{
  "message": "Bought 5 shares of AAPL at $190.00. Anything else?",
  "actions": {
    "trades": [
      {
        "status": "executed",
        "id": "uuid",
        "user_id": "default",
        "ticker": "AAPL",
        "side": "buy",
        "quantity": 5.0,
        "price": 190.0,
        "executed_at": "2026-07-06T12:34:56Z"
      }
    ],
    "watchlist_changes": [
      { "status": "executed", "ticker": "PYPL", "action": "add" }
    ]
  },
  "created_at": "2026-07-06T12:34:56Z"
}
```

- A failed trade/watchlist change (e.g. insufficient cash) appears in the same
  array with `"status": "failed"` and an `"error"` string instead of the
  executed fields, so the LLM's `message` can acknowledge it. Example:
  `{ "status": "failed", "ticker": "TSLA", "side": "buy", "quantity": 1000, "error": "Insufficient cash: ..." }`.

The LLM call itself (`app.llm.get_chat_response`, per
`planning/LLM_CONTRACT.md`) never raises: on `LLM_MOCK=true` it returns the
canonical mock response with no network call; on a real call failure or
schema-invalid output it returns an apologetic fallback message with empty
`trades`/`watchlist_changes`. The 503 above (missing `OPENROUTER_API_KEY`,
non-mock) is the only error path the chat route itself returns.
