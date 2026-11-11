## 1. Backend Resilience

- [x] 1.1 Add a per-metric market stats cache keyed by contract, effective period, limit, and metric key.
- [x] 1.2 Populate metric cache only after successful metric normalization.
- [x] 1.3 On per-metric OKX failure, fill the failed metric from matching stale metric cache when available and emit explicit warning text.
- [x] 1.4 Adjust OKX incomplete/disconnect retry backoff to give transient empty responses more time to recover.

## 2. Frontend Retry UX

- [x] 2.1 Expose a `reload({ force })` function from the market stats hook.
- [x] 2.2 Add a compact retry button to the trading stats summary/status area.
- [x] 2.3 Keep warning messages concise and specific when stats are partial or cached.

## 3. Verification

- [x] 3.1 Add backend tests for per-metric stale fallback.
- [x] 3.2 Add frontend static tests for forced retry wiring.
- [x] 3.3 Run backend tests, frontend tests, frontend build, and OpenSpec strict validation.
