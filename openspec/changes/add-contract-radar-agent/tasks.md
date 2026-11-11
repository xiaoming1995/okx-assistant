## 1. Backend Radar Model and Scoring

- [x] 1.1 Define radar request/response payload shapes for filters, scores, metrics, tags, reasons, warnings, source, timestamp, and cache age.
- [x] 1.2 Implement numeric helpers for volume, price range, candle returns, volume spike, data completeness, and score clamping.
- [x] 1.3 Implement deterministic tradability, volatility, risk penalty, and opportunity score calculation.
- [x] 1.4 Add unit tests for scoring determinism, low-volume penalty, non-live filtering, missing-candle penalty, and ranking order.

## 2. Backend Scan API and Cache

- [x] 2.1 Implement staged scan flow using instruments and tickers first, then candles for a bounded candidate set.
- [x] 2.2 Add radar cache or snapshot persistence with freshness window, force refresh, stale fallback, and warning metadata.
- [x] 2.3 Add `GET /api/market/radar` with filters for settlement currency, minimum volume, volatility level, risk level, limit, and force refresh.
- [x] 2.4 Add metric-based fallback reasons so radar works when LLM configuration is missing or unavailable.
- [x] 2.5 Add optional LLM explanation generation for top candidates without allowing it to modify numeric scores or rank.
- [x] 2.6 Add API tests for successful scan, empty data, cached response, force refresh, stale fallback, filters, and LLM fallback.

## 3. Frontend Radar Experience

- [x] 3.1 Add frontend API client/types for radar results and scan filters.
- [x] 3.2 Add a contract radar page with summary status, filters, ranked rows, score values, key metrics, tags, warnings, and empty/loading/error states.
- [x] 3.3 Add focused result details showing reasons, risk warnings, and recent market metrics for the selected contract.
- [x] 3.4 Add actions from each radar result to open market, manual trade, or automation flows with the selected contract.
- [x] 3.5 Add navigation entry for the radar page without disrupting existing market, trade, automation, strategy, signal, positions, LLM, usage, or account pages.
- [x] 3.6 Add frontend tests for rendering, filters, selected details, stale warning, and workflow actions.

## 4. Validation

- [x] 4.1 Run backend tests covering radar scoring and API behavior.
- [x] 4.2 Run frontend tests covering radar UI behavior.
- [x] 4.3 Run frontend production build.
- [x] 4.4 Manually verify radar with cached and force-refresh scans using the local app.
- [x] 4.5 Confirm radar language describes suitability and volatility rather than guaranteed profit or direct trade instruction.
