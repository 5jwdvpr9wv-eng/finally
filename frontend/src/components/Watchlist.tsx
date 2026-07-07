'use client';

import { useEffect, useRef, useState } from 'react';
import { Sparkline } from './Sparkline';
import type { PricePoint } from '@/hooks/usePriceStream';
import type { PriceUpdate } from '@/lib/types';

interface WatchlistProps {
  tickers: string[];
  livePrices: Record<string, PriceUpdate>;
  history: Record<string, PricePoint[]>;
  sessionOpen: Record<string, number>;
  selectedTicker: string | null;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

const fmtPrice = (n: number) => n.toFixed(2);
const fmtPct = (n: number) => `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;

export function Watchlist({
  tickers,
  livePrices,
  history,
  sessionOpen,
  selectedTicker,
  onSelect,
  onAdd,
  onRemove,
}: WatchlistProps) {
  const [newTicker, setNewTicker] = useState('');

  const handleAdd = () => {
    const t = newTicker.trim().toUpperCase();
    if (!t) return;
    onAdd(t);
    setNewTicker('');
  };

  return (
    <div className="flex h-full flex-col rounded border border-border-muted bg-navy-panel">
      <div className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Watchlist</h2>
      </div>
      <div className="flex gap-1 border-b border-border-muted px-3 py-2">
        <input
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          placeholder="Add ticker"
          aria-label="Add ticker to watchlist"
          className="min-w-0 flex-1 rounded border border-border-muted bg-navy-bg px-2 py-1 text-xs text-gray-200 placeholder-gray-600 focus:border-blue-primary focus:outline-none"
        />
        <button
          onClick={handleAdd}
          className="rounded bg-purple-secondary px-2 py-1 text-xs font-medium text-white hover:opacity-90"
        >
          Add
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {tickers.map((ticker) => (
          <WatchlistRow
            key={ticker}
            ticker={ticker}
            update={livePrices[ticker]}
            points={history[ticker] ?? []}
            openPrice={sessionOpen[ticker]}
            selected={selectedTicker === ticker}
            onSelect={() => onSelect(ticker)}
            onRemove={() => onRemove(ticker)}
          />
        ))}
      </div>
    </div>
  );
}

interface WatchlistRowProps {
  ticker: string;
  update: PriceUpdate | undefined;
  points: PricePoint[];
  openPrice: number | undefined;
  selected: boolean;
  onSelect: () => void;
  onRemove: () => void;
}

function WatchlistRow({
  ticker,
  update,
  points,
  openPrice,
  selected,
  onSelect,
  onRemove,
}: WatchlistRowProps) {
  const [flashToken, setFlashToken] = useState(0);
  const [flashDirection, setFlashDirection] = useState<'up' | 'down' | null>(null);
  const lastPriceRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (update === undefined) return;
    if (lastPriceRef.current !== undefined && update.price !== lastPriceRef.current) {
      setFlashDirection(update.price > lastPriceRef.current ? 'up' : 'down');
      setFlashToken((t) => t + 1);
    }
    lastPriceRef.current = update.price;
  }, [update]);

  const changeSinceOpen =
    openPrice && update?.price !== undefined ? ((update.price - openPrice) / openPrice) * 100 : null;

  const flashClass =
    flashDirection === 'up' ? 'animate-flash-green' : flashDirection === 'down' ? 'animate-flash-red' : '';

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
      data-testid={`watchlist-row-${ticker}`}
      className={`flex cursor-pointer items-center gap-3 border-b border-border-muted px-3 py-2 text-sm hover:bg-white/5 ${
        selected ? 'bg-accent-yellow/10 border-l-2 border-l-accent-yellow' : ''
      }`}
    >
      <div className="w-14 shrink-0 font-medium text-gray-100">{ticker}</div>
      <div key={flashToken} className={`w-16 shrink-0 rounded px-1 text-right tabular-nums ${flashClass}`}>
        {update?.price !== undefined ? fmtPrice(update.price) : '—'}
      </div>
      <div
        className={`w-16 shrink-0 text-right text-xs tabular-nums ${
          changeSinceOpen === null
            ? 'text-gray-500'
            : changeSinceOpen >= 0
              ? 'text-up-green'
              : 'text-down-red'
        }`}
        data-testid={`watchlist-change-${ticker}`}
      >
        {changeSinceOpen === null ? '—' : fmtPct(changeSinceOpen)}
      </div>
      <div className="ml-auto shrink-0">
        <Sparkline
          points={points}
          color={changeSinceOpen !== null && changeSinceOpen < 0 ? '#e5484d' : '#26a65b'}
        />
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        aria-label={`Remove ${ticker} from watchlist`}
        className="shrink-0 px-1 text-gray-600 hover:text-down-red"
      >
        ×
      </button>
    </div>
  );
}
