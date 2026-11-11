## 1. Routing and Navigation

- [x] 1.1 Add `aiOutlook` to the market route state and parse `#/market/ai-outlook`.
- [x] 1.2 Preserve `inst` and `bar` query parameters for the AI outlook route, with safe defaults for invalid values.
- [x] 1.3 Add `AI看行情` to the market secondary navigation and mark it active on the dedicated route.
- [x] 1.4 Ensure `buildAppHash` emits the correct AI outlook route and query string.

## 2. Shared Market Selection

- [x] 2.1 Identify duplicated market instrument list, filter, sort, watchlist, and ticker display logic in chart and trading-data pages.
- [x] 2.2 Extract a reusable market instrument rail component or hooks with selected contract, filters, sorting, watch toggles, and ticker display.
- [x] 2.3 Adopt the shared rail in the chart page without changing existing chart behavior.
- [x] 2.4 Adopt the shared rail in the trading-data page without changing existing trading-data behavior.

## 3. Dedicated AI Outlook Page

- [x] 3.1 Create a `MarketAiOutlookPage` component under the market section.
- [x] 3.2 Render selected-contract context, latest ticker metrics, K-line period controls, and manual `开始分析` / `刷新AI` controls.
- [x] 3.3 Move AI outlook request state into the dedicated page and keep it manually triggered only.
- [x] 3.4 Render the complete AI report on the dedicated page using the existing outlook response schema.
- [x] 3.5 Update the route query when the user changes selected contract or K-line period, without automatically requesting analysis.
- [x] 3.6 Show idle, loading, success, fallback, warning, cached, and error states in a stable layout.

## 4. Chart Page Entry

- [x] 4.1 Remove the full inline AI report panel from the market chart page.
- [x] 4.2 Change the chart-page `AI看行情` action to navigate to `#/market/ai-outlook` with current `inst` and `bar`.
- [x] 4.3 Keep chart price, K-line details, realtime state, and warning behavior unchanged.

## 5. Safety and Copy

- [x] 5.1 Keep the dedicated page labeled as user reading reference and not an automated trading signal.
- [x] 5.2 Ensure the page does not render trade submission, order prefill, strategy creation, automation mutation, or leverage controls.
- [x] 5.3 Preserve wording that the report will not place orders and will not affect automated trading.

## 6. Tests and Verification

- [x] 6.1 Update AI outlook static tests to assert the report lives on the dedicated page and the chart page only navigates to it.
- [x] 6.2 Add route/navigation static coverage for `#/market/ai-outlook?inst=...&bar=...`.
- [x] 6.3 Add layout/static coverage for the dedicated report sections and read-only safety wording.
- [x] 6.4 Run frontend tests and build.
- [x] 6.5 Run OpenSpec strict validation for this change.
- [x] 6.6 Manually verify in browser: chart page entry navigates to AI page, no AI request runs on page load, manual analysis renders the three horizons, and returning to the chart leaves realtime K-line behavior intact.
