'use client';

import { useEffect, useState } from 'react';
import type { TradeSide } from '@/lib/types';

interface TradeBarProps {
  defaultTicker?: string | null;
  onTrade: (ticker: string, quantity: number, side: TradeSide) => Promise<void>;
}

// Market orders only, instant fill, no confirmation dialog, whole-number
// quantity — per PLAN.md §2/§10. Fractional shares are AI-chat only.
export function TradeBar({ defaultTicker, onTrade }: TradeBarProps) {
  const [ticker, setTicker] = useState(defaultTicker ?? '');
  const [quantity, setQuantity] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (defaultTicker) setTicker(defaultTicker);
  }, [defaultTicker]);

  const submit = async (side: TradeSide) => {
    setError(null);
    const t = ticker.trim().toUpperCase();
    const qty = Number(quantity);
    if (!t) {
      setError('Enter a ticker');
      return;
    }
    if (!Number.isInteger(qty) || qty <= 0) {
      setError('Quantity must be a positive whole number');
      return;
    }
    setSubmitting(true);
    try {
      await onTrade(t, qty, side);
      setQuantity('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Trade failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-2 rounded border border-border-muted bg-navy-panel px-3 py-2">
      <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">Trade</span>
      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Ticker"
        aria-label="Trade ticker"
        className="w-24 rounded border border-border-muted bg-navy-bg px-2 py-1 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-primary focus:outline-none"
      />
      <input
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        placeholder="Qty"
        type="number"
        step={1}
        min={1}
        aria-label="Trade quantity"
        className="w-20 rounded border border-border-muted bg-navy-bg px-2 py-1 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-primary focus:outline-none"
      />
      <button
        onClick={() => submit('buy')}
        disabled={submitting}
        className="rounded bg-up-green px-4 py-1 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
      >
        Buy
      </button>
      <button
        onClick={() => submit('sell')}
        disabled={submitting}
        className="rounded bg-down-red px-4 py-1 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
      >
        Sell
      </button>
      {error && (
        <span className="text-xs text-down-red" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}
