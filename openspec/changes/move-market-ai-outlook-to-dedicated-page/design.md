## Context

The current market chart page owns contract selection, realtime ticker/candle updates, K-line rendering, and the full AI market-reading panel. The AI panel has expanded from a compact chart companion into a report surface with macro sources, three time horizons, source warnings, and reassessment notes. Keeping that full report inside the chart page competes with the K-line viewport and makes the page feel unstable or crowded when report text grows.

The backend AI endpoint is already independent and read-only. This change should therefore focus on frontend route boundaries, navigation, state handoff, and reusable market-list behavior rather than changing the AI analysis core.

## Goals / Non-Goals

**Goals:**

- Move the complete AI market-reading report into a dedicated market subpage.
- Keep the chart page focused on realtime price, selected-contract summary, K-line details, and a clear AI entry action.
- Preserve manual AI execution: no AI request on page load, realtime tick, candle update, or contract selection.
- Preserve selected contract and selected K-line period when navigating from the chart to the AI page.
- Reuse existing `POST /api/market/ai-outlook` and current response schema.
- Keep the AI report read-only and user-reference oriented.
- Reduce duplicated market instrument list/ticker behavior where practical.

**Non-Goals:**

- Do not change the backend outlook schema, prompt semantics, macro source implementation, or LLM provider configuration.
- Do not add automated trading actions, order prefill, leverage changes, or strategy creation from the AI page.
- Do not remove the chart page, K-line details, or realtime market data.
- Do not redesign all market navigation beyond adding the AI page entry.

## Decisions

### Decision: Add `market/ai-outlook` as a First-Class Market Route

Add a new market tab such as `aiOutlook` and route it to `#/market/ai-outlook`. The route should support `inst` and `bar` query params. Invalid or missing contracts fall back to the existing default contract; invalid bars fall back to `1m`.

Rationale: the report is a distinct workflow and benefits from a bookmarkable URL, stable vertical space, and direct navigation from the market module.

Alternative considered: open the report in a modal over the chart. This would keep the user near the chart, but the report now has enough content that a modal would require nested scrolling and would still compete with the chart.

### Decision: Keep the Chart Page as the Primary Entry Point

The chart page should retain an "AI看行情" action, but clicking it should navigate to the dedicated AI page with the current `inst` and `bar` instead of rendering the full report inline.

Rationale: users discover AI analysis while looking at a chart, but the actual reading experience gets a page designed for report content.

Alternative considered: remove the chart-page action and rely only on secondary navigation. That makes the route cleaner but weakens discoverability from the user's current workflow.

### Decision: Manual Trigger Remains Mandatory

The dedicated AI page should show an idle state for the selected contract until the user clicks "开始分析" or "刷新AI". Contract changes and bar changes should reset or mark the current report stale, but they must not automatically call the LLM endpoint.

Rationale: AI calls consume tokens and should remain user-controlled. It also prevents realtime market updates from causing repeated layout or content churn.

Alternative considered: auto-load a cached report on page entry. That feels smoother, but it can still surprise users by showing old analysis or issuing a backend request when they expected only navigation.

### Decision: Reuse a Shared Market Instrument Rail

Extract the repeated instrument-list, filter, sort, watchlist, and ticker-display UI into a shared component or hook used by the chart page, trading-data page, and AI page. If a full extraction is too large for one pass, implement the AI page with a small shared helper first and leave deeper deduplication as a follow-up task.

Rationale: the chart and trading-data pages already duplicate significant market-list behavior. Adding a third copy increases maintenance risk and can cause inconsistent names, sorting, or realtime price updates.

Alternative considered: duplicate the chart page list in the AI page. This is faster but leaves three parallel versions of the same behavior.

### Decision: Report Page Uses the Existing Panel as the Starting Point

Reuse `MarketAiOutlookPanel` or split it into a report component that can render in both compact and full-page modes during migration. The dedicated page should favor full-page readability: less aggressive line clamping, clearer source/warning placement, and stable card sizing for the three horizons.

Rationale: the current panel already encodes the right safety labels and response fields. A careful split reduces behavioral regression.

Alternative considered: rebuild the report UI from scratch. That gives maximum layout freedom but increases risk of dropping existing safety wording or fallback states.

### Decision: Keep Backend Unchanged Unless Route Needs Bar Normalization

The frontend should keep calling `POST /api/market/ai-outlook` with `instId`, `bar`, `limit`, and force flags. Backend changes are only needed if implementation discovers missing validation or a route-specific response field is truly necessary.

Rationale: the backend is already read-only, tested, and returns the required multi-horizon report data.

Alternative considered: add a new endpoint for the page. This is unnecessary because the page does not need a different analysis contract.

## Risks / Trade-offs

- [Risk] Users may miss the report if it disappears from the chart. -> Mitigation: keep a prominent chart-page entry action and add a market secondary tab.
- [Risk] Route state may drift when users switch contracts on the AI page. -> Mitigation: update the hash query when selected contract or bar changes.
- [Risk] Refactoring the market instrument rail may be larger than expected. -> Mitigation: keep the extraction narrow and verify chart, trading-data, and AI pages with focused static tests.
- [Risk] The AI page could still feel like a trading signal page. -> Mitigation: keep read-only labels, avoid execution wording, and do not provide any trade/order controls.
- [Risk] Existing chart-page tests may assume the panel is inline. -> Mitigation: update tests to assert chart entry behavior and add new tests for dedicated page rendering.

## Migration Plan

1. Add route parsing/building support for `#/market/ai-outlook?inst=...&bar=...`.
2. Add the market secondary tab labeled `AI看行情`.
3. Move AI request state and report rendering into a new dedicated page component.
4. Change the chart-page AI action to navigate to the dedicated page with the current contract and period.
5. Reuse or factor shared market instrument/ticker list behavior for the AI page.
6. Update static tests for routing, manual trigger behavior, safety wording, and dedicated report layout.
7. Run frontend tests/build and perform browser verification for chart entry and AI page report generation.

Rollback is straightforward: remove the `ai-outlook` route/tab and restore the inline chart-page panel from the previous implementation. The backend endpoint remains unaffected.

## Open Questions

- Should the AI page show a small live K-line preview, or only the report and selected-contract metrics in the first pass?
- Should the AI page remember the last generated report per contract/bar during the current browser session, or always show idle after navigation?
- Should "AI看行情" appear before or after "行情图表" in the market secondary navigation?
