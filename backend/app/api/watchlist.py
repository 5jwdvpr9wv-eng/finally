"""Watchlist routes: list with live prices, add, remove."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import add_to_watchlist, get_watchlist, remove_from_watchlist
from app.market import PriceCache
from app.market.interface import MarketDataSource

from .deps import get_market_source, get_price_cache

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class WatchlistRequest(BaseModel):
    ticker: str


@router.get("")
async def list_watchlist(price_cache: PriceCache = Depends(get_price_cache)) -> dict:
    entries = get_watchlist()
    items = []
    for entry in entries:
        update = price_cache.get(entry.ticker)
        items.append(
            {
                "ticker": entry.ticker,
                "added_at": entry.added_at,
                "price": update.price if update else None,
                "previous_price": update.previous_price if update else None,
                "change": update.change if update else None,
                "change_percent": update.change_percent if update else None,
                "direction": update.direction if update else None,
            }
        )
    return {"watchlist": items}


@router.post("")
async def add_watchlist_ticker(
    body: WatchlistRequest,
    market_source: MarketDataSource = Depends(get_market_source),
) -> dict:
    ticker = body.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")
    entry = add_to_watchlist(ticker)
    await market_source.add_ticker(ticker)
    return {"ticker": entry.ticker, "added_at": entry.added_at}


@router.delete("/{ticker}")
async def remove_watchlist_ticker(
    ticker: str,
    market_source: MarketDataSource = Depends(get_market_source),
) -> dict:
    normalized = ticker.strip().upper()
    removed = remove_from_watchlist(normalized)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{normalized} is not on the watchlist")
    await market_source.remove_ticker(normalized)
    return {"removed": True, "ticker": normalized}
