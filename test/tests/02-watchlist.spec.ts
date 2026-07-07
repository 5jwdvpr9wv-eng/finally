import { test, expect } from '@playwright/test';
import { waitForLivePrice } from './helpers';

const NEW_TICKER = 'PYPL';

test.describe('watchlist management', () => {
  test('adds and removes a ticker', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByTestId(`watchlist-row-${NEW_TICKER}`)).not.toBeVisible();

    await page.getByLabel('Add ticker to watchlist').fill(NEW_TICKER);
    await page.getByRole('button', { name: 'Add' }).click();

    await expect(page.getByTestId(`watchlist-row-${NEW_TICKER}`)).toBeVisible();
    await waitForLivePrice(page, NEW_TICKER);

    await page.getByLabel(`Remove ${NEW_TICKER} from watchlist`).click();
    await expect(page.getByTestId(`watchlist-row-${NEW_TICKER}`)).not.toBeVisible();

    // Reconciles with the backend on reload rather than only an optimistic update.
    await page.reload();
    await expect(page.getByTestId(`watchlist-row-${NEW_TICKER}`)).not.toBeVisible();
  });
});
