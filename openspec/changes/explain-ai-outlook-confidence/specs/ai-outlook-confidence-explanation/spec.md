## ADDED Requirements

### Requirement: Report-scoped confidence explanation
For every manually generated AI market report with a confidence value, the system SHALL return a bounded confidence-explanation payload tied to that report's chart snapshot. The payload MUST distinguish report source, base reference confidence, direction-confirmation state, and trading-data availability. It MUST state that the value is reference strength rather than a probability of price movement or guaranteed result.

#### Scenario: User reads an indicator-fallback report
- **WHEN** a manual AI report has `metric-fallback` as its source
- **THEN** the report identifies the result as a rule-based fallback and presents a user-safe fallback reason beside the confidence basis
- **AND** it MUST NOT expose provider secrets, raw exception details, or a trading instruction

#### Scenario: User reads a report with available but non-confirming structure data
- **WHEN** all supported trading-structure fields are available but the chart direction and at least two directional structure observations are not aligned
- **THEN** the explanation identifies trading data as obtained while separately identifying the direction as unconfirmed
- **AND** it explains which available observations are neutral, confirming, or conflicting

### Requirement: Readable confidence basis in the AI outlook page
The AI outlook page SHALL render a compact, visible confidence-basis region only for an already generated report. It MUST show the reference value, its non-probability meaning, source state, direction-confirmation state, and data-availability state without requiring a tooltip.

#### Scenario: User views the decision reference on a desktop or narrow layout
- **WHEN** a generated report includes the confidence explanation
- **THEN** the page displays the source and summary explanation before or alongside the evidence rows
- **AND** the layout keeps labels, values, and their interpretation readable without horizontal clipping

#### Scenario: Older cached response lacks the new payload
- **WHEN** the UI receives a generated report that has no confidence-explanation payload
- **THEN** it derives a conservative, clearly labelled fallback explanation from existing source, decision, and structure fields
- **AND** it continues to show the report without triggering another AI request

### Requirement: Non-executing explanation boundary
The confidence explanation SHALL remain a report-reading aid. It MUST NOT introduce personalized buy/sell instructions, entry or target prices, position size, leverage, automated actions, or an assertion of likely profit.

#### Scenario: User reads the new explanation
- **WHEN** the user expands or reads the confidence basis in a generated report
- **THEN** no market request, AI generation request, order, or automation mutation is initiated
