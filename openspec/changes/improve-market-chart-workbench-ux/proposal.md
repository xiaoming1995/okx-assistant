## Why

The market chart currently presents its contract summary, connection metadata, and twelve K-line detail values with the same visual weight. This leaves too little room for the price trend, makes the important data hard to scan, and forces short desktop viewports into a scroll-first experience instead of a usable one-screen workbench.

## What Changes

- Reorganize the market chart into a clear hierarchy: persistent market summary, lightweight realtime status, and contextual K-line inspection details.
- Add a volume subchart and clearer latest-price/trend affordances so users can read price movement and activity together.
- Preserve a user's manual chart pan and zoom position during realtime updates; only follow new data automatically while the user is viewing the newest edge.
- Make the desktop chart workbench use the available viewport height efficiently, keeping the core summary, period controls, price chart, and volume view visible together at the supported desktop baseline.
- Keep detailed K-line values available on hover or focus without permanently dedicating a two-row grid to every field.
- Retain the existing contract rail, supported bar intervals, read-only market data behavior, and compliant TradingView attribution link.

## Capabilities

### New Capabilities

- `market-chart-workbench-ux`: A readable, trend-focused, realtime market chart workbench with contextual candle details and responsive desktop height behavior.

### Modified Capabilities

- None.

## Impact

- Affected frontend: market chart rendering and interactions in `frontend/src/main.tsx`, responsive chart layout and component styles in `frontend/src/styles.css`, and focused frontend tests.
- Uses the existing realtime candle payload, including its volume fields; no backend endpoint, market-data contract, trading action, or dependency change is required.
- Runtime acceptance will cover desktop viewports of 1280x720 and 1440x900, user-controlled chart navigation during realtime updates, and retained external attribution.
