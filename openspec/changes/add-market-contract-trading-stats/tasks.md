## 1. Backend OKX Trading Statistics

- [x] 1.1 Add `OkxClient` methods for contract long/short account ratio, contract taker buy/sell volume, and contract open interest history.
- [x] 1.2 Normalize OKX array responses into named backend structures with numeric-safe derived values for buy share, buy/sell ratio, and open interest change.
- [x] 1.3 Add period, limit, and instrument validation that accepts SWAP contract ids and maps unsupported chart periods to an explicit supported stats period.
- [x] 1.4 Add focused backend tests for response parsing, zero/missing taker volume, period fallback, and partial metric failures.

## 2. Market Stats API

- [x] 2.1 Add `GET /api/market/stats` for selected-contract trading statistics with `instId`, `period`, `limit`, and optional `force` parameters.
- [x] 2.2 Add cache/fallback behavior keyed by `instId + period + limit` so chart interactions do not exceed OKX trading-statistics rate limits.
- [x] 2.3 Return a normalized payload with source, timestamp, cache age, effective stats period, metric data, and metric-specific warnings.
- [x] 2.4 Ensure stats API failures do not affect existing `/api/candles`, `/api/tickers`, `/api/instruments`, trading, or automation endpoints.

## 3. Market Chart UI

- [x] 3.1 Add frontend types and loader state for the normalized market stats API.
- [x] 3.2 Reload stats when the selected contract or effective statistics period changes, while clearing stale previous-contract stats.
- [x] 3.3 Add a compact trading-structure summary near the selected contract section with long/short account ratio, taker buy share, open interest, and open interest change.
- [x] 3.4 Add detail panels below the chart for long/short ratio, taker buy/sell, and open interest trends with clear loading, empty, stale, and partial-error states.
- [x] 3.5 Display the effective statistics period whenever it differs from the selected K-line period.
- [x] 3.6 Keep all statistic labels observational and avoid direct buy, sell, long, or short instructions.

## 4. Verification

- [x] 4.1 Add or update focused frontend tests for selected-contract stats loading, contract switching, period labeling, partial failure display, and observational copy.
- [x] 4.2 Run backend tests covering OKX trading-statistics parsing and API behavior.
- [x] 4.3 Run frontend tests and production build.
- [x] 4.4 Run `openspec validate add-market-contract-trading-stats --strict`.
