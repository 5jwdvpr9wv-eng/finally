'use client';

import { useEffect, useRef } from 'react';
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts';
import type { PricePoint } from '@/hooks/usePriceStream';

interface MainChartProps {
  ticker: string | null;
  points: PricePoint[];
}

export function MainChart({ ticker, points }: MainChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const pointsRef = useRef<PricePoint[]>(points);
  pointsRef.current = points;

  useEffect(() => {
    // Dynamically imported (rather than a top-level import) so this
    // canvas-based library is never evaluated during Next's static export
    // page-data-collection pass — only after the component has mounted in
    // a real browser.
    let cancelled = false;

    import('lightweight-charts').then(({ createChart }) => {
      if (cancelled || !containerRef.current) return;

      const chart = createChart(containerRef.current, {
        layout: { background: { color: '#1a1a2e' }, textColor: '#9ca3af' },
        grid: {
          vertLines: { color: '#2a2e3a' },
          horzLines: { color: '#2a2e3a' },
        },
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
        timeScale: { timeVisible: true, secondsVisible: true },
      });
      const series = chart.addLineSeries({ color: '#209dd7', lineWidth: 2 });
      series.setData(pointsRef.current.map((p) => ({ time: p.time as UTCTimestamp, value: p.price })));
      chart.timeScale().fitContent();

      chartRef.current = chart;
      seriesRef.current = series;

      // Lightweight Charts renders its canvas at whatever size it's told;
      // it doesn't know about the flex layout's actual available space, so
      // we measure the container directly instead of hardcoding a height.
      const resizeObserver = new ResizeObserver(() => {
        if (containerRef.current) {
          chart.applyOptions({
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight,
          });
        }
      });
      resizeObserver.observe(containerRef.current);
      (chart as unknown as { __cleanup?: () => void }).__cleanup = () => resizeObserver.disconnect();
    });

    return () => {
      cancelled = true;
      const chart = chartRef.current;
      if (chart) {
        (chart as unknown as { __cleanup?: () => void }).__cleanup?.();
        chart.remove();
      }
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    seriesRef.current.setData(points.map((p) => ({ time: p.time as UTCTimestamp, value: p.price })));
    chartRef.current?.timeScale().fitContent();
  }, [points]);

  return (
    <div className="flex h-full flex-col rounded border border-border-muted bg-navy-panel p-3">
      <div className="mb-2 flex items-center gap-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Chart</h2>
        {ticker && (
          <span className="text-sm font-semibold text-accent-yellow" data-testid="main-chart-ticker">
            {ticker}
          </span>
        )}
      </div>
      <div className="relative min-h-0 flex-1 overflow-hidden">
        <div ref={containerRef} data-testid="main-chart-container" className="h-full overflow-hidden" />
        {!ticker && (
          <div className="absolute inset-0 flex items-center justify-center bg-navy-panel text-sm text-gray-600">
            Select a ticker from the watchlist
          </div>
        )}
      </div>
    </div>
  );
}
