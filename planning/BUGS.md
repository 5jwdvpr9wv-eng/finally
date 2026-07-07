# FinAlly Bug Tracker

Filed by the Integration Tester during E2E test development. Format: symptom,
failing test, repro steps, owning component, status.

---

## BUG-001: MainChart canvas overlaps and blocks the Trade bar's Buy/Sell buttons

- **Owner:** frontend-engineer
- **Status:** fixed
- **Failing tests:** `test/tests/03-trade-buy.spec.ts`, `test/tests/04-trade-sell.spec.ts` (blocked by 03), `test/tests/05-portfolio-viz.spec.ts`
- **Symptom:** Clicking the "Buy" (or "Sell") button in the Trade bar times out. Playwright reports the click target is obscured: `<canvas width="548" height="28"></canvas> from <div class="h-80 min-h-0">…</div> subtree intercepts pointer events`.
- **Root cause:** `frontend/src/components/MainChart.tsx:29-38` calls `createChart(containerRef.current, { ..., height: 320, ... })` — the chart height is hardcoded to 320px rather than measured from the container's actual available space. The chart's parent box (`<div className="h-80 min-h-0">` in `frontend/src/app/page.tsx`, 320px total) also contains the "Chart" header row and `p-3` padding, so the actual space left for the chart body is well under 320px. Lightweight Charts renders its canvas at the requested 320px regardless, so the canvas overflows the flex box and visually/functionally overlaps the TradeBar rendered directly below it in the layout, stealing pointer events from its buttons.
- **Repro steps:**
  1. Load the app, select any ticker (or use the default selection).
  2. Attempt to click the Buy or Sell button in the Trade bar (directly below the main chart).
  3. The click is intercepted by the chart's canvas element instead of reaching the button.
- **Suggested fix direction:** measure the container's actual `clientHeight` (e.g. via `containerRef.current.clientHeight` or a `ResizeObserver`) and pass that to `createChart`/`chart.applyOptions` instead of the hardcoded `320`, and/or add `overflow-hidden` to the chart's wrapping div as a safety net.
- **Fix applied:** `frontend/src/components/MainChart.tsx` — `createChart` now sizes off `containerRef.current.clientHeight` (measured, not hardcoded) instead of a literal `320`. Replaced the `window` `resize` listener with a `ResizeObserver` on the chart container so the canvas is re-measured and re-sized (`chart.applyOptions({ width, height })`) whenever the container's actual box changes, not just on window resize. Added `overflow-hidden` to both the chart's relative wrapper and the `containerRef` div as a safety net so the canvas can never visually overflow into sibling elements (like the TradeBar) even if a future sizing regression is introduced.
- **Verification:** `npm test` (25/25 component tests pass) and `npm run build` (static export) both succeed with no errors. Re-run `test/tests/03-trade-buy.spec.ts`, `04-trade-sell.spec.ts`, `05-portfolio-viz.spec.ts` to confirm the Playwright scenarios are unblocked.
- **E2E confirmation (integration-tester):** rebuilt the Docker image from scratch (`docker compose -f test/docker-compose.test.yml build --no-cache finally`) and ran the full Playwright suite against the real container. `03-trade-buy.spec.ts`, `04-trade-sell.spec.ts`, and `05-portfolio-viz.spec.ts` all pass — Buy/Sell clicks are no longer intercepted by the chart canvas. Full suite: 8/8 passed. Closing this bug.
