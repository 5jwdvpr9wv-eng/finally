// Shapes mirror planning/API_CONTRACT.md (published by the backend engineer).

export interface PriceUpdate {
  ticker: string;
  price: number;
  previous_price: number;
  timestamp: number; // unix seconds
  change: number;
  change_percent: number;
  direction: 'up' | 'down' | 'flat';
}

// SSE payload: a single `data:` event carries a dict keyed by ticker,
// per API_CONTRACT.md "GET /api/stream/prices".
export type PriceStreamPayload = Record<string, PriceUpdate>;

export type ConnectionStatus = 'connected' | 'reconnecting' | 'disconnected';

export interface WatchlistTicker {
  ticker: string;
  added_at: string;
  price: number | null;
  previous_price: number | null;
  change: number | null;
  change_percent: number | null;
  direction: 'up' | 'down' | 'flat';
}

export interface Position {
  ticker: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_pl_percent: number;
}

export interface Portfolio {
  cash_balance: number;
  positions: Position[];
  total_value: number;
}

export interface PortfolioSnapshot {
  id: string;
  user_id: string;
  total_value: number;
  recorded_at: string;
}

export type TradeSide = 'buy' | 'sell';

export interface TradeRequest {
  ticker: string;
  quantity: number;
  side: TradeSide;
}

export interface Trade {
  id: string;
  user_id: string;
  ticker: string;
  side: TradeSide;
  quantity: number;
  price: number;
  executed_at: string;
}

export interface TradeResponse {
  trade: Trade;
  portfolio: Portfolio;
}

// Shape of one entry in a chat response's actions.trades / actions.watchlist_changes
// array — either fully executed (extends the base record) or failed (minimal
// echo of the request plus an error string). Per API_CONTRACT.md "POST /api/chat".
export type ChatActionTrade =
  | (Trade & { status: 'executed' })
  | { status: 'failed'; ticker: string; side: TradeSide; quantity: number; error: string };

export type ChatActionWatchlistChange =
  | { status: 'executed'; ticker: string; action: 'add' | 'remove' }
  | { status: 'failed'; ticker: string; action: 'add' | 'remove'; error: string };

export interface ChatActions {
  trades: ChatActionTrade[];
  watchlist_changes: ChatActionWatchlistChange[];
}

export interface ChatMessage {
  id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  actions: ChatActions | null;
  created_at: string;
}

export interface ChatResponse {
  message: string;
  actions: ChatActions;
  created_at: string;
}
