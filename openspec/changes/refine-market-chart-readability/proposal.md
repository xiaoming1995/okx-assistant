## Why

The market-chart page repeats a transient realtime status beneath its title, so an otherwise secondary gray message changes continuously and distracts from price information. In addition, the chart initially accepts cached candle batches without validating their ordering or continuity and fits every available candle into the viewport, allowing stale gaps or a single large move to flatten the price action users need to read.

## What Changes

- Remove the always-changing realtime status subtitle from the market-chart title area while retaining explicit source, freshness, and warning states in the existing operational-status and warning surfaces.
- Validate cached and realtime candle batches before they become chart data: normalize timestamp order, remove duplicate or invalid rows, detect period-sized gaps, and avoid presenting an unsuitable cache batch as a complete initial trend.
- Make the default chart camera focus on a bounded recent window of the retained candle history, so typical price movement remains visually legible without discarding the user's ability to pan through the full loaded range.
- Add a user-facing action that returns the chart to the newest focused window after historical exploration; retain the existing rule that realtime updates do not override a manually historical view.
- Streamline the candle reading surface so the primary inspected values are scannable and secondary detail remains available without competing with the price plot.

## Capabilities

### New Capabilities

- `market-chart-readability`: Quiet operational status, trustworthy initial candle presentation, and a user-controlled recent-trend camera for the market chart.

### Modified Capabilities

- None.

## Impact

- Affected frontend: `frontend/src/main.tsx`, `frontend/src/styles.css`, and focused static/browser-facing tests for the market chart.
- Affected backend: realtime public-candle seed and update handling in `backend/app/main.py`, with focused realtime coverage for cache validity behavior.
- Continues to use existing REST, cache, and WebSocket candle sources, the installed `lightweight-charts` library, supported bar intervals, and read-only market behavior; no trading action, API contract, or new dependency is introduced.
