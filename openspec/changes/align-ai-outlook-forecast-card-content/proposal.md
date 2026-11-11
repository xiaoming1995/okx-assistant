## Why

The conditional forecast cards have equal outer columns, but their inner reading rhythm depends on model-generated text length. When one direction or summary wraps while another does not, the evidence and re-read cues no longer share reliable visual baselines, making the report feel uneven.

## What Changes

- Define an internal alignment contract for forecast cards: a shared metadata line, a reserved direction track, flexible summary space, and a bottom-anchored re-read cue.
- Keep all chart-grounded explanation visible without line clamping or fixed card heights.
- Preserve existing count-aware desktop columns and narrow-screen stacking; no forecast data, prompt, market-data, or trading behavior changes.
- Add regression coverage for cards with intentionally different direction and summary lengths.

## Capabilities

### New Capabilities

- `ai-outlook-forecast-content-alignment`: Keep the internal hierarchy and re-read baseline of generated forecast cards orderly across uneven text lengths.

### Modified Capabilities

- None.

## Impact

- `frontend/src/styles.css` forecast-card layout tracks and spacing.
- `frontend/src/marketAiOutlook.static.test.mjs` layout-contract regression coverage.
- No API, persisted data, LLM prompt, chart-source, or trading changes.
