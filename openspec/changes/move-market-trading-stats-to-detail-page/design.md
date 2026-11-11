## Context

The market chart page uses a fixed-height application shell on desktop. After adding the trading-structure summary and three detailed statistics panels, the right-side chart area can exceed the available viewport while parent containers still hide overflow. This causes the lower trading-statistics content to be clipped on common desktop browser heights.

The existing backend already provides normalized contract statistics through `GET /api/market/stats`, and the frontend already has formatting helpers for long/short account ratio, taker buy/sell balance, open interest, loading states, period mismatch labels, and observational copy.

## Goals / Non-Goals

**Goals:**

- Restore a focused market chart page that fits better in the desktop workspace.
- Preserve a compact selected-contract trading-structure summary close to the K-line context.
- Provide a dedicated page for complete selected-contract trading statistics.
- Reuse the existing normalized market statistics endpoint and frontend formatting logic.
- Keep labels observational and avoid direct trading instructions.

**Non-Goals:**

- Do not change OKX Trading Statistics endpoint integration or backend response shape.
- Do not add new statistics sources such as top-trader ratios in this change.
- Do not feed trading statistics into automation or order submission logic.
- Do not redesign the full market navigation or instrument list.

## Decisions

### Use a Dedicated Page Instead of a Modal

Add a market-level route for full contract trading data and link to it from the chart summary.

Rationale: the detail content is analytical and likely to grow with additional periods or metrics. A dedicated page gives it stable vertical space, bookmarkable state, and simpler responsive behavior.

Alternative considered: open a modal over the chart. A modal is convenient for quick inspection, but it would still need internal scrolling on small and medium screens and would compete with the chart for context.

### Keep the Chart Page Summary Compact

The chart page should retain the current summary metrics and status chips but remove the three detailed trend panels from the chart layout.

Rationale: users can still see the current trading structure while inspecting price action, but the page no longer needs to fit full statistical history below the K-line.

Alternative considered: make the right pane scrollable while leaving all current content on the chart page. This fixes clipping, but it leaves the chart page dense and makes the main K-line less central.

### Reuse Market Stats Loading Logic Where Possible

Factor the trading-stats loading and derived summary logic so both the chart page and detail page can read the same selected-contract stats without duplicating fragile formatting rules.

Rationale: both surfaces need the same period fallback, warning handling, and observational labels. Reuse reduces drift between the summary and full view.

Alternative considered: duplicate the existing chart-page logic in the new page. That is faster initially, but it increases maintenance risk when stats labels or API shape change.

## Risks / Trade-offs

- [Risk] Users may not discover the full trading data page. -> Mitigation: add a clear chart-page entry labeled as a command to view the full contract trading data.
- [Risk] Route state can get out of sync with the currently selected contract. -> Mitigation: pass the selected contract through the route query and default to `BTC-USDT-SWAP` when absent.
- [Risk] Moving detail panels could feel like hiding useful data. -> Mitigation: keep the summary on the chart page and show the same current metrics at the top of the detail page.
- [Risk] Adding another market route can complicate navigation. -> Mitigation: keep it under the existing market section and reuse existing navigation patterns.
