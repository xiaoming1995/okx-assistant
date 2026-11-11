## 1. Chart-Only Default and Empty-State Recovery

- [x] 1.1 Change only `MarketPage` to initialize the left contract filter as `自选`, while retaining existing defaults for AI outlook and trading-data pages.
- [x] 1.2 Add a clear market-chart empty self-selected state with a `查看全部合约` action that changes only the local filter and does not mutate the watchlist or current chart selection.
- [x] 1.3 Preserve direct-route/current-contract rendering and existing star add/remove behavior when the selected contract is absent from the self-selected rail.

## 2. Coverage and Verification

- [x] 2.1 Extend focused frontend tests for the chart-only self-selected default, empty-state restore action, unchanged adjacent-page defaults, and no implicit watchlist/selection mutation.
- [x] 2.2 Run the frontend test suite, production build, and strict OpenSpec validation.
- [ ] 2.3 Verify in a browser with populated and empty self-selected states: the chart page defaults to `自选`, `查看全部合约` restores the rail without changing the current chart, a direct non-self-selected contract remains visible, and adjacent market pages retain their current default filters.
