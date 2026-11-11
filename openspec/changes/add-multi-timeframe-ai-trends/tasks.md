## 1. Multi-timeframe market evidence

- [x] 1.1 Build independent 15m, 1H, and 1D K-line snapshots with per-period source, freshness, and unavailable-state metadata.
- [x] 1.2 Derive bounded deterministic trend readings, evidence, and complete-candle confirmation/re-read conditions from each period.
- [x] 1.3 Include multi-period snapshot identity in the manual AI report cache key and response while retaining compatibility with existing reports.

## 2. Direction-first presentation

- [x] 2.1 Render a compact, aligned 15-minute, 1-hour, and daily trend section immediately after the primary direction card.
- [x] 2.2 Show a concise alignment sentence and clear per-period unavailable state without duplicating confidence or detailed evidence cards.
- [x] 2.3 Preserve the read-only market-reading boundary and keep detailed report sections expandable/compatible.

## 3. Verification

- [x] 3.1 Add backend coverage for independent-period evidence, missing-period degradation, and cache identity.
- [x] 3.2 Add frontend static coverage for the compact three-period reading and read-only wording.
- [x] 3.3 Run focused tests, frontend production build, strict OpenSpec validation, and a live manual report/API verification.
