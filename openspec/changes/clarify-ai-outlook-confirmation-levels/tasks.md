## 1. Report confirmation-level contract

- [x] 1.1 Extend the report-scoped observation-level payload with explicit bullish and bearish candidate confirmation prices, requirements, status, and invalidation details.
- [x] 1.2 Derive candidate status only from the existing report snapshot and available structure evidence, preserving unavailable and stale-report behavior.
- [x] 1.3 Add backend tests for valid candidate prices, partial confirmation, return-to-range invalidation, and no execution-oriented fields.

## 2. Next-step decision presentation

- [x] 2.1 Extend the frontend response type and compatibility fallback for the additive confirmation-level payload.
- [x] 2.2 Replace the scattered observation-level card content with a current observation state and compact bullish/bearish candidate cards containing price meaning, conditions, status, and invalidation.
- [x] 2.3 Add responsive styles and frontend regression coverage for compact candidate presentation, stale snapshots, and the no-direct-transaction boundary.

## 3. Validation

- [x] 3.1 Run focused backend and frontend tests, production build, and strict OpenSpec validation.
- [x] 3.2 Rebuild the locally served services and verify a generated wait report displays current state, both candidate confirmation prices, and non-clipped responsive layout without order controls.
