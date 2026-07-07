import type { Position } from '@/lib/types';

interface PositionsTableProps {
  positions: Position[];
}

const currency = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 });

export function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <div className="flex h-full flex-col rounded border border-border-muted bg-navy-panel p-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Positions</h2>
      {positions.length === 0 ? (
        <div className="flex flex-1 items-center justify-center text-sm text-gray-600">
          No open positions
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <table className="w-full text-left text-sm" data-testid="positions-table">
            <thead className="sticky top-0 bg-navy-panel text-[11px] uppercase tracking-wide text-gray-500">
              <tr>
                <th className="pb-2 pr-2 font-medium">Ticker</th>
                <th className="pb-2 pr-2 text-right font-medium">Qty</th>
                <th className="pb-2 pr-2 text-right font-medium">Avg Cost</th>
                <th className="pb-2 pr-2 text-right font-medium">Price</th>
                <th className="pb-2 pr-2 text-right font-medium">P&amp;L</th>
                <th className="pb-2 text-right font-medium">P&amp;L %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.ticker} className="border-t border-border-muted" data-testid={`position-row-${p.ticker}`}>
                  <td className="py-1.5 pr-2 font-medium text-gray-100">{p.ticker}</td>
                  <td className="py-1.5 pr-2 text-right tabular-nums">{p.quantity}</td>
                  <td className="py-1.5 pr-2 text-right tabular-nums">{currency(p.avg_cost)}</td>
                  <td className="py-1.5 pr-2 text-right tabular-nums">{currency(p.current_price)}</td>
                  <td
                    className={`py-1.5 pr-2 text-right tabular-nums ${
                      p.unrealized_pl >= 0 ? 'text-up-green' : 'text-down-red'
                    }`}
                  >
                    {currency(p.unrealized_pl)}
                  </td>
                  <td
                    className={`py-1.5 text-right tabular-nums ${
                      p.unrealized_pl_percent >= 0 ? 'text-up-green' : 'text-down-red'
                    }`}
                  >
                    {p.unrealized_pl_percent >= 0 ? '+' : ''}
                    {p.unrealized_pl_percent.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
