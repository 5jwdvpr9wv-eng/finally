"""Entry point for the LLM chat module: ``get_chat_response``."""

from __future__ import annotations

import asyncio
import os

from app.db.models import ChatMessage

from .client import call_llm
from .models import ChatResponse, PortfolioContext
from .prompts import build_messages

# Canonical mock response, verbatim from PLAN.md §9. Deliberately action-free so
# E2E tests can control trade execution separately.
MOCK_RESPONSE = ChatResponse(
    message=(
        "I've analyzed your portfolio. You have $10,000 in cash and no open "
        "positions. I recommend starting with a diversified position — shall "
        "I buy 5 shares of AAPL?"
    ),
    trades=[],
    watchlist_changes=[],
)

FALLBACK_MESSAGE = (
    "Sorry, I ran into a problem processing that — could you try rephrasing "
    "or asking again?"
)
FALLBACK_RESPONSE = ChatResponse(message=FALLBACK_MESSAGE, trades=[], watchlist_changes=[])


def _is_mock_mode() -> bool:
    return os.environ.get("LLM_MOCK", "").strip().lower() == "true"


async def get_chat_response(
    user_message: str,
    portfolio_context: PortfolioContext,
    history: list[ChatMessage],
) -> ChatResponse:
    """Get FinAlly's structured response to a chat message.

    Builds the system prompt (portfolio context + last 20 turns of history),
    calls the LLM via LiteLLM/OpenRouter/Cerebras requesting structured output,
    and returns the parsed ``ChatResponse``. Never raises: if ``LLM_MOCK=true``
    the canonical mock response is returned with no network call; if the model
    call fails or returns output that doesn't match the schema, an apologetic
    fallback ``ChatResponse`` (empty trades/watchlist_changes) is returned
    instead.

    Assumes the caller only invokes this when ``OPENROUTER_API_KEY`` is set or
    mock mode is on — checking for a missing key is the route's responsibility
    (PLAN.md §5 specifies HTTP 503 in that case).
    """
    if _is_mock_mode():
        return MOCK_RESPONSE.model_copy(deep=True)

    messages = build_messages(portfolio_context, history, user_message)

    try:
        raw = await asyncio.to_thread(call_llm, messages)
        return ChatResponse.model_validate_json(raw)
    except Exception:
        return FALLBACK_RESPONSE.model_copy(deep=True)
