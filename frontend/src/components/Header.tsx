import { ConnectionDot } from './ConnectionDot';
import type { ConnectionStatus } from '@/lib/types';

interface HeaderProps {
  totalValue: number;
  cashBalance: number;
  status: ConnectionStatus;
}

const currency = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 });

export function Header({ totalValue, cashBalance, status }: HeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-border-muted bg-navy-panel px-6 py-3">
      <div className="flex items-center gap-3">
        <span className="text-lg font-bold tracking-tight text-accent-yellow">FinAlly</span>
        <span className="text-xs text-gray-500">AI Trading Workstation</span>
      </div>
      <div className="flex items-center gap-8">
        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wide text-gray-500">Portfolio Value</div>
          <div className="text-lg font-semibold text-gray-100" data-testid="total-value">
            {currency(totalValue)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wide text-gray-500">Cash</div>
          <div className="text-lg font-semibold text-blue-primary" data-testid="cash-balance">
            {currency(cashBalance)}
          </div>
        </div>
        <ConnectionDot status={status} />
      </div>
    </header>
  );
}
