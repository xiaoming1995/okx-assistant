## 1. Resilient account snapshots

- [x] 1.1 Add environment-scoped account refresh state, capped retry scheduling, and complete-snapshot fallback without retaining raw upstream messages in API responses.
- [x] 1.2 Return structured account freshness metadata and display-safe unavailable/fallback states from `GET /api/account`.
- [x] 1.3 Add deterministic backend coverage for retained memory snapshots, persisted fallback snapshots, unavailable responses, retry backoff, and refresh recovery.

## 2. Position P&L presentation

- [x] 2.1 Add a current open-position floating P&L summary with signed aggregate, sign counts, margin, notional, and snapshot state.
- [x] 2.2 Add scoped positive, negative, and neutral P&L formatting/styles that override generic table typography without affecting unrelated pages.
- [x] 2.3 Add focused frontend coverage for aggregate scope, signed P&L rendering, semantic classes, and safe freshness copy.

## 3. Verification

- [x] 3.1 Run focused backend/frontend tests, build the frontend, and check formatting/static errors.
- [x] 3.2 Rebuild the active Docker services and verify `GET /api/account`, the rendered positions route, and degraded refresh behaviour.
