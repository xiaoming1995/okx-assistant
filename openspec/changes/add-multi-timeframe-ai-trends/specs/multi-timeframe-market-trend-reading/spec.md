## ADDED Requirements

### Requirement: AI outlook SHALL return independent fixed-period trend readings
For every successful manual AI outlook built from a valid chart snapshot, the system SHALL return trend readings for `15m`, `1H`, and `1D`. Each reading MUST be calculated from a K-line snapshot for its own period and MUST identify its period, source freshness, trend state, and data availability.

#### Scenario: All three K-line snapshots are available
- **WHEN** a user manually generates an outlook and 15m, 1H, and 1D K-line snapshots are available
- **THEN** the response SHALL include one independently calculated reading for each period
- **AND** no 1H or 1D reading SHALL be inferred by aggregating the selected chart period

#### Scenario: One period is unavailable
- **WHEN** one fixed-period K-line snapshot cannot be obtained and no valid cache exists
- **THEN** only that period's reading SHALL be marked as unavailable with a user-readable reason
- **AND** the system MUST NOT substitute another period's trend for it

### Requirement: Each trend reading SHALL provide concise, verifiable evidence
Each available period reading SHALL include a bounded trend label, at most two evidence summaries drawn from that period's K-line data, and a confirmation condition that requires a complete K-line close when a directional boundary is used. It SHALL include an invalidation or re-read condition.

#### Scenario: Period is still within its recent range
- **WHEN** the selected period has not completed a directional move beyond its recent range
- **THEN** its reading SHALL identify the state as range or wait
- **AND** its confirmation condition SHALL name the period and the price boundary to observe

#### Scenario: Period establishes an upward or downward reading
- **WHEN** its moving-average and recent-price conditions establish a directional reading
- **THEN** the evidence SHALL cite only values or states calculated from that same period
- **AND** the UI contract SHALL describe it as an observational trend, not a buy or sell instruction

### Requirement: AI outlook SHALL summarize multi-period alignment without noise
The primary AI outlook UI SHALL place a compact multi-timeframe section after the primary direction summary. It SHALL show 15-minute, 1-hour, and daily items with a common visual structure and one alignment sentence. Detailed evidence, confidence explanation, and trading-structure cards SHALL remain outside this compact section.

#### Scenario: Short and larger periods agree
- **WHEN** the available 15m, 1H, and 1D readings have the same directional trend
- **THEN** the section SHALL state that the available periods are aligned

#### Scenario: Periods conflict or are incomplete
- **WHEN** available period readings conflict or one or more periods are unavailable
- **THEN** the section SHALL state that the readings are split or incomplete
- **AND** it MUST NOT convert the conflict into a definitive trading action

### Requirement: Multi-timeframe trend reading SHALL remain read-only
The multi-timeframe section SHALL describe market snapshots and conditional confirmation only. It MUST NOT show order controls, leverage, position sizing, target prices, stop-loss instructions, or personalized investment language.

#### Scenario: A user reads a confirmation price
- **WHEN** a trend item shows a confirmation condition containing a price
- **THEN** it SHALL label the price as a condition for re-reading the market snapshot rather than an instruction to transact
