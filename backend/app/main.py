"""FinAlly FastAPI application: API routes, SSE market stream, static frontend."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.portfolio import router as portfolio_router
from app.api.watchlist import router as watchlist_router
from app.db import get_watchlist, record_snapshot
from app.market import PriceCache, create_market_data_source
from app.market.stream import create_stream_router
from app.services.trading import compute_total_value

logger = logging.getLogger(__name__)

SNAPSHOT_INTERVAL_SECONDS = 30
# backend/app/main.py -> parents[2] is the project root (sibling of frontend/).
_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "out"


async def _snapshot_loop(price_cache: PriceCache) -> None:
    while True:
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
        try:
            record_snapshot(compute_total_value(price_cache))
        except Exception:
            logger.exception("Failed to record periodic portfolio snapshot")


def _mount_frontend(app: FastAPI) -> None:
    if _FRONTEND_DIST.is_dir():
        app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
    else:
        logger.warning("Frontend build not found at %s; static serving disabled", _FRONTEND_DIST)


def create_app() -> FastAPI:
    """Build a fresh FinAlly app with its own price cache and market source.

    Factored out (rather than a bare module-level ``app``) so tests can create
    isolated instances without sharing background-task state across cases.
    """
    price_cache = PriceCache()
    market_source = create_market_data_source(price_cache)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        tickers = [entry.ticker for entry in get_watchlist()]
        await market_source.start(tickers)
        snapshot_task = asyncio.create_task(_snapshot_loop(price_cache))
        try:
            yield
        finally:
            snapshot_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await snapshot_task
            await market_source.stop()

    app = FastAPI(title="FinAlly", lifespan=lifespan)
    app.state.price_cache = price_cache
    app.state.market_source = market_source

    app.include_router(create_stream_router(price_cache))
    app.include_router(health_router)
    app.include_router(portfolio_router)
    app.include_router(watchlist_router)
    app.include_router(chat_router)

    _mount_frontend(app)
    return app


app = create_app()
