import { deriveLivePortfolio } from '@/lib/derive';
import type { Portfolio, PriceUpdate } from '@/lib/types';

function makeUpdate(ticker: string, price: number): PriceUpdate {
  return {
    ticker,
    price,
    previous_price: price,
    timestamp: Date.now() / 1000,
    change: 0,
    change_percent: 0,
    direction: 'flat',
  };
}

describe('deriveLivePortfolio', () => {
  const portfolio: Portfolio = {
    cash_balance: 5000,
    positions: [
      {
        ticker: 'AAPL',
        quantity: 10,
        avg_cost: 100,
        current_price: 100,
        market_value: 1000,
        unrealized_pl: 0,
        unrealized_pl_percent: 0,
      },
    ],
    total_value: 6000,
  };

  it('recomputes market value and P&L using the live price when available', () => {
    const result = deriveLivePortfolio(portfolio, { AAPL: makeUpdate('AAPL', 110) });
    const [position] = result.positions;

    expect(position.current_price).toBe(110);
    expect(position.market_value).toBe(1100);
    expect(position.unrealized_pl).toBe(100);
    expect(position.unrealized_pl_percent).toBeCloseTo(10);
  });

  it('recomputes total_value as cash plus the sum of live market values', () => {
    const result = deriveLivePortfolio(portfolio, { AAPL: makeUpdate('AAPL', 110) });
    expect(result.total_value).toBe(5000 + 1100);
  });

  it('falls back to the server-supplied current_price when no live price exists yet', () => {
    const result = deriveLivePortfolio(portfolio, {});
    expect(result.positions[0].current_price).toBe(100);
    expect(result.positions[0].market_value).toBe(1000);
  });

  it('reflects an unrealized loss with a negative P&L percent', () => {
    const result = deriveLivePortfolio(portfolio, { AAPL: makeUpdate('AAPL', 90) });
    expect(result.positions[0].unrealized_pl).toBe(-100);
    expect(result.positions[0].unrealized_pl_percent).toBeCloseTo(-10);
  });
});
