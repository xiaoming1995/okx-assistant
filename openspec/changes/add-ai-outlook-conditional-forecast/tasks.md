## 1. Conditional Forecast Mapping

- [x] 1.1 Map recognized 15-minute, one-hour, and current-day response horizons into bounded reader-facing forecast entries in chronological order.
- [x] 1.2 Translate directional bias, confidence, summary, watch, and risk content into chart-oriented Chinese copy while filtering raw fields and external degradation from primary cards.

## 2. Forecast Report Experience

- [x] 2.1 Add a compact `条件推演` section after chart evidence, including timeframe, direction, confidence, and one concise condition or re-read cue per available horizon.
- [x] 2.2 Preserve absent-horizon, loading, stale-snapshot, manual-trigger, and read-only states without fabricating a forecast or triggering another analysis request.
- [x] 2.3 Add responsive styles that keep three forecast cards scannable on desktop and stack them without clipping on narrow widths.

## 3. Verification

- [x] 3.1 Update frontend tests for supported-order, conditional wording, raw/macro filtering, manual behavior, and responsive layout.
- [x] 3.2 Run the relevant frontend tests, production build, strict OpenSpec validation, and verify a manually generated browser report in the rebuilt local service.
