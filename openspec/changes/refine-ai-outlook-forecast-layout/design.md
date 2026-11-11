## Context

The manual AI market report already separates current conclusion, chart evidence, conditional forecasts, freshness state, and secondary source details. Forecast cards are currently rendered in a fixed three-column grid, even when the response provides fewer than three horizons, and each card stacks every field vertically. The visual result is unused space and a much taller forecast block than its neighboring report sections.

## Goals / Non-Goals

**Goals:**

- Make one, two, and three usable forecast cards occupy their available desktop width evenly.
- Make the card hierarchy scannable: timeframe and confidence first, directional observation second, chart rationale third, and one concise re-read cue last.
- Preserve readable widths across desktop and laptop views before stacking cards on narrow displays.
- Retain all manual, chart-based, conditional, and read-only safeguards.

**Non-Goals:**

- Change the forecast response, its supported horizons, its generation prompt, or its chart-data basis.
- Hide a returned forecast, introduce price targets, or turn the reading into a trading instruction.
- Redesign the surrounding conclusion, evidence, rail, or source-details sections.

## Decisions

- Use a forecast-count layout marker on the existing forecast grid rather than a fixed `repeat(3, ...)` definition. This gives one item full width, two items equal width, and three items equal width without relying on empty grid tracks. CSS `auto-fit` was considered, but an explicit marker is more predictable for the bounded one-to-three response contract and easier to regression-test.
- Add a compact card header that holds the human-readable horizon and confidence badge on one row. Direction remains the visual title, so metadata does not compete with the conclusion.
- Retain the full chart-grounded summary and re-read condition, but reduce their margins and visually separate the condition as a single footer cue. This is preferred over line-clamping, which could silently hide the evidence that makes a conditional forecast understandable.
- Keep two cards side-by-side until the narrow-phone breakpoint. The current generic `1120px` single-column rule is suitable for the larger conclusion/evidence layout, but it is unnecessarily early for two concise forecast cards.

## Risks / Trade-offs

- [An unusually long model summary still makes one card taller] → Cards remain content-sized and preserve complete text; the more compact header and spacing limit unnecessary height without hiding information.
- [A future response adds an unsupported number of horizons] → The existing bounded response mapping still permits only known horizons, and the layout marker is derived from that bounded list.
- [Breakpoint changes could cause cramped cards] → Add static assertions for two-card layout and a browser check at desktop and narrow widths.

## Migration Plan

- Deploy with the frontend bundle only; no persisted data or API migration is required.
- Rollback consists of restoring the previous forecast-card markup and CSS; API responses and report cache remain compatible.

## Open Questions

- None. The screenshot and current bounded forecast contract establish the required one-to-three-card behavior.
