## 1. Shared Stats View Model

- [x] 1.1 Extract reusable market-statistics derived state and formatting helpers for chart and detail surfaces.
- [x] 1.2 Keep selected-contract stats loading keyed by contract and effective statistics period, clearing stale contract values during reload.

## 2. Trading Data Detail Page

- [x] 2.1 Add a dedicated market trading data route that accepts the selected contract from the route query.
- [x] 2.2 Render current trading-structure summary plus detailed long/short account ratio, taker buy/sell, and open interest sections on the dedicated page.
- [x] 2.3 Provide contract selection and period controls on the dedicated page using existing market data patterns.

## 3. Chart Page Simplification

- [x] 3.1 Keep the compact trading-structure summary on the chart page and add a clear entry to the full trading data page.
- [x] 3.2 Remove the full trading-statistics detail panels from the chart page so the chart layout no longer clips lower content.
- [x] 3.3 Preserve observational labels and avoid direct trading instructions.

## 4. Verification

- [x] 4.1 Add or update focused frontend tests for route entry, compact chart summary, full detail rendering, and stale-data clearing.
- [x] 4.2 Verify desktop viewport layout does not hide full chart-page content behind non-scrollable parents.
- [x] 4.3 Run frontend tests and production build.
- [x] 4.4 Run `openspec validate move-market-trading-stats-to-detail-page --strict`.
