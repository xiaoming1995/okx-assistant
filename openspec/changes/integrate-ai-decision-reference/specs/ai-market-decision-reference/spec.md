## ADDED Requirements

### Requirement: Conditional decision reference
The system SHALL render a decision-reference module only after a user manually generates an AI market report. The module MUST present a bounded action reference, reference confidence, a readable trigger or focus condition, an invalidation or reassessment condition, and report data quality. The action reference MUST use non-execution language and MUST NOT present a personalized order, position size, leverage, or guaranteed outcome.

#### Scenario: Report provides a directional action reference
- **WHEN** a manually generated report contains a recognized action and usable evidence
- **THEN** the AI page displays the mapped directional reference with its condition, invalidation, confidence, and data-quality state
- **AND** the page continues to state that it is reading-only and does not submit an order

#### Scenario: Report is not yet manually generated
- **WHEN** a user opens the AI page before starting analysis
- **THEN** no current decision reference is displayed as if it were generated
- **AND** opening the page does not request an AI report

### Requirement: Report-scoped trading-structure evidence
The system SHALL include report-scoped, selected-contract trading-structure evidence for long/short account ratio, taker buy/sell balance, and open-interest change whenever the existing public statistics source provides it. Each displayed item MUST identify its effective statistics period, timestamp or freshness, source state, and unavailable or partial condition.

#### Scenario: All trading statistics are available
- **WHEN** the selected contract's public statistics return all three supported metrics during manual report generation
- **THEN** the report displays a compact trading-structure evidence section with all three metric interpretations
- **AND** the evidence is scoped to the selected contract and report's effective statistics period

#### Scenario: Statistics period differs from chart period
- **WHEN** the selected chart interval is not supported by the trading-statistics source
- **THEN** the report uses the supported fallback period and visibly identifies that period
- **AND** it does not imply that the statistics have the chart interval's cadence

#### Scenario: A statistics metric is unavailable
- **WHEN** one or more trading-structure metrics are unavailable or come from a stale or partial fallback
- **THEN** available metrics remain visible with their source state
- **AND** the decision reference marks the data as needing confirmation rather than inventing the missing evidence

#### Scenario: A user reads unavailable open-interest change
- **WHEN** the report cannot obtain the open-interest change metric
- **THEN** the report identifies it as market-wide open-interest change rather than a personal position
- **AND** it states that the value was not obtained, is excluded from the current decision reference, and is not a zero value

### Requirement: Conflict-aware decision explanation
The system SHALL explain whether the chart conclusion and available trading-structure observations are confirming, conflicting, or insufficient. It MUST prefer a waiting-for-confirmation reference when evidence is conflicting, incomplete, stale, or the chart conclusion is range-bound.

#### Scenario: Direction and structure confirm each other
- **WHEN** a directional chart conclusion and at least two available trading-structure observations are aligned
- **THEN** the decision reference identifies the structure as confirming and names the supporting observations

#### Scenario: Direction and structure conflict
- **WHEN** a directional chart conclusion conflicts with one or more available trading-structure observations
- **THEN** the decision reference identifies the conflict and uses waiting-for-confirmation language
- **AND** it names a condition that requires reassessment instead of treating the chart direction as an execution instruction

#### Scenario: Direction cannot be formed
- **WHEN** chart or trading-structure evidence is incomplete or non-directional
- **THEN** the action label says that no direction is currently formed
- **AND** it explains that the reader should observe confirmation rather than infer a waiting period or a buy/sell instruction

### Requirement: Manual and non-executing behavior
The decision reference and trading-structure section SHALL reuse the report generated from a manual action. Rendering, resizing, or reading the sections MUST NOT create orders, alter automation, or perform an additional AI request.

#### Scenario: User reads decision details
- **WHEN** a user reads the decision reference or trading-structure evidence
- **THEN** the report remains read-only
- **AND** no order or automation state changes
