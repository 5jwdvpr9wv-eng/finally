"""Portfolio routes: positions/cash view, trade execution, value history."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import get_snapshots, record_snapshot
from app.market import PriceCache
from app.services.trading import TradeError, execute_trade, get_portfolio_snapshot

from .deps import get_price_cache

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class TradeRequest(BaseModel):
    ticker: str
    quantity: int = Field(gt=0)
    side: Literal["buy", "sell"]


@router.get("")
async def get_portfolio(price_cache: PriceCache = Depends(get_price_cache)) -> dict:
    return get_portfolio_snapshot(price_cache)


@router.post("/trade")
async def post_trade(
    body: TradeRequest, price_cache: PriceCache = Depends(get_price_cache)
) -> dict:
    try:
        trade = execute_trade(body.ticker, body.side, float(body.quantity), price_cache)
    except TradeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    portfolio = get_portfolio_snapshot(price_cache)
    record_snapshot(portfolio["total_value"])
    return {"trade": trade, "portfolio": portfolio}


@router.get("/history")
async def get_history() -> dict:
    snapshots = get_snapshots()
    return {"snapshots": [s.to_dict() for s in snapshots]}
