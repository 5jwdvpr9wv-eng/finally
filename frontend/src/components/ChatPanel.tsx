'use client';

import { useEffect, useRef, useState } from 'react';
import type { ChatActions, ChatMessage } from '@/lib/types';

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => Promise<void>;
}

export function ChatPanel({ messages, loading, onSend }: ChatPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  const submit = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    await onSend(text);
  };

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        aria-label="Expand AI chat panel"
        className="flex h-full w-10 flex-col items-center justify-center gap-2 rounded border border-border-muted bg-navy-panel text-accent-yellow"
      >
        <span className="[writing-mode:vertical-rl]">AI Chat</span>
      </button>
    );
  }

  return (
    <div className="flex h-full flex-col rounded border border-border-muted bg-navy-panel">
      <div className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">AI Assistant</h2>
        <button
          onClick={() => setCollapsed(true)}
          aria-label="Collapse AI chat panel"
          className="text-gray-500 hover:text-gray-200"
        >
          «
        </button>
      </div>
      <div ref={scrollRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3" data-testid="chat-history">
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-gray-500" data-testid="chat-loading">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-yellow" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-yellow [animation-delay:150ms]" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-yellow [animation-delay:300ms]" />
            <span>FinAlly is thinking…</span>
          </div>
        )}
      </div>
      <div className="flex gap-2 border-t border-border-muted p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Ask FinAlly anything..."
          aria-label="Chat message"
          className="min-w-0 flex-1 rounded border border-border-muted bg-navy-bg px-2 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-primary focus:outline-none"
        />
        <button
          onClick={submit}
          disabled={loading || !input.trim()}
          className="rounded bg-purple-secondary px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  return (
    <div
      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
      data-testid={`chat-message-${message.id}`}
    >
      <div
        className={`max-w-[90%] rounded px-3 py-2 text-sm ${
          isUser ? 'bg-blue-primary/20 text-gray-100' : 'bg-white/5 text-gray-200'
        }`}
      >
        {message.content}
      </div>
      {message.actions && <ActionSummary actions={message.actions} />}
    </div>
  );
}

function ActionSummary({ actions }: { actions: ChatActions }) {
  const trades = actions.trades ?? [];
  const changes = actions.watchlist_changes ?? [];
  if (trades.length === 0 && changes.length === 0) return null;

  return (
    <div className="mt-1 max-w-[90%] space-y-1" data-testid="chat-action-summary">
      {trades.map((t, i) => (
        <div
          key={`trade-${i}`}
          className={`rounded border px-2 py-1 text-xs ${
            t.status === 'failed'
              ? 'border-down-red/40 bg-down-red/10 text-down-red'
              : 'border-up-green/40 bg-up-green/10 text-up-green'
          }`}
        >
          {t.status === 'failed'
            ? `Failed: ${t.side} ${t.quantity} ${t.ticker} — ${t.error}`
            : `Executed: ${t.side === 'buy' ? 'Bought' : 'Sold'} ${t.quantity} ${t.ticker} @ $${t.price.toFixed(2)}`}
        </div>
      ))}
      {changes.map((c, i) => (
        <div
          key={`watch-${i}`}
          className={`rounded border px-2 py-1 text-xs ${
            c.status === 'failed'
              ? 'border-down-red/40 bg-down-red/10 text-down-red'
              : 'border-blue-primary/40 bg-blue-primary/10 text-blue-primary'
          }`}
        >
          {c.status === 'failed'
            ? `Failed to ${c.action} ${c.ticker} — ${c.error}`
            : `Watchlist: ${c.action === 'add' ? 'added' : 'removed'} ${c.ticker}`}
        </div>
      ))}
    </div>
  );
}
