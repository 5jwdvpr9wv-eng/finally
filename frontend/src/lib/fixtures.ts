import type { Portfolio, PortfolioSnapshot, WatchlistTicker, ChatMessage } from './types';

// Fixture data for local dev (NEXT_PUBLIC_USE_MOCKS=true) and component tests.
// Mirrors default seed data from planning/PLAN.md §7.

export const DEFAULT_TICKERS = [
  'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM', 'V', 'NFLX',
];

const SEED_PRICES: Record<string, number> = {
  AAPL: 190.2, GOOGL: 175.4, MSFT: 415.1, AMZN: 178.3, TSLA: 242.7,
  NVDA: 128.5, META: 505.9, JPM: 198.6, V: 275.3, NFLX: 645.8,
};

export function fixtureWatchlist(): WatchlistTicker[] {
  return DEFAULT_TICKERS.map((ticker) => ({
    ticker,
    added_at: new Date().toISOString(),
    price: SEED_PRICES[ticker],
    previous_price: SEED_PRICES[ticker],
    change: 0,
    change_percent: 0,
    direction: 'flat',
  }));
}

export function fixturePortfolio(): Portfolio {
  const positions = [
    {
      ticker: 'AAPL',
      quantity: 10,
      avg_cost: 185.0,
      current_price: SEED_PRICES.AAPL,
      market_value: 10 * SEED_PRICES.AAPL,
      unrealized_pl: 10 * (SEED_PRICES.AAPL - 185.0),
      unrealized_pl_percent: ((SEED_PRICES.AAPL - 185.0) / 185.0) * 100,
    },
    {
      ticker: 'NVDA',
      quantity: 5,
      avg_cost: 135.0,
      current_price: SEED_PRICES.NVDA,
      market_value: 5 * SEED_PRICES.NVDA,
      unrealized_pl: 5 * (SEED_PRICES.NVDA - 135.0),
      unrealized_pl_percent: ((SEED_PRICES.NVDA - 135.0) / 135.0) * 100,
    },
  ];
  const invested = positions.reduce((sum, p) => sum + p.market_value, 0);
  const cash_balance = 10000 - positions.reduce((sum, p) => sum + p.quantity * p.avg_cost, 0);
  return {
    cash_balance,
    positions,
    total_value: cash_balance + invested,
  };
}

export function fixtureHistory(): PortfolioSnapshot[] {
  const now = Date.now();
  const points = 20;
  return Array.from({ length: points }, (_, i) => ({
    id: `snap-${i}`,
    user_id: 'default',
    total_value: 10000 + Math.sin(i / 3) * 200 + i * 15,
    recorded_at: new Date(now - (points - i) * 30_000).toISOString(),
  }));
}

export function fixtureChatHistory(): ChatMessage[] {
  return [
    {
      id: 'msg-1',
      user_id: 'default',
      role: 'assistant',
      content:
        "Welcome to FinAlly! I'm your AI trading assistant. You have $10,000 in cash to start. Ask me anything about your portfolio or the market.",
      actions: null,
      created_at: new Date().toISOString(),
    },
  ];
}
