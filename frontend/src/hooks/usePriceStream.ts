'use client';

import { useEffect, useRef, useState } from 'react';
import type { ConnectionStatus, PriceStreamPayload, PriceUpdate } from '@/lib/types';

export interface PricePoint {
  time: number; // unix seconds
  price: number;
}

export interface PriceStreamState {
  prices: Record<string, PriceUpdate>;
  // Price history accumulated client-side since page load, per PLAN.md §2/§10
  // ("no historical price API exists" — sparklines/charts start empty and fill in).
  history: Record<string, PricePoint[]>;
  // First price seen per ticker this session, for "% chg since session open".
  sessionOpen: Record<string, number>;
  status: ConnectionStatus;
}

const MAX_HISTORY_POINTS = 3600; // ~30 min at the 500ms server cadence

export function usePriceStream(streamUrl = '/api/stream/prices'): PriceStreamState {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({});
  const [status, setStatus] = useState<ConnectionStatus>('reconnecting');
  const historyRef = useRef<Record<string, PricePoint[]>>({});
  const sessionOpenRef = useRef<Record<string, number>>({});
  const [historyVersion, setHistoryVersion] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      return;
    }

    const source = new EventSource(streamUrl);

    source.onopen = () => setStatus('connected');

    source.onmessage = (event: MessageEvent<string>) => {
      setStatus('connected');
      try {
        const payload: PriceStreamPayload = JSON.parse(event.data);
        setPrices((prev) => ({ ...prev, ...payload }));

        for (const [ticker, update] of Object.entries(payload)) {
          if (sessionOpenRef.current[ticker] === undefined) {
            sessionOpenRef.current[ticker] = update.price;
          }
          const series = historyRef.current[ticker] ?? [];
          series.push({ time: update.timestamp, price: update.price });
          if (series.length > MAX_HISTORY_POINTS) series.shift();
          historyRef.current[ticker] = series;
        }
        setHistoryVersion((v) => v + 1);
      } catch {
        // Malformed event; skip rather than crash the stream handler.
      }
    };

    source.onerror = () => {
      setStatus(source.readyState === EventSource.CLOSED ? 'disconnected' : 'reconnecting');
    };

    return () => {
      source.close();
    };
  }, [streamUrl]);

  // historyVersion (unused directly) forces this hook to re-render on every
  // tick even though history/sessionOpen are refs mutated in place — avoids
  // re-allocating the full per-ticker arrays on every 500ms update.
  void historyVersion;

  return {
    prices,
    history: historyRef.current,
    sessionOpen: sessionOpenRef.current,
    status,
  };
}

export { MAX_HISTORY_POINTS };
