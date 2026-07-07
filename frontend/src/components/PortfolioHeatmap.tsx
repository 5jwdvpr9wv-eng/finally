'use client';

import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import type { Position } from '@/lib/types';

interface PortfolioHeatmapProps {
  positions: Position[];
}

// Colors positions from loss-red through neutral-gray to profit-green,
// clamped at +/-20% so a single outsized winner/loser doesn't wash out
// the rest of the map.
export function pnlColor(pnlPercent: number): string {
  const clamped = Math.max(-20, Math.min(20, pnlPercent));
  const intensity = Math.abs(clamped) / 20;
  if (clamped >= 0) {
    const from = [42, 46, 58]; // border-muted gray
    const to = [38, 166, 91]; // up-green
    return rgb(lerp(from, to, intensity));
  }
  const from = [42, 46, 58];
  const to = [229, 72, 77]; // down-red
  return rgb(lerp(from, to, intensity));
}

function lerp(a: number[], b: number[], t: number): number[] {
  return a.map((v, i) => Math.round(v + (b[i] - v) * t));
}

function rgb([r, g, b]: number[]): string {
  return `rgb(${r}, ${g}, ${b})`;
}

interface TreemapCellProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  pnlPercent?: number;
}

function TreemapCell({ x = 0, y = 0, width = 0, height = 0, name, pnlPercent = 0 }: TreemapCellProps) {
  if (width <= 0 || height <= 0) return null;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={pnlColor(pnlPercent)}
        stroke="#0d1117"
        strokeWidth={2}
      />
      {width > 40 && height > 24 && (
        <text x={x + 6} y={y + 16} fontSize={11} fill="#e6e6e6" fontWeight={600}>
          {name}
        </text>
      )}
      {width > 40 && height > 40 && (
        <text x={x + 6} y={y + 30} fontSize={10} fill="#cbd5e1">
          {pnlPercent >= 0 ? '+' : ''}
          {pnlPercent.toFixed(1)}%
        </text>
      )}
    </g>
  );
}

export function PortfolioHeatmap({ positions }: PortfolioHeatmapProps) {
  const data = positions.map((p) => ({
    name: p.ticker,
    size: Math.max(p.market_value, 0.01),
    pnlPercent: p.unrealized_pl_percent,
  }));

  return (
    <div className="flex h-full flex-col rounded border border-border-muted bg-navy-panel p-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        Portfolio Heatmap
      </h2>
      {data.length === 0 ? (
        <div className="flex flex-1 items-center justify-center text-sm text-gray-600">
          No open positions
        </div>
      ) : (
        <div className="min-h-0 flex-1" data-testid="portfolio-heatmap">
          <ResponsiveContainer width="100%" height="100%">
            <Treemap
              data={data}
              dataKey="size"
              stroke="#0d1117"
              content={<TreemapCell />}
              isAnimationActive={false}
            >
              <Tooltip
                contentStyle={{ background: '#0d1117', border: '1px solid #2a2e3a' }}
                formatter={(value: number, key: string, entry) => {
                  const pnl = (entry?.payload as { pnlPercent?: number })?.pnlPercent ?? 0;
                  return [`$${value.toFixed(2)} (${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%)`, 'Value'];
                }}
              />
            </Treemap>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
