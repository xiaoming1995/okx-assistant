## 1. Calculation boundaries

- [x] 1.1 Replace the ambiguous frontend ticker-change helper with explicitly named daily-display and rolling-24-hour calculation utilities.
- [x] 1.2 Implement the daily-display base precedence of valid `sodUtc8`, then `sodUtc0`, then `open24h`, including null and zero-value handling.
- [x] 1.3 Retain `open24h` as the base for Radar and AI values explicitly labelled as 24-hour changes.

## 2. Market UI consistency

- [x] 2.1 Route market contract-list badges, daily-change sorting, and market summary movement through the daily-display utility.
- [x] 2.2 Route market-related contract-selection controls through the same daily-display utility without changing selection or watchlist behavior.
- [x] 2.3 Review visible copy and accessible labels so daily values are not described as rolling 24-hour values.

## 3. Verification

- [x] 3.1 Add focused frontend tests for UTC+8 precedence, both fallback branches, invalid ticker data, and daily-sort/display consistency.
- [x] 3.2 Add or update focused regression coverage proving Radar and AI's explicitly labelled 24-hour values continue to use `open24h`.
- [x] 3.3 Run the relevant frontend tests and production build, then run the applicable backend regression tests.
- [x] 3.4 At the same observation time, compare representative BTC and ETH market-page percentages with the OKX market view and record any source-data fallback.
- [x] 3.5 Limit all market-facing percentage values to two decimal places while preserving price-difference precision.
