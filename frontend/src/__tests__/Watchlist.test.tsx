import { render, screen, fireEvent } from '@testing-library/react';
import { Watchlist } from '@/components/Watchlist';
import type { PriceUpdate } from '@/lib/types';

function makeUpdate(ticker: string, price: number, previous: number): PriceUpdate {
  return {
    ticker,
    price,
    previous_price: previous,
    timestamp: Date.now() / 1000,
    change: price - previous,
    change_percent: ((price - previous) / previous) * 100,
    direction: price > previous ? 'up' : price < previous ? 'down' : 'flat',
  };
}

describe('Watchlist', () => {
  const baseProps = {
    tickers: ['AAPL', 'GOOGL'],
    history: {},
    sessionOpen: { AAPL: 190, GOOGL: 175 },
    selectedTicker: null,
    onSelect: jest.fn(),
    onAdd: jest.fn(),
    onRemove: jest.fn(),
  };

  it('renders each watched ticker with its live price', () => {
    render(
      <Watchlist
        {...baseProps}
        livePrices={{ AAPL: makeUpdate('AAPL', 191, 190), GOOGL: makeUpdate('GOOGL', 175, 175) }}
      />,
    );
    expect(screen.getByTestId('watchlist-row-AAPL')).toHaveTextContent('191.00');
    expect(screen.getByTestId('watchlist-row-GOOGL')).toHaveTextContent('175.00');
  });

  it('shows % change since session open', () => {
    render(
      <Watchlist
        {...baseProps}
        livePrices={{ AAPL: makeUpdate('AAPL', 195, 190) }}
      />,
    );
    expect(screen.getByTestId('watchlist-change-AAPL')).toHaveTextContent('+2.63%');
  });

  it('calls onSelect when a row is clicked', () => {
    const onSelect = jest.fn();
    render(<Watchlist {...baseProps} livePrices={{}} onSelect={onSelect} />);
    fireEvent.click(screen.getByTestId('watchlist-row-AAPL'));
    expect(onSelect).toHaveBeenCalledWith('AAPL');
  });

  it('calls onAdd with the trimmed, uppercased ticker when Add is clicked', () => {
    const onAdd = jest.fn();
    render(<Watchlist {...baseProps} livePrices={{}} onAdd={onAdd} />);
    fireEvent.change(screen.getByLabelText('Add ticker to watchlist'), { target: { value: ' pypl ' } });
    fireEvent.click(screen.getByText('Add'));
    expect(onAdd).toHaveBeenCalledWith('PYPL');
  });

  it('calls onRemove when the remove button is clicked', () => {
    const onRemove = jest.fn();
    render(<Watchlist {...baseProps} livePrices={{}} onRemove={onRemove} />);
    fireEvent.click(screen.getByLabelText('Remove AAPL from watchlist'));
    expect(onRemove).toHaveBeenCalledWith('AAPL');
  });

  it('applies a flash animation class when a ticker price changes', () => {
    const update1 = makeUpdate('AAPL', 190, 190);
    const { rerender } = render(
      <Watchlist {...baseProps} livePrices={{ AAPL: update1 }} />,
    );

    const update2 = makeUpdate('AAPL', 195, 190);
    rerender(<Watchlist {...baseProps} livePrices={{ AAPL: update2 }} />);

    const priceCell = screen.getByTestId('watchlist-row-AAPL').querySelector('.animate-flash-green');
    expect(priceCell).not.toBeNull();
  });

  it('applies a red flash animation class on a downtick', () => {
    const update1 = makeUpdate('AAPL', 190, 190);
    const { rerender } = render(
      <Watchlist {...baseProps} livePrices={{ AAPL: update1 }} />,
    );

    const update2 = makeUpdate('AAPL', 185, 190);
    rerender(<Watchlist {...baseProps} livePrices={{ AAPL: update2 }} />);

    const priceCell = screen.getByTestId('watchlist-row-AAPL').querySelector('.animate-flash-red');
    expect(priceCell).not.toBeNull();
  });
});
