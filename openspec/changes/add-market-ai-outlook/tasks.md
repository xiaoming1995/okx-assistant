## 1. Backend Macro Evidence

- [x] 1.1 Add macro evidence response models for source name, title, URL, publish/schedule time, values, summary, cache age, and warnings.
- [x] 1.2 Implement CPI evidence collection from public BLS data/news-release sources with normalization and source attribution.
- [x] 1.3 Implement Federal Reserve evidence collection for FOMC schedule/policy-rate context with normalization and source attribution.
- [x] 1.4 Add an optional market-expectation provider hook for rate-hike/cut probability and clearly label it as market expectation when enabled.
- [x] 1.5 Add macro snapshot cache keys, TTL handling, stale-cache fallback, force-refresh support, and partial-provider warnings.
- [x] 1.6 Add backend tests for successful macro normalization, partial provider failure, stale cache fallback, and no-provider fallback.

## 2. Backend Market Evidence

- [x] 2.1 Add selected-contract outlook request validation for `instId`, `bar`, candle `limit`, `forceAnalysis`, and `forceMacro`.
- [x] 2.2 Build a bounded selected-contract market evidence payload from instrument metadata, ticker snapshot, and recent candles.
- [x] 2.3 Derive technical summary fields including recent trend, recent high/low, latest candle change, range/volatility, volume context, and data freshness.
- [x] 2.4 Cap recent candle details and prompt payload size so total input remains bounded regardless of loaded chart history.
- [x] 2.5 Add backend tests for technical summary calculations, candle caps, stale ticker/candle source metadata, and insufficient-data fallback.

## 3. Backend AI Outlook

- [x] 3.1 Add `POST /api/market/ai-outlook` as a read-only endpoint that assembles macro and market evidence server-side.
- [x] 3.2 Implement a structured LLM prompt that forbids invented macro facts, mandatory trading language, guaranteed-profit wording, and execution behavior.
- [x] 3.3 Parse and normalize LLM JSON into stance, confidence, summary, macro assessment, technical assessment, suggestion, sources, generated time, cache metadata, and warnings.
- [x] 3.4 Implement deterministic fallback outlook when LLM config is missing, the LLM call fails, JSON parsing fails, or evidence is incomplete.
- [x] 3.5 Cache AI outlook results separately from macro snapshots using contract, bar, latest candle timestamp, ticker timestamp, macro hash, and prompt schema version.
- [x] 3.6 Record LLM usage with request type `market_ai_outlook`, selected contract, K-line period, token counts, duration, status, provider, and model.
- [x] 3.7 Add backend tests for successful LLM outlook, invalid JSON fallback, missing config fallback, cache reuse, force refresh, usage logging, and prohibited wording filters.

## 4. Frontend Chart UX

- [x] 4.1 Add an "AI看行情" action to the market chart page without triggering it on page load, contract selection, realtime tick, or candle update.
- [x] 4.2 Add frontend API wiring for the AI outlook endpoint with loading, error, cached, fallback, and refresh states.
- [x] 4.3 Add a compact AI outlook panel showing stance, confidence, summary, macro drivers, technical drivers, observation condition, invalidation, risk notes, source freshness, and warnings.
- [x] 4.4 Keep the chart, K-line details, contract list, realtime status pills, and period controls visible and usable while analysis loads or refreshes.
- [x] 4.5 Use stable panel dimensions and non-flashing warning states so partial macro or fallback output does not cause disruptive layout shifts.
- [x] 4.6 Add frontend static tests for manual trigger, endpoint payload, no automatic LLM call, output labels, risk/source display, and fallback warnings.

## 5. Validation

- [x] 5.1 Run backend tests covering macro evidence, market evidence, AI outlook parsing/fallback, caching, and usage logging.
- [x] 5.2 Run frontend static tests.
- [x] 5.3 Run frontend production build.
- [x] 5.4 Rebuild Docker services and verify backend health plus the market chart page.
- [x] 5.5 Manually verify: open `#/market/chart`, confirm no automatic AI request, click "AI看行情", confirm structured analysis appears, refresh analysis, and confirm no order/trading state changes occur.

## 6. User Market Report Horizons

- [x] 6.1 Update backend market evidence to include bounded multi-period K-line summaries for 15-minute, 1-hour, and today views.
- [x] 6.2 Update the LLM prompt and normalized response shape to produce a user market-reading report with `overall`, `horizons`, and `report` fields.
- [x] 6.3 Keep legacy outlook fields compatible while removing automated-trading signal wording from the primary UI.
- [x] 6.4 Update the chart-page AI panel to show future 15-minute, future 1-hour, and today reference views.
- [x] 6.5 Add tests for required report horizons, fallback horizon output, read-only user-reference labels, and stable layout.
