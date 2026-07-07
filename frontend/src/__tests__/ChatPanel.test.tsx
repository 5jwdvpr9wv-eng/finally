import { render, screen, fireEvent } from '@testing-library/react';
import { ChatPanel } from '@/components/ChatPanel';
import type { ChatMessage } from '@/lib/types';

const userMessage: ChatMessage = {
  id: 'u1',
  user_id: 'default',
  role: 'user',
  content: 'Buy 5 AAPL',
  actions: null,
  created_at: new Date().toISOString(),
};

const assistantMessage: ChatMessage = {
  id: 'a1',
  user_id: 'default',
  role: 'assistant',
  content: 'Done — bought 5 shares of AAPL at $190.00.',
  actions: {
    trades: [
      {
        status: 'executed',
        id: 't1',
        user_id: 'default',
        ticker: 'AAPL',
        side: 'buy',
        quantity: 5,
        price: 190,
        executed_at: new Date().toISOString(),
      },
    ],
    watchlist_changes: [],
  },
  created_at: new Date().toISOString(),
};

describe('ChatPanel', () => {
  it('renders message history', () => {
    render(<ChatPanel messages={[userMessage, assistantMessage]} loading={false} onSend={jest.fn()} />);
    expect(screen.getByTestId('chat-message-u1')).toHaveTextContent('Buy 5 AAPL');
    expect(screen.getByTestId('chat-message-a1')).toHaveTextContent('Done — bought 5 shares of AAPL');
  });

  it('renders an inline trade confirmation for executed actions', () => {
    render(<ChatPanel messages={[assistantMessage]} loading={false} onSend={jest.fn()} />);
    expect(screen.getByTestId('chat-action-summary')).toHaveTextContent('Bought 5 AAPL @ $190.00');
  });

  it('shows a loading indicator while waiting for the assistant', () => {
    render(<ChatPanel messages={[]} loading onSend={jest.fn()} />);
    expect(screen.getByTestId('chat-loading')).toBeInTheDocument();
  });

  it('does not show a loading indicator when not loading', () => {
    render(<ChatPanel messages={[]} loading={false} onSend={jest.fn()} />);
    expect(screen.queryByTestId('chat-loading')).not.toBeInTheDocument();
  });

  it('calls onSend with the input text and clears the input', () => {
    const onSend = jest.fn().mockResolvedValue(undefined);
    render(<ChatPanel messages={[]} loading={false} onSend={onSend} />);
    const input = screen.getByLabelText('Chat message') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'What is my P&L?' } });
    fireEvent.click(screen.getByText('Send'));
    expect(onSend).toHaveBeenCalledWith('What is my P&L?');
    expect(input.value).toBe('');
  });

  it('collapses and expands the panel', () => {
    render(<ChatPanel messages={[]} loading={false} onSend={jest.fn()} />);
    fireEvent.click(screen.getByLabelText('Collapse AI chat panel'));
    expect(screen.getByLabelText('Expand AI chat panel')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Expand AI chat panel'));
    expect(screen.getByLabelText('Collapse AI chat panel')).toBeInTheDocument();
  });
});
