## 1. Compact Shared Rail Controls

- [x] 1.1 Refactor `MarketInstrumentRail` to show readable local-followed and total counts, with `已关注` and `全部` as the persistent primary range controls.
- [x] 1.2 Move the existing USDT-settled, tradable-only, and coin-settled ranges into an accessible compact filter control that visibly reflects an active advanced range.
- [x] 1.3 Move existing default, change, and volume sort modes into an accessible compact sort control that visibly reflects the selected mode.
- [x] 1.4 Add a market-workbench owner for the single rail's search, filter, sort, instrument snapshot, ticker snapshot, refresh, and local watch-toggle state while preserving route-level selected-contract ownership.

## 2. Row Hierarchy and Responsive Styling

- [x] 2.1 Remove the redundant rail list legend and refine each contract row's code, readable name, perpetual/settlement context, price, daily change, and star-action hierarchy.
- [x] 2.2 Add compact-control, active-state, popover, truncation, and narrow-layout styles so the rail remains usable without horizontal clipping.
- [x] 2.3 Keep the chart-only local-followed empty state and `查看全部合约` recovery action compatible with the compact controls, without changing the selected chart contract or local watchlist implicitly.

## 3. Coverage and Verification

- [x] 3.1 Extend focused frontend tests for primary and advanced range selection, compact sorting, local-followed terminology/counts, row semantics, and selection/watchlist independence.
- [x] 3.2 Run the frontend test suite, production build, and strict OpenSpec validation.
- [ ] 3.3 Verify in a browser at desktop and narrow widths that all three market pages expose the concise rail, advanced controls are accessible, long contract metadata does not clip, and local-followed empty-state recovery preserves the current contract.

## 4. Shared Market Workbench

- [x] 4.1 Render one stable market workbench rail around the chart, AI outlook, and trading-data right-side views, retaining direct-entry defaults while preserving state during tab switches.
- [x] 4.2 Remove the three duplicate rendered rail instances and route their selected-contract actions through the shared workbench without changing page-specific candle, AI, or statistics requests.
- [x] 4.3 Extend Radar actions to open a candidate directly in chart, AI outlook, or trading data with the route-level selected contract set correctly.
- [x] 4.4 Add focused frontend coverage for one shared rail mount, cross-tab search/filter/sort continuity, direct-entry defaults, and Radar-to-workbench target routing.
- [x] 4.5 Refactor the chart, AI outlook, and trading-data panels to consume the workbench's selected contract, instrument/ticker snapshot, ticker source/update state, and one shared ticker realtime subscription; preserve the chart's independent candle subscription and each page's AI/statistics work.
- [ ] 4.6 Run the frontend test suite, production build, strict OpenSpec validation, and browser verification of cross-tab continuity at desktop and narrow widths.
- [x] 4.7 Preserve Radar candidate visibility by initializing chart, AI outlook, and trading-data workbenches in the complete range only for a Radar handoff; retain direct-entry defaults and make compact rail controls use stable two-row desktop layout.
- [ ] 4.8 Extend focused coverage and verify Radar-to-workbench range behavior plus desktop/narrow control readability.

## 5. Collapsible Desktop Rail

- [x] 5.1 Add workbench-owned desktop rail collapse state and accessible expand/collapse controls without remounting or resetting the shared rail context.
- [x] 5.2 Add responsive grid and rail styles that free horizontal space on desktop but keep the full rail visible at the existing single-column breakpoint.
- [ ] 5.3 Add focused coverage, run frontend tests/build/strict validation, and verify desktop/narrow collapse behavior in a browser.
