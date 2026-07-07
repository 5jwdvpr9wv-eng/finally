import { test, expect } from '@playwright/test';
import { readCashBalance, waitForLivePrice } from './helpers';

test.describe('buy shares', () => {
  test('reduces cash and opens a position', async ({ page }) => {
    await page.goto('/');
    await waitForLivePrice(page, 'AAPL');

    const cashBefore = await readCashBalance(page);

    await page.getByLabel('Trade ticker').fill('AAPL');
    await page.getByLabel('Trade quantity').fill('5');
    await page.getByRole('button', { name: 'Buy' }).click();

    const positionRow = page.getByTestId('position-row-AAPL');
    await expect(positionRow).toBeVisible();
    await expect(positionRow).toContainText('5');

    await expect
      .poll(async () => readCashBalance(page), { timeout: 10_000 })
      .toBeLessThan(cashBefore);
  });
});
