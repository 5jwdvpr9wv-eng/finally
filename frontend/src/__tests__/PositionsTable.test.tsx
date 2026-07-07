import { render, screen } from '@testing-library/react';
import { PositionsTable } from '@/components/PositionsTable';
import type { Position } from '@/lib/types';

const winner: Position = {
  ticker: 'AAPL',
  quantity: 10,
  avg_cost: 100,
  current_price: 110,
  market_value: 1100,
  unrealized_pl: 100,
  unrealized_pl_percent: 10,
};

const loser: Position = {
  ticker: 'TSLA',
  quantity: 5,
  avg_cost: 250,
  current_price: 230,
  market_value: 1150,
  unrealized_pl: -100,
  unrealized_pl_percent: -8,
};

describe('PositionsTable', () => {
  it('shows an empty state with no positions', () => {
    render(<PositionsTable positions={[]} />);
    expect(screen.getByText('No open positions')).toBeInTheDocument();
  });

  it('renders each position with its P&L', () => {
    render(<PositionsTable positions={[winner, loser]} />);
    expect(screen.getByTestId('position-row-AAPL')).toHaveTextContent('+10.00%');
    expect(screen.getByTestId('position-row-TSLA')).toHaveTextContent('-8.00%');
  });

  it('renders quantity, avg cost, and current price', () => {
    render(<PositionsTable positions={[winner]} />);
    const row = screen.getByTestId('position-row-AAPL');
    expect(row).toHaveTextContent('10');
    expect(row).toHaveTextContent('$100.00');
    expect(row).toHaveTextContent('$110.00');
  });
});
