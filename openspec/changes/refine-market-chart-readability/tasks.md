## 1. Candle Batch Integrity

- [x] 1.1 Define supported-bar durations and shared backend candle normalization that filters invalid timestamps, sorts ascending, and de-duplicates rows.
- [x] 1.2 Classify normalized cache batches for interval continuity and freshness before sending a cache seed for the selected contract and period.
- [x] 1.3 Update REST-seed, WebSocket, and unavailable-current-source paths to persist/send normalized data and expose an explicit degraded warning when only unsuitable persisted history remains.
- [x] 1.4 Add focused backend tests for normalization, duplicate handling, gap/freshness suitability, valid cache seeding, invalid-cache REST recovery, and degraded fallback behavior.

## 2. Readable Market-Chart Interaction

- [x] 2.1 Remove the routine-changing market-chart title subtitle while retaining source, freshness, and warning states in the existing status and notice surfaces.
- [x] 2.2 Normalize received candle payloads defensively in the frontend before setting chart state and represent degraded candle-source warnings without misleading live status.
- [x] 2.3 Add a reusable newest-window camera that focuses the initial or changed chart context on the latest 80 candles while retaining the full loaded history.
- [x] 2.4 Add an explicit `最新` control that applies the newest-window camera without refetching or resetting the selected contract, interval, historical navigation, or contextual inspector.
- [x] 2.5 Refine the contextual candle inspector to emphasize timestamp, OHLC, signed change, and volume, with amplitude and quote turnover available as secondary detail.
- [x] 2.6 Preserve synchronized volume, manual historical pan/zoom protection, and the existing external TradingView attribution without the in-plot logo.

## 3. Verification

- [x] 3.1 Extend focused frontend coverage for title-status removal, normalized/degraded candle handling, newest-window calculation, `最新` control, inspector hierarchy, and attribution retention.
- [x] 3.2 Run focused backend realtime tests, the full backend suite as appropriate, frontend tests, production build, and strict OpenSpec validation.
- [x] 3.3 Verify in a browser at 1280x720 and 1440x900: no moving title subtitle, clear initial recent candle movement, volume synchronization, and no required right-workbench vertical scroll.
- [x] 3.4 Verify valid and degraded seed paths, manual historical pan during a realtime update, the `最新` return control, and `document.querySelectorAll('#tv-attr-logo').length === 0`.
