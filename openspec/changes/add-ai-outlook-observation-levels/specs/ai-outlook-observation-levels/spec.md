## ADDED Requirements

### Requirement: Derive report-scoped conditional observation levels
For a manually generated AI market report with valid selected-snapshot recent high and low values, the system SHALL return an additive observation-level payload tied to the report's instrument, K-line period, and chart snapshot. The payload SHALL identify the neutral range, the upper bullish-observation boundary, and the lower bearish-observation boundary using traceable snapshot prices rather than LLM-generated price prose.

#### Scenario: Valid chart range produces both boundaries
- **WHEN** a manual report's selected chart snapshot contains a valid recent 20-candle low below its recent 20-candle high
- **THEN** the response includes the neutral range and matching upper and lower observation boundaries with the selected instrument, period, and snapshot metadata

#### Scenario: Chart range is unavailable
- **WHEN** the selected chart snapshot lacks a valid recent high or low
- **THEN** the response marks observation levels unavailable and does not invent a price boundary

### Requirement: Explain confirmation and return-to-range conditions
The system SHALL describe an upper-boundary reading change as requiring a completed selected-period candle above the range plus non-conflicting available volume and trading-structure evidence. It SHALL describe a lower-boundary reading change symmetrically, SHALL treat open-interest growth as participation evidence rather than price direction, and SHALL state that a move back into the neutral range restores observation status.

#### Scenario: No-direction report exposes conditional reading rules
- **WHEN** the decision reference cannot form a direction because evidence conflicts or is insufficient
- **THEN** its observation levels show the neutral range, upper and lower observation conditions, and the return-to-range condition in reader-facing language

#### Scenario: Trading structure is partial
- **WHEN** one or more report-scoped trading-structure metrics are unavailable or partial
- **THEN** the level explanation identifies that confirmation is incomplete and does not label the affected direction fully confirmed

### Requirement: Render snapshot-fresh, read-only levels in the decision reference
The AI outlook page SHALL render a compact conditional-level panel in a fixed order of neutral range, upper observation line, lower observation line, and return-to-range condition when the response contains valid observation levels. The panel SHALL show the report's K-line period and SHALL prompt the reader to refresh when the selected chart has newer data than the report snapshot.

#### Scenario: Reader views a current no-direction report
- **WHEN** a manually generated no-direction report contains valid observation levels
- **THEN** the decision-reference area presents all four level rows without clipping, and retains the visible reading-only/no-order boundary

#### Scenario: Chart advances after the report
- **WHEN** a newer selected-chart snapshot is available than the report's level snapshot
- **THEN** the panel identifies that its levels are based on the earlier snapshot and asks the reader to manually refresh before treating them as current

### Requirement: Keep conditional levels outside execution scope
Conditional observation levels SHALL remain public-market reading information. The system MUST NOT derive or display entry prices, target prices, stop-loss prices, position sizes, leverage, order controls, automatic notifications, or automatic trading actions from the levels.

#### Scenario: Reader receives conditional level information
- **WHEN** the AI outlook page renders observation levels
- **THEN** it uses observation-oriented wording and does not add trading execution controls or personalized trade parameters
