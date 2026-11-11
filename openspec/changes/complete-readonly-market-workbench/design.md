## Context

The selected contract, ticker, and candle snapshot are owned by `MarketContractWorkspace`; `MarketPage` owns the chart presentation. The served desktop chart currently has candlesticks, MA5/10/20, a contextual candle inspector, and no volume histogram. `improve-market-chart-workbench-ux` records a completed volume task, so source and served-bundle behavior need reconciliation before implementation. The chart route has no order-book API or component today. The existing design guide requires a restrained light workbench, explicit data-state language, and desktop/narrow verification.

Implementation audit (2026-10-19): the prior task `2.1` is checked, but `MarketPage` creates only `CandlestickSeries` and three `LineSeries`; `marketChartPresentation.static.test.mjs` does not assert a histogram. The served `#/market/chart` at desktop width likewise shows only the price pane. The current `frontend/dist` bundle is generated from this chart source. Treat volume as missing behavior and add a behavioral regression check before considering it restored.

## Goals / Non-Goals

**Goals:**

- Show price and candle volume on one synchronized timeline, preserving the current chart-navigation and inspection behavior.
- Show current public bid/ask depth for the selected contract with unambiguous contract quantity, spread, timestamp, and freshness.
- Give the top turnover and change figures a stable period and unit meaning.
- Preserve chart legibility across the existing shared-rail breakpoints and operational states.

**Non-Goals:**

- No order placement, personal orders or positions, automatic trading, recommendations, or dark-theme redesign.
- No full-depth incremental book reconstruction, new persisted market history, or multi-contract depth subscriptions in this release.
- No mark/index price, recent-trades stream, or new indicator controls until the core price/volume/depth reading is accepted.

## Decisions

### 1. Reconcile the volume feature before extending the chart

Compare the current chart source, served bundle, and prior OpenSpec task. Render a `lightweight-charts` histogram in a separate pane from existing candle `volume` values, sharing the same time scale and selected instrument/bar. Keep the price pane larger. Label the histogram `成交量（张）` only for verified SWAP candle data. Treat missing or invalid values as unavailable, not zero. Crosshair inspection and the node-detail dialog must refer to the same selected candle and source. Preserve the existing rule that a historical pan/zoom is not reset by a realtime update.

An overlaid histogram was considered; it would obscure price candles and price-scale reading. A second data API is unnecessary because the candle payload already carries volume.

### 2. Use bounded REST snapshots for the first order-book release

Add a public, credential-free client method for OKX `GET /api/v5/market/books`, requesting 10 levels per side for one validated SWAP instrument. Expose `GET /api/market/order-book?instId=...` through the backend with normalized string prices and quantities, `instId`, source snapshot `ts`, server `receivedAt`, `cacheAgeMs`, `state`, and a short Chinese status. The backend holds an in-memory cache keyed by contract with a roughly two-second freshness target, coalesces concurrent requests, and backs off after failures. A retained complete snapshot is displayable for at most 15 seconds with a visible `缓存` label and age; after that, rows are replaced by an unavailable state. Do not persist snapshots or expose raw upstream errors to the browser. Check instrument identity against supported SWAP instruments and bound request depth server-side.

The frontend polls the endpoint about every three seconds only while the chart route is visible, pauses when the document is hidden, and discards late responses for a previously selected contract. It distinguishes initial loading, fresh, updating with retained rows, cached, empty, and unavailable states. It never paints the previous contract's rows under the new contract heading. This fits a reading tool without the complexity of reconstructing incremental WebSocket books; the polling and cache intervals can be tuned after runtime observation. The public OKX API documents the order-book endpoint and contract-unit quantity: https://www.okx.com/docs-v5/en/ .

### 3. Keep depth presentation precise and secondary to the chart

Present the nearest 10 ask and 10 bid levels around a central spread row, with price, `数量（张）`, and `累计（张）`. Display asks above the spread and bids below it; use restrained red/green plus explicit `卖`/`买` labels. Derive spread from best ask and bid in the same snapshot. If either side is missing, prices are invalid, or ask is not above bid, omit the normal spread and show a data warning. Depth bars are only a visual aid and must not suggest executable liquidity or a trading action.

Place depth beside the combined chart when the right workbench has sufficient width, using a bounded panel width; otherwise put it below the chart in document flow. The shared 352px/48px rail behavior stays in `MarketContractWorkspace`. At 1280x720 the price and volume panes remain readable and the book may flow below them; at 1440x900 they may share a row if the available content width permits. At <=1200px retain the existing single-column rail-first flow; at <=767px keep summary, chart, volume, then depth in that order without document-wide horizontal overflow. Existing design tokens, Mantine controls, focus rings, and reduced-motion rules apply.

### 4. Give summary metrics one verified basis each

Use `volCcyQuote24h` only for `24h 成交额（<quote currency>）`. When it is absent, change the label and unit to `24h 成交量（<base currency>）` for `volCcy24h`, or `24h 成交量（张）` for `vol24h`. If all are missing, show an unavailable value. Never substitute the latest candle's quote volume for a 24-hour figure. Apply the same unit-aware wording in the shared contract rail. Calculate `今日涨跌（UTC+8）` only from `sodUtc8`; do not silently fall back to UTC+0 or rolling 24-hour open. Keep price/K-line source and update state separate from market values. The local ETH ticker observed during implementation had no `volCcyQuote24h` but had `volCcy24h`; the old rail prefixed the base-currency volume with `$`, motivating this explicit fallback.

## Risks / Trade-offs

- [Order-book snapshots age quickly] → Always show source time and freshness; cap retained rows at 15 seconds and omit rows beyond that age.
- [Many viewers amplify public API calls] → Share short-lived backend cache and in-flight refresh per instrument, poll only the visible selected chart, and back off after failures.
- [A wide book compresses candles] → Use main-content width to decide side-by-side versus stacked layout, preserving price and volume pane space.
- [Quantity units vary by instrument] → Scope V1 to the supported SWAP contract context, label quantities in contracts, and reject data that cannot be identified safely.
- [Historical OpenSpec completion differs from runtime] → Audit source and served bundle before changing the chart, then validate the resulting histogram in the browser rather than relying on task checkboxes.

## Migration Plan

1. Record the current chart and served-bundle discrepancy; implement and verify the volume pane and summary-basis correction using existing data.
2. Add the public client method, normalized endpoint, bounded memory cache, and backend contract tests.
3. Add the depth panel and responsive layout, then verify desktop and narrow visual and interaction states.
4. Deploy backend before frontend. If the endpoint is unavailable, the chart still loads and the depth region reports unavailable without blocking price or volume.
5. Roll back by reverting the frontend/backend additions; no database migration or persisted user setting is involved.

## Open Questions

- None blocking the first release. The exact cache and poll intervals should be adjusted only if measured runtime behavior or upstream rate limits require it.
