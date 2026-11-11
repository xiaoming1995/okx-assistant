## Why

The AI outlook page renders the current conclusion and chart-evidence modules side by side, but their nested content begins at different vertical positions and creates a visibly uneven reading surface. The mismatch is especially obvious when one module contains badges or longer prose.

## What Changes

- Give the two primary AI outlook reading modules a shared outer top edge and a predictable internal content rhythm.
- Keep the conclusion summary, evidence facts, badges, and all existing text visible while aligning their module headers and reading bodies.
- Preserve the existing responsive single-column layout and read-only analysis boundary.

## Capabilities

### New Capabilities

- `ai-outlook-reading-module-alignment`: Defines consistent desktop and narrow-screen alignment behavior for the current conclusion and chart-evidence modules.

### Modified Capabilities

- None.

## Impact

- Affects the AI outlook reading-area styles and their static layout regression checks.
- Does not change market data, analysis generation, APIs, forecasts, or trading behavior.
