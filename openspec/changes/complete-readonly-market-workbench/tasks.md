## 1. Reconcile Existing Chart and Summary

- [x] 1.1 Compare `improve-market-chart-workbench-ux` volume requirements with current chart source, focused tests, and the served bundle; record the concrete gap before changing the chart.
- [x] 1.2 Add the synchronized SWAP candle-volume histogram and unavailable-volume state while preserving MA series, price scale, crosshair/node detail, and manual historical navigation.
- [x] 1.3 Make the top summary and shared rail label available 24-hour quote, base, or contract activity by its actual unit; keep UTC+8 day change on `sodUtc8` and avoid different-period fallbacks.
- [x] 1.4 Add focused tests for volume alignment, unit/unavailable semantics, selected-candle consistency, historical-view retention, and summary-basis fallback behavior.

## 2. Public Order-Book Data

- [x] 2.1 Add a credential-free OKX order-book client method and normalize up to 10 valid ask/bid levels per side for a validated SWAP instrument, retaining source timestamp and string numeric precision.
- [x] 2.2 Expose `GET /api/market/order-book?instId=...` with a short per-instrument memory cache, coalesced refresh, failure backoff, explicit age/state metadata, and no raw upstream exception in user-facing responses.
- [x] 2.3 Bound retained snapshots to 15 seconds; verify invalid contract, empty book, missing side, invalid/crossed prices, concurrent requests, failed refresh, and expired-cache cases with backend tests.

## 3. Depth Panel and Responsive Workbench

- [x] 3.1 Add a selected-contract read-only depth panel with nearest asks/bids, per-level and cumulative `张` quantities, valid spread, snapshot time, and distinct initial/loading/updating/cache/empty/unavailable feedback.
- [x] 3.2 Poll only while the chart route and document are visible; cancel or ignore stale requests when the contract changes and never show the previous contract's levels under the new heading.
- [x] 3.3 Place depth beside the chart only when main-content width permits, otherwise below synchronized price and volume panes; preserve the shared rail and existing design tokens.
- [x] 3.4 Add focused frontend coverage for selected-contract isolation, statuses, no order-entry controls, responsive reading order, and accessible labels/focus.

## 4. Runtime Acceptance

- [x] 4.1 Run focused backend/frontend tests, the relevant full suites, production build, and `openspec validate complete-readonly-market-workbench --strict`.
- [x] 4.2 Verify the served route at 1280x720, 1440x900, and 390px with a populated book; confirm volume alignment, summary units, spread, chart readability, panel placement, and no page-wide horizontal overflow.
- [x] 4.3 Verify contract/period switching and initial, empty, cached, failed-refresh, expired, keyboard-focus, and relevant disabled states in the browser; distinguish served-page results from source/build results.
