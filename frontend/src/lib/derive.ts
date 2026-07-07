import type { Portfolio, Position, PriceUpdate } from './types';

// Recomputes positions' current_price/market_value/unrealized P&L using the
// live SSE price cache when available, falling back to the server-supplied
// current_price otherwise (e.g. before the first SSE tick for that ticker).
export function deriveLivePortfolio(
  portfolio: Portfolio,
  livePrices: Record<string, PriceUpdate>,
): Portfolio {
  const positions: Position[] = portfolio.positions.map((p) => {
    const live = livePrices[p.ticker]?.price;
    const currentPrice = live ?? p.current_price;
    const marketValue = p.quantity * currentPrice;
    const unrealizedPl = marketValue - p.quantity * p.avg_cost;
    const unrealizedPlPercent = p.avg_cost > 0 ? (unrealizedPl / (p.quantity * p.avg_cost)) * 100 : 0;
    return {
      ...p,
      current_price: currentPrice,
      market_value: marketValue,
      unrealized_pl: unrealizedPl,
      unrealized_pl_percent: unrealizedPlPercent,
    };
  });

  const totalValue = portfolio.cash_balance + positions.reduce((sum, p) => sum + p.market_value, 0);

  return { cash_balance: portfolio.cash_balance, positions, total_value: totalValue };
}
