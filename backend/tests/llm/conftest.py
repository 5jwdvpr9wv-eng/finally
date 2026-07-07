"""Shared fixtures for LLM module tests."""

import pytest

from app.llm.models import PortfolioContext, PositionContext, WatchlistItemContext


@pytest.fixture
def empty_portfolio() -> PortfolioContext:
    return PortfolioContext(cash=10000.0, total_value=10000.0, positions=[], watchlist=[])


@pytest.fixture
def sample_portfolio() -> PortfolioContext:
    return PortfolioContext(
        cash=5000.0,
        total_value=6000.0,
        positions=[
            PositionContext(
                ticker="AAPL",
                quantity=5,
                avg_cost=190.0,
                current_price=200.0,
                unrealized_pnl=50.0,
                unrealized_pnl_percent=5.26,
            )
        ],
        watchlist=[
            WatchlistItemContext(ticker="AAPL", price=200.0),
            WatchlistItemContext(ticker="NFLX", price=None),
        ],
    )
