import type {
  ChatMessage,
  ChatResponse,
  Portfolio,
  PortfolioSnapshot,
  TradeRequest,
  TradeResponse,
  WatchlistTicker,
} from './types';
import {
  fixtureChatHistory,
  fixtureHistory,
  fixturePortfolio,
  fixtureWatchlist,
} from './fixtures';

// Toggle with NEXT_PUBLIC_USE_MOCKS=true for local dev before the backend is
// reachable. Endpoint shapes follow planning/API_CONTRACT.md.
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === 'true';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch {
      // Non-JSON error body; fall back to statusText.
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export async function getPortfolio(): Promise<Portfolio> {
  if (USE_MOCKS) return fixturePortfolio();
  return request<Portfolio>('/api/portfolio');
}

export async function getPortfolioHistory(): Promise<PortfolioSnapshot[]> {
  if (USE_MOCKS) return fixtureHistory();
  const { snapshots } = await request<{ snapshots: PortfolioSnapshot[] }>('/api/portfolio/history');
  return snapshots;
}

export async function executeTrade(trade: TradeRequest): Promise<TradeResponse> {
  if (USE_MOCKS) {
    return {
      trade: { id: 'mock', user_id: 'default', ...trade, price: 100, executed_at: new Date().toISOString() },
      portfolio: fixturePortfolio(),
    };
  }
  return request<TradeResponse>('/api/portfolio/trade', {
    method: 'POST',
    body: JSON.stringify(trade),
  });
}

export async function getWatchlist(): Promise<WatchlistTicker[]> {
  if (USE_MOCKS) return fixtureWatchlist();
  const { watchlist } = await request<{ watchlist: WatchlistTicker[] }>('/api/watchlist');
  return watchlist;
}

export async function addToWatchlist(ticker: string): Promise<{ ticker: string; added_at: string }> {
  if (USE_MOCKS) return { ticker, added_at: new Date().toISOString() };
  return request('/api/watchlist', {
    method: 'POST',
    body: JSON.stringify({ ticker }),
  });
}

export async function removeFromWatchlist(ticker: string): Promise<void> {
  if (USE_MOCKS) return;
  await request<{ removed: boolean; ticker: string }>(`/api/watchlist/${encodeURIComponent(ticker)}`, {
    method: 'DELETE',
  });
}

export async function getChatHistory(): Promise<ChatMessage[]> {
  if (USE_MOCKS) return fixtureChatHistory();
  const { messages } = await request<{ messages: ChatMessage[] }>('/api/chat/history');
  return messages;
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  if (USE_MOCKS) {
    return {
      message: `(mock) You said: "${message}"`,
      actions: { trades: [], watchlist_changes: [] },
      created_at: new Date().toISOString(),
    };
  }
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}
