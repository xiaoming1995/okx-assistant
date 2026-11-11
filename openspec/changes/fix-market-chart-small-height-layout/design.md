## Context

The market chart page is arranged inside a `100vh` application shell. At desktop widths, `body`, `.appShell`, `.marketLayout`, and `.marketMain` all hide overflow. The right panel contains the workspace header, contract summary, trading structure summary, chart panel, and lower metrics row. When the viewport height is short, the lower metrics row extends below the viewport and is clipped by `.marketMain`.

## Goals / Non-Goals

**Goals:**
- Make the market chart page usable at short desktop heights.
- Preserve the fixed workbench feel on normal desktop heights.
- Keep the chart visible and usable while allowing lower metrics to be reached.
- Avoid changing data loading, API behavior, or market-stat calculations.

**Non-Goals:**
- Do not redesign the market page.
- Do not change mobile layout behavior beyond avoiding regressions.
- Do not remove the lower metric row.

## Decisions

1. Add a desktop short-height media query instead of globally changing `body` scrolling.
   - Rationale: the reported issue happens at wide desktop width with limited height, not at mobile widths. A scoped query avoids destabilizing unrelated pages.
   - Alternative considered: set `body { overflow:auto }` globally. That would fix clipping but can make the whole app shell and side rail scroll together, weakening the current workbench layout.

2. Enable vertical scrolling on `.marketMain` only for short desktop-height screens.
   - Rationale: the right content column is the part that overflows. The left contract list already has its own scroll behavior.
   - Alternative considered: only reduce chart height. That can still fail when trading-stat warnings or wrapped controls increase the top content height.

3. Reduce chart minimum height in the short-height media query.
   - Rationale: scrolling solves reachability, while a smaller chart minimum height keeps more content visible without forcing immediate scroll.

## Risks / Trade-offs

- Short-height users may see a slightly smaller chart -> limited to short desktop-height screens, and the chart remains the largest flexible region.
- Nested scrolling can feel less simple than page scrolling -> scoped to the overflowing right content area so the contract list remains stable.
- Future panels above the chart can add height again -> browser verification should assert the bottom metrics are reachable, not just that CSS rules exist.
