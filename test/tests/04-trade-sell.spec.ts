import { test, expect } from '@playwright/test';
import { readCashBalance } from './helpers';

// Depends on 03-trade-buy.spec.ts having left an open 5-share AAPL position.
test.describe('sell shares', () => {
  test('partial sell updates the position, full sell removes it', async ({ page }) => {
    await page.goto('/');

    const positionRow = page.getByTestId('position-row-AAPL');
    await expect(positionRow).toBeVisible();
    const cashBeforePartial = await readCashBalance(page);

    await page.getByLabel('Trade ticker').fill('AAPL');
    await page.getByLabel('Trade quantity').fill('2');
    await page.getByRole('button', { name: 'Sell' }).click();

    await expect(positionRow).toContainText('3');
    await expect
      .poll(async () => readCashBalance(page), { timeout: 10_000 })
      .toBeGreaterThan(cashBeforePartial);

    const cashBeforeFull = await readCashBalance(page);

    await page.getByLabel('Trade ticker').fill('AAPL');
    await page.getByLabel('Trade quantity').fill('3');
    await page.getByRole('button', { name: 'Sell' }).click();

    await expect(page.getByTestId('position-row-AAPL')).not.toBeVisible();
    await expect
      .poll(async () => readCashBalance(page), { timeout: 10_000 })
      .toBeGreaterThan(cashBeforeFull);
  });
});
