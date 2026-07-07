"""Chat routes: conversation history and the LLM-driven assistant turn."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import (
    add_to_watchlist,
    get_recent_chat_messages,
    get_watchlist,
    remove_from_watchlist,
    save_chat_message,
)
from app.llm import (
    PortfolioContext,
    TradeInstruction,
    WatchlistChangeInstruction,
    get_chat_response,
)
from app.market import PriceCache
from app.services.trading import TradeError, execute_trade, get_portfolio_snapshot

from .deps import get_price_cache

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_HISTORY_LIMIT = 50
LLM_CONTEXT_LIMIT = 20


class ChatRequest(BaseModel):
    message: str


@router.get("/history")
async def chat_history() -> dict:
    messages = get_recent_chat_messages(limit=CHAT_HISTORY_LIMIT)
    return {"messages": [m.to_dict() for m in messages]}


@router.post("")
async def post_chat(
    body: ChatRequest, price_cache: PriceCache = Depends(get_price_cache)
) -> dict:
    mock_mode = os.environ.get("LLM_MOCK", "false").strip().lower() == "true"
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key and not mock_mode:
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY is not configured")

    save_chat_message("user", body.message)

    portfolio_context = _build_portfolio_context(price_cache)
    history = get_recent_chat_messages(limit=LLM_CONTEXT_LIMIT)
    llm_response = await get_chat_response(body.message, portfolio_context, history)

    executed_trades = _apply_trades(llm_response.trades, price_cache)
    executed_watchlist_changes = _apply_watchlist_changes(llm_response.watchlist_changes)

    actions = {"trades": executed_trades, "watchlist_changes": executed_watchlist_changes}
    assistant_message = save_chat_message("assistant", llm_response.message, actions=actions)

    return {
        "message": assistant_message.content,
        "actions": actions,
        "created_at": assistant_message.created_at,
    }


def _build_portfolio_context(price_cache: PriceCache) -> PortfolioContext:
    portfolio = get_portfolio_snapshot(price_cache)
    watchlist = []
    for entry in get_watchlist():
        update = price_cache.get(entry.ticker)
        watchlist.append({"ticker": entry.ticker, "price": update.price if update else None})
    return PortfolioContext.from_snapshot({**portfolio, "watchlist": watchlist})


def _apply_trades(trades: list[TradeInstruction], price_cache: PriceCache) -> list[dict]:
    results = []
    for trade in trades:
        try:
            result = execute_trade(trade.ticker, trade.side, trade.quantity, price_cache)
            results.append({"status": "executed", **result})
        except TradeError as exc:
            results.append(
                {
                    "status": "failed",
                    "ticker": trade.ticker,
                    "side": trade.side,
                    "quantity": trade.quantity,
                    "error": str(exc),
                }
            )
    return results


def _apply_watchlist_changes(changes: list[WatchlistChangeInstruction]) -> list[dict]:
    results = []
    for change in changes:
        ticker = change.ticker.strip().upper()
        if change.action == "add":
            add_to_watchlist(ticker)
        else:
            remove_from_watchlist(ticker)
        results.append({"status": "executed", "ticker": ticker, "action": change.action})
    return results
