import { render, screen } from '@testing-library/react';
import { PortfolioHeatmap, pnlColor } from '@/components/PortfolioHeatmap';
import type { Position } from '@/lib/types';

describe('pnlColor', () => {
  it('returns green-shifted color for a profit', () => {
    expect(pnlColor(10)).toBe('rgb(40, 106, 75)');
  });

  it('returns red-shifted color for a loss', () => {
    expect(pnlColor(-10)).toBe('rgb(136, 59, 68)');
  });

  it('clamps extreme values so color intensity saturates at +/-20%', () => {
    expect(pnlColor(50)).toBe(pnlColor(20));
    expect(pnlColor(-50)).toBe(pnlColor(-20));
  });
});

describe('PortfolioHeatmap', () => {
  it('shows an empty state with no positions', () => {
    render(<PortfolioHeatmap positions={[]} />);
    expect(screen.getByText('No open positions')).toBeInTheDocument();
  });

  it('renders the treemap container when positions exist', () => {
    const positions: Position[] = [
      {
        ticker: 'AAPL',
        quantity: 10,
        avg_cost: 100,
        current_price: 110,
        market_value: 1100,
        unrealized_pl: 100,
        unrealized_pl_percent: 10,
      },
    ];
    render(<PortfolioHeatmap positions={positions} />);
    expect(screen.getByTestId('portfolio-heatmap')).toBeInTheDocument();
  });
});
