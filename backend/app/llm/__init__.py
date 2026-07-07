"""LLM chat module: builds prompts, calls OpenRouter/Cerebras, returns structured output.

Public API: ``get_chat_response`` plus the ``ChatResponse`` / ``PortfolioContext``
shapes it accepts and returns. See planning/LLM_CONTRACT.md for the full contract.
"""

from .models import (
    ChatResponse,
    PortfolioContext,
    PositionContext,
    TradeInstruction,
    WatchlistChangeInstruction,
    WatchlistItemContext,
)
from .service import get_chat_response

__all__ = [
    "ChatResponse",
    "PortfolioContext",
    "PositionContext",
    "TradeInstruction",
    "WatchlistChangeInstruction",
    "WatchlistItemContext",
    "get_chat_response",
]
