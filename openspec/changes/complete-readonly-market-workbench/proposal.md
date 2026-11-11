## Why

The current market chart shows price movement and moving averages, but its live page has no visible volume pane or order book. A viewer cannot compare a price move with traded activity or current bid/ask depth in one reading flow. The top `24h 量` also mixes possible ticker units and can fall back to a single candle, making its period and unit unclear.

## What Changes

- Restore a synchronized, unit-labelled candle-volume pane beneath the price chart. First reconcile the existing completed OpenSpec volume task with the current source and served page.
- Add a read-only order-book panel for the selected contract, showing nearby asks and bids, quantity in contracts, cumulative depth, spread, snapshot time, and explicit loading/cache/error states.
- Make the market summary and shared contract rail label the available 24-hour activity by its actual quote-currency, base-currency, or contract unit; no single-candle value may stand in for a 24-hour metric. Keep the UTC+8 day-change meaning visible.
- Keep price and volume dominant at desktop sizes; place depth below the chart when the main content is too narrow. Retain the shared contract rail, periods, chart inspection, and responsive reading order.
- Preserve the page as market observation. No order entry, order/position management, trading signal, or personal account data is added to the chart route.

## Capabilities

### New Capabilities

- `readonly-market-chart-depth`: A coherent price, volume, and public order-book reading surface with explicit units, data freshness, and responsive presentation.

### Modified Capabilities

- None. The related historical chart-workbench changes are under `openspec/changes/` and are not synced as base specs in `openspec/specs/`.

## Impact

- Frontend: `MarketPage` in `frontend/src/main.tsx`, chart/workbench rules in `frontend/src/styles.css`, and focused market/responsive tests.
- Backend: a public selected-contract order-book snapshot endpoint and bounded cache/refresh behavior in `backend/app/main.py`, with focused backend tests. Existing candle and ticker endpoints remain the sources for the price chart and summary.
- Runtime: adds public OKX market-data reads only. Existing trading, automation, AI analysis, routes, account permissions, and persistence are outside scope.
- Acceptance: desktop 1280x720 and 1440x900 plus narrow 390px, including first load, empty, retained-cache, failed-refresh, contract switch, keyboard focus, and disabled or unavailable controls.
