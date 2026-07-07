import { test, expect } from '@playwright/test';
import { waitForLivePrice } from './helpers';

test.describe('portfolio visualization', () => {
  test('heatmap renders position colors and the P&L chart has data points', async ({ page }) => {
    await page.goto('/');
    await waitForLivePrice(page, 'MSFT');

    // Heatmap and P&L chart only render their chart body once there's at
    // least one position / snapshot, so open a position first.
    await page.getByLabel('Trade ticker').fill('MSFT');
    await page.getByLabel('Trade quantity').fill('2');
    await page.getByRole('button', { name: 'Buy' }).click();
    await expect(page.getByTestId('position-row-MSFT')).toBeVisible();

    const heatmap = page.getByTestId('portfolio-heatmap');
    await expect(heatmap).toBeVisible();
    const heatmapRect = heatmap.locator('rect').first();
    await expect(heatmapRect).toBeVisible();
    const fill = await heatmapRect.getAttribute('fill');
    expect(fill).toMatch(/^rgb\(\d+, \d+, \d+\)$/);

    const pnlChart = page.getByTestId('pnl-chart');
    await expect(pnlChart).toBeVisible();
    // Recharts draws the series as an SVG <path>; a trade just executed
    // (which records an immediate snapshot per PLAN.md §7), so at least one
    // data point should be plotted. Check DOM presence/data rather than
    // pixel visibility — a flat portfolio value over a short test window
    // legitimately renders a zero-height line, which toBeVisible() would
    // (wrongly) treat as hidden even though real points were drawn.
    const curve = pnlChart.locator('.recharts-line-curve');
    await expect(curve).toBeAttached();
    const d = await curve.getAttribute('d');
    expect(d, 'line chart path should have a non-empty data string').toBeTruthy();
  });
});
