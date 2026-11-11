## 1. Market Summary and Responsive Workspace

- [x] 1.1 Refactor the market chart header and contract summary into persistent market values, compact 24-hour context, and separately styled realtime operational status.
- [x] 1.2 Replace the permanent twelve-card K-line details grid with a compact contextual candle inspector that distinguishes inspected candles from the latest candle.
- [x] 1.3 Update desktop chart-workbench layout rules so the summary, interval controls, price pane, and volume pane fit in the right workbench at 1280x720 and 1440x900 without required vertical scrolling.
- [x] 1.4 Add bounded compact-height and narrow-layout fallback rules that preserve core chart access and make remaining overflow reachable without clipping.

## 2. Chart Trend and Realtime Navigation

- [x] 2.1 Add a synchronized volume histogram pane from the existing candle volume data, including direction colors, unavailable-data behavior, and chart lifecycle cleanup.
- [x] 2.2 Keep the candlestick price pane visually dominant and retain a clear current-price/trend affordance while sharing the time scale with the volume pane.
- [x] 2.3 Replace unconditional realtime `fitContent()` behavior with explicit initial/context-change fitting and newest-edge auto-follow detection.
- [x] 2.4 Preserve manual historical pan or zoom and crosshair-selected candle context through realtime candle updates.
- [x] 2.5 Retain the header TradingView attribution link and keep the library attribution logo out of the chart plot.

## 3. Verification

- [x] 3.1 Extend focused frontend coverage for hierarchy, contextual candle inspection, volume-pane behavior, realtime navigation rules, responsive layout baselines, and retained attribution.
- [x] 3.2 Run the focused frontend tests, full frontend test suite, production build, and strict OpenSpec validation.
- [x] 3.3 Perform browser checks at 1280x720 and 1440x900 to confirm all core chart-workbench elements are visible without right-panel vertical scrolling.
- [x] 3.4 Perform a controlled realtime-update check after manually panning or zooming to historical candles, then recheck newest-edge auto-follow and the absence of `#tv-attr-logo`.
