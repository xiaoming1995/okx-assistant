## 1. Backend Liquidity Model

- [x] 1.1 Add radar liquidity metadata fields for value, basis, unit, confidence, and display label.
- [x] 1.2 Normalize OKX ticker volume fields so quote turnover is preferred for comparable scoring.
- [x] 1.3 Keep fallback volume fields visible but mark them as lower-confidence liquidity sources.
- [x] 1.4 Add response compatibility handling for cached radar snapshots that do not include new liquidity fields.

## 2. Backend Tradability and Ranking

- [x] 2.1 Add tradability classification such as playable, watch-only, and low-liquidity.
- [x] 2.2 Apply live state, liquidity, and candle-data gates before default opportunity ranking.
- [x] 2.3 Update opportunity sorting so playable contracts rank before non-playable contracts.
- [x] 2.4 Ensure high volatility cannot move a low-liquidity contract above playable contracts in the default ranking.
- [x] 2.5 Keep LLM explanations unable to modify liquidity fields, tradability classification, scores, or rank.

## 3. Frontend Radar Experience

- [x] 3.1 Update radar TypeScript types for liquidity metadata and tradability classification.
- [x] 3.2 Update radar list rows to show liquidity basis instead of an ambiguous 24h volume value.
- [x] 3.3 Add concise status labels for playable, watch-only, and low-liquidity results.
- [x] 3.4 Add ranking copy or UI affordance explaining that default rank combines tradability, liquidity, volatility, and risk.
- [x] 3.5 Keep existing actions to open selected contracts in market, trade, and automation flows.

## 4. Validation

- [x] 4.1 Add backend tests for quote-turnover normalization and fallback basis labeling.
- [x] 4.2 Add backend tests proving low-liquidity high-volatility contracts do not outrank playable contracts by default.
- [x] 4.3 Add frontend smoke tests for liquidity basis labels and tradability status labels.
- [x] 4.4 Run backend radar tests.
- [x] 4.5 Run frontend tests.
- [x] 4.6 Run frontend production build.
- [x] 4.7 Manually verify the radar page with cached and force-refresh scans.
