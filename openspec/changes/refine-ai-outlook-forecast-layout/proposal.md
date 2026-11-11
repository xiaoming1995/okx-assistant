## Why

The conditional forecast section presents useful chart-grounded outlooks, but a fixed three-column grid leaves visible empty space when only one or two horizons are returned. Its vertically stacked metadata and long copy also make the report taller and harder to scan than the surrounding conclusion and evidence blocks.

## What Changes

- Make forecast cards fill the available row according to the number of usable horizons: one full-width card, two equal cards, or three equal cards.
- Consolidate each card's timeframe and confidence into a compact header, retain the directional observation as the primary label, and present the re-read condition as a concise footer.
- Keep two forecast cards side-by-side at ordinary desktop and laptop widths; use a single column only when the readable card width can no longer be preserved.
- Preserve all current manual-generation, chart-snapshot, conditional-prediction, and read-only behaviors.

## Capabilities

### New Capabilities

- `ai-outlook-forecast-layout`: Present the manual AI outlook's conditional forecasts in a compact, count-aware, responsive reading layout.

### Modified Capabilities

<!-- No existing base specification covers the AI outlook forecast layout. -->

## Impact

- `frontend/src/main.tsx` forecast-card structure and forecast-count layout marker.
- `frontend/src/styles.css` adaptive grid, compact card hierarchy, and responsive breakpoints.
- `frontend/src/marketAiOutlook.static.test.mjs` layout and read-only regression coverage.
- No API, market-data, LLM, trading, or automatic-request behavior changes.
