'use client';

import type { PricePoint } from '@/hooks/usePriceStream';

interface SparklineProps {
  points: PricePoint[];
  width?: number;
  height?: number;
  color: string;
}

// Lightweight inline SVG sparkline (accumulated client-side since page load —
// no historical price API exists, per PLAN.md §2/§10). Avoids the overhead of
// mounting a full chart library instance per watchlist row.
export function Sparkline({ points, width = 80, height = 28, color }: SparklineProps) {
  if (points.length < 2) {
    return (
      <svg width={width} height={height} className="opacity-30" aria-hidden="true">
        <line x1={0} y1={height / 2} x2={width} y2={height / 2} stroke="#3a3f4b" strokeWidth={1} />
      </svg>
    );
  }

  const prices = points.map((p) => p.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  const path = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * width;
      const y = height - ((p.price - min) / range) * height;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} role="img" aria-label="price sparkline">
      <path d={path} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  );
}
