import { test, expect } from '@playwright/test';

const MOCK_MESSAGE_SNIPPET = "I've analyzed your portfolio";

test.describe('AI chat', () => {
  test('sends a message and renders the mocked assistant response', async ({ page }) => {
    await page.goto('/');

    await page.getByLabel('Chat message').fill('What should I do with my portfolio?');
    await page.getByRole('button', { name: 'Send' }).click();

    // User bubble appears immediately (optimistic local append).
    await expect(page.getByTestId('chat-history')).toContainText('What should I do with my portfolio?');

    // Loading indicator shows while waiting, then the canonical LLM_MOCK
    // response (PLAN.md §9) is rendered as the assistant's reply.
    await expect(page.getByTestId('chat-history')).toContainText(MOCK_MESSAGE_SNIPPET, { timeout: 10_000 });
    await expect(page.getByTestId('chat-loading')).not.toBeVisible();
  });

  test('shows executed trade and watchlist actions inline', async ({ page }) => {
    // The canonical LLM_MOCK response is deliberately action-free (PLAN.md §9),
    // so a real mocked round-trip never carries trades/watchlist_changes.
    // Route interception exercises the frontend's inline-confirmation
    // rendering for the case where the LLM *does* return executed actions.
    await page.route('**/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Done — bought 5 shares of AAPL and added PYPL to your watchlist.',
          actions: {
            trades: [
              {
                status: 'executed',
                id: 'test-trade-1',
                user_id: 'default',
                ticker: 'AAPL',
                side: 'buy',
                quantity: 5,
                price: 190.5,
                executed_at: new Date().toISOString(),
              },
            ],
            watchlist_changes: [{ status: 'executed', ticker: 'PYPL', action: 'add' }],
          },
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/');
    await page.getByLabel('Chat message').fill('Buy 5 AAPL and add PYPL to my watchlist');
    await page.getByRole('button', { name: 'Send' }).click();

    const summary = page.getByTestId('chat-action-summary').last();
    await expect(summary).toBeVisible();
    await expect(summary).toContainText('Bought 5 AAPL @ $190.50');
    await expect(summary).toContainText('Watchlist: added PYPL');
  });
});
