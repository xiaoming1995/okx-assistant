## 1. Resilient bulk ticker refresh

- [x] 1.1 Add structured refresh state, safe failure classification, and capped shared backoff to the ticker snapshot cache.
- [x] 1.2 Return a complete cached snapshot immediately during refresh or backoff, while preserving an explicit no-snapshot unavailable state.
- [x] 1.3 Add deterministic backend coverage for retained snapshots, retry scheduling, raw-error containment, and unavailable first load.

## 2. Readable market-workspace status

- [x] 2.1 Extend the shared frontend ticker payload type and derive a compact Chinese freshness status with compatibility fallback.
- [x] 2.2 Replace the raw ticker transport warning in chart, AI-outlook, and trading-data workspace notices with the structured status while preserving the unavailable state.
- [x] 2.3 Add frontend regression coverage for stale, backing-off, and unavailable ticker states.

## 3. Validation

- [x] 3.1 Run focused backend/frontend tests, production build, and strict OpenSpec validation.
- [x] 3.2 Rebuild local services and verify a forced bulk refresh failure retains a usable snapshot without a raw `IncompleteRead` page banner.
