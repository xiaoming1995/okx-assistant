## 1. Report-Scoped Trading Structure

- [x] 1.1 Build a bounded trading-structure snapshot from existing contract statistics using the selected chart period or labeled 5m fallback.
- [x] 1.2 Include the structure snapshot in AI evidence, cache identity, response metadata, and deterministic fallback output without changing manual-trigger behavior.
- [x] 1.3 Derive a conflict-aware decision reference that combines chart stance, existing suggestion fields, trading-structure availability, and confirmation/conflict state.

## 2. AI Decision Reading Experience

- [x] 2.1 Add typed client mappings and reader-facing labels for decision actions, data quality, source state, and the three trading-structure metrics.
- [x] 2.2 Render a compact decision-reference module and report-scoped trading-structure evidence in the AI page while retaining the visible read-only boundary.
- [x] 2.3 Add responsive styling that keeps the new evidence readable without clipping or overcrowding the current conclusion, chart evidence, or forecast sections.

## 3. Validation

- [x] 3.1 Add backend tests for period fallback, partial statistics, cache-sensitive evidence, and conflict-aware decision output.
- [x] 3.2 Add frontend static coverage for manual-only decision rendering, read-only wording, structure labels, and narrow layout rules.
- [x] 3.3 Run focused backend/frontend tests, production build, strict OpenSpec validation, rebuilt local services, and desktop/narrow browser checks.

## 4. Reader-Facing Clarifications

- [x] 4.1 Replace ambiguous waiting and open-interest labels with plain-language decision and market-wide-position explanations.
- [x] 4.2 Add focused frontend coverage for unavailable open-interest wording and no-direction action wording.
- [x] 4.3 Verify the degraded report state in the running browser and re-run strict validation.
