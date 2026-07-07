'use client';

import { useCallback, useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { Watchlist } from '@/components/Watchlist';
import { MainChart } from '@/components/MainChart';
import { PortfolioHeatmap } from '@/components/PortfolioHeatmap';
import { PnLChart } from '@/components/PnLChart';
import { PositionsTable } from '@/components/PositionsTable';
import { TradeBar } from '@/components/TradeBar';
import { ChatPanel } from '@/components/ChatPanel';
import { usePriceStream } from '@/hooks/usePriceStream';
import {
  addToWatchlist,
  executeTrade,
  getChatHistory,
  getPortfolio,
  getPortfolioHistory,
  getWatchlist,
  removeFromWatchlist,
  sendChatMessage,
} from '@/lib/api';
import { deriveLivePortfolio } from '@/lib/derive';
import type { ChatMessage, Portfolio, PortfolioSnapshot, TradeSide } from '@/lib/types';
import { DEFAULT_TICKERS } from '@/lib/fixtures';

const PORTFOLIO_POLL_MS = 5000;
const HISTORY_POLL_MS = 30000;

export default function Home() {
  const { prices, history, sessionOpen, status } = usePriceStream();
  const [tickers, setTickers] = useState<string[]>(DEFAULT_TICKERS);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio>({
    cash_balance: 10000,
    positions: [],
    total_value: 10000,
  });
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const refreshPortfolio = useCallback(async () => {
    try {
      setPortfolio(await getPortfolio());
    } catch {
      // Backend not reachable yet; keep last known state.
    }
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      setSnapshots(await getPortfolioHistory());
    } catch {
      // Backend not reachable yet.
    }
  }, []);

  useEffect(() => {
    getWatchlist()
      .then((items) => {
        if (items.length > 0) setTickers(items.map((i) => i.ticker));
      })
      .catch(() => {
        // Fall back to default watchlist until the backend is reachable.
      });
    getChatHistory()
      .then(setMessages)
      .catch(() => {
        // No history yet / backend not reachable.
      });
    refreshPortfolio();
    refreshHistory();
  }, [refreshPortfolio, refreshHistory]);

  useEffect(() => {
    if (!selectedTicker && tickers.length > 0) setSelectedTicker(tickers[0]);
  }, [tickers, selectedTicker]);

  useEffect(() => {
    const portfolioTimer = setInterval(refreshPortfolio, PORTFOLIO_POLL_MS);
    const historyTimer = setInterval(refreshHistory, HISTORY_POLL_MS);
    return () => {
      clearInterval(portfolioTimer);
      clearInterval(historyTimer);
    };
  }, [refreshPortfolio, refreshHistory]);

  const handleAddTicker = useCallback(async (ticker: string) => {
    setTickers((prev) => (prev.includes(ticker) ? prev : [...prev, ticker]));
    try {
      await addToWatchlist(ticker);
    } catch {
      // Optimistic add; will reconcile on next getWatchlist() call.
    }
  }, []);

  const handleRemoveTicker = useCallback(
    async (ticker: string) => {
      setTickers((prev) => prev.filter((t) => t !== ticker));
      if (selectedTicker === ticker) setSelectedTicker(null);
      try {
        await removeFromWatchlist(ticker);
      } catch {
        // Optimistic remove; will reconcile on next getWatchlist() call.
      }
    },
    [selectedTicker],
  );

  const handleTrade = useCallback(
    async (ticker: string, quantity: number, side: TradeSide) => {
      const { portfolio: fresh } = await executeTrade({ ticker, quantity, side });
      setPortfolio(fresh);
      await refreshHistory();
    },
    [refreshHistory],
  );

  const handleSendChat = useCallback(async (text: string) => {
    const userMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      user_id: 'default',
      role: 'user',
      content: text,
      actions: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setChatLoading(true);
    try {
      const response = await sendChatMessage(text);
      const assistantMessage: ChatMessage = {
        id: `local-${Date.now()}-assistant`,
        user_id: 'default',
        role: 'assistant',
        content: response.message,
        actions: response.actions,
        created_at: response.created_at,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      if (response.actions.trades.length > 0 || response.actions.watchlist_changes.length > 0) {
        await Promise.all([refreshPortfolio(), refreshHistory()]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: `local-${Date.now()}-error`,
          user_id: 'default',
          role: 'assistant',
          content: e instanceof Error ? `Sorry, something went wrong: ${e.message}` : 'Sorry, something went wrong.',
          actions: null,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }, [refreshPortfolio, refreshHistory]);

  const livePortfolio = deriveLivePortfolio(portfolio, prices);

  return (
    <div className="flex h-screen flex-col">
      <Header totalValue={livePortfolio.total_value} cashBalance={livePortfolio.cash_balance} status={status} />
      <div className="grid min-h-0 flex-1 grid-cols-[280px_1fr_320px] gap-3 p-3">
        <div className="min-h-0">
          <Watchlist
            tickers={tickers}
            livePrices={prices}
            history={history}
            sessionOpen={sessionOpen}
            selectedTicker={selectedTicker}
            onSelect={setSelectedTicker}
            onAdd={handleAddTicker}
            onRemove={handleRemoveTicker}
          />
        </div>

        <div className="flex min-h-0 flex-col gap-3">
          <div className="h-80 min-h-0">
            <MainChart ticker={selectedTicker} points={selectedTicker ? (history[selectedTicker] ?? []) : []} />
          </div>
          <TradeBar defaultTicker={selectedTicker} onTrade={handleTrade} />
          <div className="grid min-h-0 flex-1 grid-cols-2 gap-3">
            <PortfolioHeatmap positions={livePortfolio.positions} />
            <PnLChart snapshots={snapshots} />
          </div>
          <div className="h-56 min-h-0">
            <PositionsTable positions={livePortfolio.positions} />
          </div>
        </div>

        <div className="min-h-0">
          <ChatPanel messages={messages} loading={chatLoading} onSend={handleSendChat} />
        </div>
      </div>
    </div>
  );
}
