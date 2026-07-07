import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export const DEFAULT_TICKERS = [
  'AAPL',
  'GOOGL',
  'MSFT',
  'AMZN',
  'TSLA',
  'NVDA',
  'META',
  'JPM',
  'V',
  'NFLX',
];

/** Parses a header/table currency cell like "$10,000.00" into a number. */
export function parseCurrency(text: string): number {
  return Number(text.replace(/[^0-9.-]/g, ''));
}

export async function readCashBalance(page: Page): Promise<number> {
  const text = await page.getByTestId('cash-balance').innerText();
  return parseCurrency(text);
}

export async function readTotalValue(page: Page): Promise<number> {
  const text = await page.getByTestId('total-value').innerText();
  return parseCurrency(text);
}

/** Waits until a watchlist row has received at least one live SSE price tick. */
export async function waitForLivePrice(page: Page, ticker: string): Promise<void> {
  const row = page.getByTestId(`watchlist-row-${ticker}`);
  await expect(row).toBeVisible();
  await expect(row).not.toContainText('—', { timeout: 15_000 });
}
