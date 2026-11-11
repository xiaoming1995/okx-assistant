## 1. Backend Market Summary

- [x] 1.1 Define backend response models for market summary, AI analysis, watchlist items, highlights, risks, freshness, and warnings.
- [x] 1.2 Implement a summary builder that derives scan counts, market breadth, liquidity distribution, volatility distribution, risk counts, and deterministic radar leaders from current radar data.
- [x] 1.3 Cap all top lists and prompt fields so the LLM payload stays bounded regardless of total contract or candle count.
- [x] 1.4 Add unit tests for summary calculations, payload caps, missing data handling, and freshness metadata.

## 2. Backend LLM Analysis

- [x] 2.1 Add an explicit AI market analysis API action for the current Contract Radar scan context.
- [x] 2.2 Implement the LLM prompt using the compact market summary and require a strict structured JSON response.
- [x] 2.3 Parse and validate LLM output into market regime, confidence, summary, highlights, watchlist, risk warnings, suggested filters, source, generated time, and warnings.
- [x] 2.4 Ensure LLM output cannot mutate deterministic radar scores, rank order, tradability status, risk labels, or trading state.
- [x] 2.5 Implement deterministic fallback analysis when LLM configuration is missing, the request fails, or response parsing fails.
- [x] 2.6 Cache AI analysis separately from radar scan snapshots using scan context, filter settings, timestamp, and cache age metadata.
- [x] 2.7 Add backend tests for successful LLM analysis, missing config fallback, invalid response fallback, cache reuse, and force refresh.

## 3. Frontend Contract Radar UX

- [x] 3.1 Add a separate manual AI market analysis action that is available only after a radar scan context exists.
- [x] 3.2 Prevent page load, filter changes, and ordinary radar scan from automatically triggering the LLM analysis request.
- [x] 3.3 Add a compact AI market analysis panel showing regime, confidence, summary, highlights, watchlist, risks, freshness, and warnings.
- [x] 3.4 Keep deterministic candidate ranking visible and unchanged when AI analysis loads or refreshes.
- [x] 3.5 Add clear loading, empty, cached, fallback, and error states for the analysis panel.
- [x] 3.6 Update frontend static tests for manual-trigger behavior, section labels, fallback display, and ranking preservation.

## 4. Validation

- [x] 4.1 Run backend radar tests and update expected payloads where needed.
- [x] 4.2 Run frontend static tests.
- [x] 4.3 Run frontend production build.
- [x] 4.4 Manually verify the Contract Radar flow: open page, no auto AI call, scan manually, request AI analysis manually, confirm concise analysis panel and unchanged ranking.
