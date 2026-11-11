## 1. Layout Fix

- [x] 1.1 Add a desktop short-height CSS rule for the market chart workspace.
- [x] 1.2 Make the right market content area scroll vertically when short-height content overflows.
- [x] 1.3 Reduce chart minimum height only inside the short-height breakpoint.
- [x] 1.4 Keep the lower metrics row stable and reachable without changing market data rendering.
- [x] 1.5 Preserve a usable chart plot area on short-height screens by compacting surrounding summary chrome before over-compressing the chart.
- [x] 1.6 Move the TradingView attribution out of the chart plot area so it no longer appears as an icon overlay.

## 2. Verification

- [x] 2.1 Add static frontend coverage for the short-height market chart CSS rules.
- [x] 2.2 Run frontend tests and production build.
- [x] 2.3 Rebuild/restart frontend and verify the reported short-height viewport in browser.
- [x] 2.4 Re-verify that the chart area remains usable and the lower metrics stay visible at the reported short-height viewport.
- [x] 2.5 Verify the chart plot area no longer renders the `tv-attr-logo` overlay.
