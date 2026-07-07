import { test, expect } from '@playwright/test';

test.describe('SSE resilience', () => {
  test('reports reconnecting after a stream drop, then recovers to connected', async ({ page }) => {
    await page.goto('/');
    const dot = page.getByTestId('connection-status');
    await expect(dot).toHaveAttribute('data-status', 'connected', { timeout: 15_000 });

    // Sever the stream: abort every new request to the SSE endpoint so the
    // browser's native EventSource retry logic keeps failing to reconnect.
    await page.route('**/api/stream/prices', (route) => route.abort());
    await page.reload();

    await expect(dot).toHaveAttribute('data-status', 'reconnecting', { timeout: 15_000 });

    // Restore the endpoint; EventSource's built-in auto-retry (no page
    // reload needed) should re-establish the connection on its own.
    await page.unroute('**/api/stream/prices');

    await expect(dot).toHaveAttribute('data-status', 'connected', { timeout: 15_000 });
  });
});
