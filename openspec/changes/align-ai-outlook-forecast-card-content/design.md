## Context

The existing forecast grid gives one, two, or three cards equal outer columns. Each card still lays out its header, direction, summary, and re-read condition in normal document flow. Because the direction and summary are generated text, a line wrap in one card changes the vertical position of the later content in that card without a shared internal alignment contract.

## Goals / Non-Goals

**Goals:**

- Keep metadata, directional observation, summary, and re-read cue in a predictable top-to-bottom hierarchy across a shared forecast row.
- Bottom-align the re-read cue while retaining complete generated explanation.
- Reserve a consistent two-line direction track so summary text begins on a common visual rhythm when directions differ in length.
- Retain the existing count-aware grid and responsive breakpoint behavior.

**Non-Goals:**

- Truncate, clamp, or otherwise hide chart-grounded content.
- Change AI response mapping, supported horizons, generation timing, or the reading-only safety boundary.
- Alter the surrounding conclusion, evidence, follow-up, or contract-rail layout.

## Decisions

- Use a card-local CSS grid with four semantic rows: metadata, direction, flexible summary, and footer. The summary row consumes remaining row space and the footer stays at the bottom of an equal-height row. This is more reliable than only applying a top margin to the footer.
- Reserve up to two natural direction lines with a minimum track height, rather than fixing a card height or line-clamping the title. It aligns the scan path for normal output and still allows an unusually long direction to expand safely.
- Keep the forecast grid's equal-height stretch behavior. It supplies the shared height needed for bottom-aligned footers while its content-driven row height prevents clipping.
- Cover the CSS contract with static regression assertions and verify the generated report in the browser at desktop and narrow widths.

## Risks / Trade-offs

- [An unusually long direction exceeds the reserved track] → The track expands instead of clipping content; alignment remains correct for the rest of the row.
- [A longer summary makes the entire row taller] → Both cards stretch together and retain their shared footer baseline; no information is hidden.
- [Layout-only changes regress narrow screens] → Preserve the existing narrow breakpoint and test both desktop and stacked states.

## Migration Plan

- Ship as a frontend-only CSS and regression-test change.
- Rollback consists of removing the card-grid track rules; data and cached reports remain compatible.

## Open Questions

- None.
