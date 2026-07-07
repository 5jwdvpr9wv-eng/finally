'use client';

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { PortfolioSnapshot } from '@/lib/types';

interface PnLChartProps {
  snapshots: PortfolioSnapshot[];
}

export function PnLChart({ snapshots }: PnLChartProps) {
  const data = snapshots.map((s) => ({
    time: new Date(s.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    value: s.total_value,
  }));

  return (
    <div className="flex h-full flex-col rounded border border-border-muted bg-navy-panel p-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        Portfolio Value
      </h2>
      {data.length === 0 ? (
        <div className="flex flex-1 items-center justify-center text-sm text-gray-600">
          No history yet
        </div>
      ) : (
        <div className="min-h-0 flex-1" data-testid="pnl-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <XAxis dataKey="time" stroke="#6b7280" fontSize={10} tickLine={false} />
              <YAxis
                stroke="#6b7280"
                fontSize={10}
                tickLine={false}
                domain={['auto', 'auto']}
                tickFormatter={(v: number) => `$${v.toLocaleString()}`}
                width={64}
              />
              <Tooltip
                contentStyle={{ background: '#0d1117', border: '1px solid #2a2e3a' }}
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Value']}
              />
              <Line type="monotone" dataKey="value" stroke="#ecad0a" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
