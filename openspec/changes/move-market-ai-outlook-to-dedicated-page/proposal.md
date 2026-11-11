## Why

The market chart page now carries realtime K-line content and a full AI market-reading report in the same viewport, making the chart page visually dense and harder to scan. The AI report has grown into its own workflow with macro context, multi-horizon outlooks, sources, and reassessment notes, so it needs a dedicated page while the chart remains a clear entry point.

## What Changes

- Add a dedicated market subpage for AI market outlook reports, reachable from the market navigation and from the chart page.
- Keep the market chart page focused on selected-contract price, K-line details, and a lightweight "AI看行情" entry action.
- Preserve the existing read-only backend `POST /api/market/ai-outlook` API and current report schema.
- Carry selected contract and K-line period through the route, for example `#/market/ai-outlook?inst=ETH-USDT-SWAP&bar=1m`.
- Render the complete AI report only on the dedicated page, including overall view, future 15-minute view, future 1-hour view, today view, key factors, K-line factors, focus items, reassessment conditions, sources, and reference notes.
- Reuse or factor the market instrument list/ticker loading patterns so the chart, trading-data page, and AI outlook page do not drift.
- Keep the report explicitly observational: no order placement, order prefill, strategy creation, automation mutation, or trading-signal language.

## Capabilities

### New Capabilities
- `market-ai-outlook-page`: Dedicated page and navigation behavior for viewing user-triggered AI market outlook reports under the market module.

### Modified Capabilities
- None.

## Impact

- Frontend routing: add `market/ai-outlook` route state and market secondary navigation entry.
- Frontend chart page: replace the embedded full AI report panel with a lightweight entry action that preserves current `inst` and `bar`.
- Frontend AI page: add a dedicated report page with selected-contract context, K-line period controls, manual analysis/refresh controls, report states, sources, warnings, and read-only labels.
- Frontend shared code: likely factor reusable market instrument list and ticker-loading behavior from the chart and trading-data pages.
- Tests: update existing AI outlook static tests and add route/navigation tests for the dedicated page and chart-page entry.
- Backend/API: no response-shape change expected; use the existing read-only endpoint.
