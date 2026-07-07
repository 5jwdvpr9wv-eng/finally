import { test, expect } from '@playwright/test';
import { DEFAULT_TICKERS, readCashBalance, readTotalValue, waitForLivePrice } from './helpers';

test.describe('fresh start', () => {
  test('shows the default watchlist, $10k cash, and streaming prices', async ({ page }) => {
    await page.goto('/');

    // Default watchlist (PLAN.md §7 seed data) renders in full.
    for (const ticker of DEFAULT_TICKERS) {
      await expect(page.getByTestId(`watchlist-row-${ticker}`)).toBeVisible();
    }

    expect(await readCashBalance(page)).toBe(10000);
    expect(await readTotalValue(page)).toBe(10000);

    // Connection indicator reaches "connected" and prices start streaming.
    await expect(page.getByTestId('connection-status')).toHaveAttribute('data-status', 'connected', {
      timeout: 15_000,
    });
    await waitForLivePrice(page, DEFAULT_TICKERS[0]);

    // Positions/heatmap/P&L start empty for a brand-new user.
    await expect(page.getByText('No open positions').first()).toBeVisible();
  });
});
