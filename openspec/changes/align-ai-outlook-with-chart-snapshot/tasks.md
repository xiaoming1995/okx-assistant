## 1. Chart Snapshot Contract

- [x] 1.1 Define the server-side `ChartSnapshot` model, lifecycle/TTL, opaque identifier, and bounded immutable candle evidence for an `instId` and `bar`.
- [x] 1.2 Build snapshots from normalized existing candle/cache/realtime batches, including source, timestamps, candle count, current-candle state, completeness warnings, and chart-aligned technical summary fields.
- [x] 1.3 Extend chart REST and realtime candle payloads with compatible snapshot metadata and add focused backend tests for fresh, cached, degraded, and mismatched snapshot states.
- [x] 1.4 Add snapshot lookup/validation that rejects expired or contract/period-mismatched identifiers without selecting unrelated candle evidence.

## 2. Shared Market Workbench Candle State

- [x] 2.1 Add a market-workbench chart-snapshot controller keyed by selected contract and bar, including initialization, realtime update, source/warning state, and cleanup behavior.
- [x] 2.2 Refactor `MarketPage` to consume the shared controller for K-line drawing, detail data, moving averages, update status, and existing chart interactions without changing chart routes.
- [x] 2.3 Make AI outlook consume the same active snapshot state and initialize the matching snapshot for a direct AI deep link without starting an AI analysis.
- [x] 2.4 Add frontend tests for chart-to-AI handoff, period/contract changes, direct-link snapshot initialization, and preserving one workbench snapshot across market-tab navigation.

## 3. Snapshot-Driven AI Evidence and Response

- [x] 3.1 Extend the AI outlook request and cache key to reference a validated `snapshotId`, while retaining recoverable handling when the snapshot is absent or expired.
- [x] 3.2 Replace independently fetched multi-period K lines as the primary AI technical basis with the matching snapshot's current-period candles and derived evidence.
- [x] 3.3 Update the LLM prompt, strict response normalization, and deterministic fallback to produce current-chart structure, evidence, data status, and observation conditions without future-price prediction language.
- [x] 3.4 Retain macro events and any multi-period comparison only as attributed supplementary content that cannot alter the primary chart conclusion.
- [x] 3.5 Add backend tests proving the report, fallback, source metadata, and stale-report handling all reference the same snapshot shown to the chart.

## 4. Evidence-First AI Reading Experience

- [x] 4.1 Redesign the AI report first screen around current-chart conclusion, snapshot data status, at most three traceable evidence items, and non-executing observation/reassessment conditions.
- [x] 4.2 Remove the old primary “未来15分钟 / 未来1小时 / 今天走势” prediction-card hierarchy and render macro/multi-period information as clearly labelled secondary content.
- [x] 4.3 Display report-versus-chart freshness: identify when a newer chart snapshot exists and offer a manual refresh that does not run automatically.
- [x] 4.4 Preserve idle, loading, error, cached, degraded-source, and read-only safety states with understandable Chinese labels and no trading/automation actions.
- [x] 4.5 Update frontend tests for the new report contract, snapshot provenance, manual-trigger boundary, and the absence of mixed-period future-prediction copy in the primary report.

## 5. Verification and Release Readiness

- [x] 5.1 Run focused backend and frontend tests, the full relevant test suite, production build, and `openspec validate align-ai-outlook-with-chart-snapshot --strict`.
- [x] 5.2 Verify in a browser that a selected `15m` chart and its AI report show the same contract, period, candle timestamp/count, source state, and primary evidence.
- [x] 5.3 Verify direct AI deep links, snapshot expiry/recovery, cached or incomplete OKX data, realtime chart advances after report generation, desktop readability, and narrow-width access.
- [x] 5.4 Record verification separately for successful UI flow and any external OKX/macro-data degradation, so external-source warnings are not mistaken for an unverified UI result.
