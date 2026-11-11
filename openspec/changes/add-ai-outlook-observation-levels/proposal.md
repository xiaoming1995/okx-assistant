## Why

When the AI report cannot form a direction, it currently explains why the evidence conflicts but leaves the reader without concrete price boundaries to watch. The selected chart snapshot already contains recent highs, lows, volume context, and trading-structure evidence, so it can present traceable conditional observation levels without turning the report into an execution recommendation.

## What Changes

- Add a report-scoped `条件水位` section whenever the report is in an observation or no-direction state.
- Derive a neutral observation range, an upper bullish-observation line, and a lower bearish-observation line deterministically from the current chart snapshot's recent range.
- Explain the price-close, volume, and available trading-structure conditions that must accompany each boundary before the reading changes direction; show that a return to the range cancels the breakout observation.
- Bind every level to the report's selected instrument, K-line period, snapshot time, and freshness state so newer chart data asks the reader to refresh rather than treating old levels as live signals.
- Preserve manual generation, read-only behavior, and the existing boundary against orders, position sizing, leverage, target prices, stop-loss instructions, or automated actions.

## Capabilities

### New Capabilities

- `ai-outlook-observation-levels`: Report-scoped, conditional chart-boundary levels for no-direction AI market readings.

### Modified Capabilities

<!-- None. Existing base specs do not define this report-scoped level capability. -->

## Impact

- `backend/app/main.py`: Add deterministic observation-level derivation to the manual AI report response and fallback response using existing chart and trading-structure evidence.
- `frontend/src/main.tsx` and `frontend/src/styles.css`: Render compact, readable range, upper/lower level, confirmation, and refresh-state information in the decision-reference area.
- `tests/test_market_ai_outlook.py` and `frontend/src/marketAiOutlook.static.test.mjs`: Cover derivation, partial-data behavior, copy, snapshot freshness, and the no-execution boundary.
- No new external data source or trading/automation API is introduced.
