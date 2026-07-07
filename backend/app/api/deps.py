"""Shared FastAPI dependencies for accessing app-wide singletons.

The price cache and market data source are created once in ``app.main`` and
stashed on ``app.state``; routes pull them out via these dependency functions
instead of importing globals directly.
"""

from __future__ import annotations

from fastapi import Request

from app.market import PriceCache
from app.market.interface import MarketDataSource


def get_price_cache(request: Request) -> PriceCache:
    return request.app.state.price_cache


def get_market_source(request: Request) -> MarketDataSource:
    return request.app.state.market_source
