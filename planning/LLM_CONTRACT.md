# FinAlly LLM Chat Contract

`backend/app/llm/` owns prompt construction, the LiteLLM/OpenRouter/Cerebras call,
structured-output parsing, and mock mode. It does **not** touch the database or
execute trades/watchlist changes — the route (`backend/app/api/chat.py`) does
persistence and auto-execution after calling this module.

```python
from app.llm import get_chat_response, ChatResponse, PortfolioContext
```

---

## `get_chat_response`

```python
async def get_chat_response(
    user_message: str,
    portfolio_context: PortfolioContext,
    history: list[ChatMessage],
) -> ChatResponse
```

- `user_message` — the new user turn (plain text, not yet persisted by this
  function — the caller persists it).
- `portfolio_context` — a `PortfolioContext` describing current cash, positions
  with P&L, watchlist with live prices, and total value. See below for how to
  build one from the shape `get_portfolio_snapshot` already produces.
- `history` — the most recent chat turns, **oldest first** (the same order
  `get_recent_chat_messages` returns). Pass `limit=20` per PLAN.md §9; this
  function also defensively truncates to the last 20 itself, so passing more is
  harmless.
- Returns a `ChatResponse` (see below). **Never raises.**

### Behavior

1. If `LLM_MOCK` (env var, checked at call time) is `"true"` (case-insensitive),
   returns the canonical mock response below with **no network call** — no
   `OPENROUTER_API_KEY` needed.
2. Otherwise, builds a system prompt (FinAlly persona + portfolio context) plus
   the history plus `user_message`, calls the model via LiteLLM → OpenRouter
   with Cerebras as the inference provider, requesting structured output
   matching `ChatResponse`'s schema.
3. If the call succeeds and the output parses/validates against the schema,
   returns it as a `ChatResponse`.
4. If the call raises (network error, timeout, etc.) **or** the model's output
   fails to parse/validate (malformed JSON, missing `message`, invalid
   `side`/`action`, non-positive `quantity`, etc.), returns a fallback
   `ChatResponse` with an apologetic `message` and empty `trades` /
   `watchlist_changes`. This function never raises.

### Assumption this function makes

This function assumes it is only called when `OPENROUTER_API_KEY` is set
(non-empty) **or** `LLM_MOCK=true`. Checking for a missing key and returning
HTTP 503 (per PLAN.md §5) is the route's responsibility, done *before* calling
`get_chat_response` — this module does not check for the key itself.

---

## `ChatResponse` (return type — also the structured-output schema)

A pydantic `BaseModel` (`from app.llm import ChatResponse`):

```python
class TradeInstruction(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float  # must be > 0

class WatchlistChangeInstruction(BaseModel):
    ticker: str
    action: Literal["add", "remove"]

class ChatResponse(BaseModel):
    message: str
    trades: list[TradeInstruction] = []
    watchlist_changes: list[WatchlistChangeInstruction] = []
```

This matches PLAN.md §9's JSON schema exactly, just typed. Access fields as
attributes (`response.message`, `response.trades`, `trade.ticker`, `trade.side`,
`trade.quantity`), not via `dict.get(...)`. If you need a plain dict (e.g. for
logging), call `response.model_dump()`.

**Important for the route's current stub:** `app/api/chat.py`'s `_call_llm`
stub returns a plain dict and the caller does `llm_response.get("trades", [])`
/ `llm_response["message"]`. Once wired to this module, that code needs to
switch to attribute access (`llm_response.trades`, `llm_response.message`) and
convert each `TradeInstruction`/`WatchlistChangeInstruction` to whatever shape
`_apply_trades`/`_apply_watchlist_changes` expects (e.g.
`{"ticker": t.ticker, "side": t.side, "quantity": t.quantity}` or just pass the
attributes directly — both `_apply_trades` and `_apply_watchlist_changes`
already read `.get("ticker")` etc. on dicts, so either adapt those helpers to
accept attribute access or convert with `t.model_dump()` first).

---

## `PortfolioContext` (input — plain dataclasses, not pydantic)

```python
@dataclass(frozen=True, slots=True)
class PositionContext:
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

@dataclass(frozen=True, slots=True)
class WatchlistItemContext:
    ticker: str
    price: float | None  # None if no live price is cached yet

@dataclass(frozen=True, slots=True)
class PortfolioContext:
    cash: float
    total_value: float
    positions: list[PositionContext] = []
    watchlist: list[WatchlistItemContext] = []
```

### Building one from `get_portfolio_snapshot`

`app/services/trading.py:get_portfolio_snapshot(price_cache)` returns
`{"cash_balance", "positions": [{"ticker", "quantity", "avg_cost",
"current_price", "market_value", "unrealized_pl", "unrealized_pl_percent"}],
"total_value"}`, and `app/api/chat.py:_build_portfolio_context` adds a
`"watchlist": [{"ticker", "price"}]` key to that dict. A classmethod handles
this exact shape (including the `cash_balance` vs `cash` and `unrealized_pl`
vs `unrealized_pnl` naming differences) so the route doesn't need to
hand-translate field names:

```python
from app.llm import PortfolioContext

snapshot = {**get_portfolio_snapshot(price_cache), "watchlist": watchlist}
portfolio_context = PortfolioContext.from_snapshot(snapshot)
```

`from_snapshot` accepts either `cash` or `cash_balance`, and either
`unrealized_pl`/`unrealized_pl_percent` or
`unrealized_pnl`/`unrealized_pnl_percent` on each position dict.

---

## `history: list[ChatMessage]`

`ChatMessage` is `app.db.models.ChatMessage` (imported, not redefined) —
`id`, `user_id`, `role` (`"user"`/`"assistant"`), `content`, `actions`,
`created_at`. Pass the result of `get_recent_chat_messages(limit=20)` directly
(oldest-first, per `DB_CONTRACT.md`); do not include the new `user_message`
itself in `history` — it's passed separately and appended last.

---

## Mock mode

Set `LLM_MOCK=true` (env var). `get_chat_response` then returns, verbatim,
regardless of `user_message`/`portfolio_context`/`history`:

```json
{
  "message": "I've analyzed your portfolio. You have $10,000 in cash and no open positions. I recommend starting with a diversified position — shall I buy 5 shares of AAPL?",
  "trades": [],
  "watchlist_changes": []
}
```

No network call is made in this path — safe to use without an
`OPENROUTER_API_KEY`.

---

## Model / provider

`openrouter/openai/gpt-oss-120b` via LiteLLM, with `extra_body={"provider":
{"order": ["cerebras"]}}` to pin the Cerebras inference provider, per the
`cerebras` skill. `reasoning_effort="low"`. Structured output requested via
`response_format=ChatResponse` (pydantic), parsed with
`ChatResponse.model_validate_json(...)`.

---

## Module layout

- `app/llm/models.py` — `ChatResponse`, `TradeInstruction`,
  `WatchlistChangeInstruction`, `PortfolioContext`, `PositionContext`,
  `WatchlistItemContext`.
- `app/llm/prompts.py` — `build_messages(portfolio_context, history,
  user_message) -> list[dict]`, `format_portfolio_context(...)`.
- `app/llm/client.py` — `call_llm(messages: list[dict]) -> str`, the raw
  LiteLLM call (sync; wrapped in `asyncio.to_thread` by the service).
- `app/llm/service.py` — `get_chat_response` (the public entry point), the
  canonical mock response, and the fallback response.

## Tests

`backend/tests/llm/` — mock mode (exact canonical text, no network call),
well-formed structured parsing, malformed/invalid parsing (bad JSON, missing
fields, invalid enum values, non-positive quantity) falling back gracefully,
network/call failures falling back gracefully, and prompt construction
(portfolio context formatting, history ordering/truncation to last 20). All
LiteLLM calls are mocked — no real network access in tests.

Run: `cd backend && uv sync --extra dev && uv run --extra dev pytest -v`
(19/19 pass in `tests/llm/`; 156/156 pass across the whole backend suite as of
this writing).
