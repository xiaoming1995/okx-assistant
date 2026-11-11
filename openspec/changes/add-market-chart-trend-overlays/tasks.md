## 1. Deterministic Chart-Derived Data

- [x] 1.1 Add frontend utilities that calculate MA5, MA10, and MA20 from normalized retained candle closes, preserve timestamp alignment, and omit values before valid lookback history exists.
- [x] 1.2 Replace the fixed 80-candle camera calculation with an at-most-48-candle newest window while retaining complete loaded history and the existing historical-view protection.
- [x] 1.3 Add pure helpers for selected-bar close timing and visible logical-range high/low selection, including empty, short, invalid, and same-candle-extrema cases.
- [x] 1.4 Extend focused frontend tests for moving-average output, selected/newest legend values, focused window bounds, countdown eligibility, and visible-range extrema clamping.

## 2. Trend-Oriented Chart Presentation

- [x] 2.1 Add MA5, MA10, and MA20 line series to the existing price pane with the documented colors, no competing price labels, and synchronized updates alongside candlesticks and volume.
- [x] 2.2 Add a compact, color-matched in-plot trend legend that follows the crosshair-selected candle or newest candle and presents unavailable values clearly.
- [x] 2.3 Preserve the latest-price anchor and add an unconfirmed-candle closing countdown; add bounded high/low annotations that update with the visible range without displacing a manually historical view.
- [x] 2.4 Refine responsive chart, legend, and annotation layout so the active price label, trend legend, extrema labels, inspector, and volume pane remain legible at the supported workbench viewports.
- [x] 2.5 Preserve read-only boundaries: do not add signals, recommendations, order-entry actions, new API routes, persistent preferences, or external dependencies.

## 3. Verification

- [x] 3.1 Run focused frontend tests, the full frontend test suite, production build, and strict OpenSpec validation.
- [x] 3.2 Verify in a browser at 1280x720 and 1440x900 across 1m and 15m: MA5/10/20 colors and values match their lines, the initial view is at most 48 candles, price/volume remain clear, and no required workbench content is vertically clipped.
- [x] 3.3 Verify short-history and historical-pan states: unavailable MA values do not fabricate data, realtime updates preserve historical navigation, `最新` returns to the recent view, countdown appears only for an active candle, extrema stay bounded to the visible range, and the TradingView attribution link remains while `#tv-attr-logo` stays absent.
