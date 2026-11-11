## ADDED Requirements

### Requirement: Shared chart snapshot has an identifiable and inspectable market state
The system SHALL create a server-issued chart snapshot for every active contract and supported K-line period used by the market workbench. A snapshot SHALL identify its contract, period, normalized K-line sequence, candle count, last-candle timestamp, snapshot timestamp, source, cache/degradation state, and data-completeness warning when applicable. The snapshot SHALL expose a stable identifier that the client can use only for the corresponding contract and period during its validity window.

#### Scenario: Realtime chart data produces a snapshot
- **WHEN** the market workbench receives an initial or updated candle batch for `BTC-USDT-SWAP` at `15m`
- **THEN** the chart consumer receives normalized candles and metadata with one matching, identifiable `BTC-USDT-SWAP` `15m` snapshot

#### Scenario: Degraded source remains visible in snapshot metadata
- **WHEN** an OKX candle refresh fails and the workbench falls back to a persisted candle batch
- **THEN** the snapshot SHALL retain the available candle data and SHALL identify the fallback source and warning rather than representing it as a fresh realtime snapshot

### Requirement: Chart and AI outlook share the same primary candle evidence
The market chart and AI outlook SHALL use the same active chart snapshot for a selected contract and period while the market workbench remains mounted. The AI outlook request SHALL reference the server-issued snapshot identifier, and the backend SHALL build its primary technical evidence only from the matching snapshot rather than independently retrieving another primary candle batch.

#### Scenario: User opens AI outlook from a chart
- **WHEN** a user viewing `BTC-USDT-SWAP` `15m` opens AI看行情 from the market chart
- **THEN** the AI page SHALL retain the matching active chart snapshot and a manually generated report SHALL identify that same contract, period, candle count, and last-candle timestamp

#### Scenario: User opens an AI deep link without a mounted chart
- **WHEN** a user opens an AI outlook deep link with a valid contract and period but no active chart snapshot
- **THEN** the workbench SHALL initialize a chart snapshot for that contract and period before enabling manual analysis, without automatically generating an AI report

#### Scenario: Snapshot identifier does not match request state
- **WHEN** an AI request supplies a missing, expired, or contract/period-mismatched snapshot identifier
- **THEN** the backend SHALL not generate a report from unrelated candles and SHALL return a recoverable snapshot-state result that lets the client initialize the matching chart snapshot

### Requirement: AI primary report explains the selected chart instead of predicting mixed periods
The AI outlook primary report SHALL describe the selected chart period's current K-line structure, evidence, data status, and non-executing observation conditions. Its technical evidence SHALL be derived from the same snapshot's K-line sequence and SHALL be traceable to displayed values such as latest candle, moving-average relationship, recent range, high/low levels, and volume context. The primary report SHALL NOT present mixed-period historical inputs as “未来15分钟”, “未来1小时”, or other future-price predictions.

#### Scenario: User reads a 15-minute chart report
- **WHEN** a user manually generates a report for a `15m` chart snapshot
- **THEN** the primary conclusion SHALL identify `15m` as its analysis period and SHALL not claim that 1m, 5m, 1H, or 4H data is the basis of that conclusion

#### Scenario: Deterministic fallback uses chart evidence
- **WHEN** the LLM is unavailable or its output cannot be accepted
- **THEN** the fallback report SHALL use the matching chart snapshot's current-period evidence and SHALL retain the same data-status disclosure and non-executing wording

### Requirement: AI outlook presents evidence and freshness before supplementary context
The AI outlook page SHALL present, before supplementary context, a current-chart conclusion, snapshot data status, no more than three primary evidence items, and observation/reassessment conditions. Data status SHALL show the analysis period, snapshot/last-candle time, candle count, source, and any completeness or degraded-source warning. Macro events and any multi-period comparison SHALL be visually secondary, attributable, and explicitly labelled as supplementary information rather than the basis of the primary chart conclusion.

#### Scenario: Report has fresh complete data
- **WHEN** a user opens a generated AI outlook with a fresh complete chart snapshot
- **THEN** the page SHALL show the snapshot's period, time, candle count, and source with the current-chart conclusion before macro or supplementary content

#### Scenario: Chart advances after report generation
- **WHEN** the active chart receives a newer snapshot after an AI report was generated
- **THEN** the page SHALL identify that the report references an older snapshot and SHALL offer a manual refresh without automatically issuing another AI request

### Requirement: The chart-driven AI flow remains manual and read-only
The chart-driven AI outlook SHALL remain a manually requested, reading-only feature. Entering the page, initializing or updating a chart snapshot, changing a contract or period, and receiving realtime data SHALL NOT automatically call the LLM, create an order, prepare a trade, change automation state, or consume private account data. The UI SHALL retain a clear statement that the report is for market reading only and does not place orders or affect automation.

#### Scenario: User changes selected period
- **WHEN** a user changes the selected period from `15m` to `1H`
- **THEN** the workbench SHALL initialize or select the matching `1H` chart snapshot, clear or mark the prior report outdated, and wait for a user action before generating a new AI report
