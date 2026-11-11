## ADDED Requirements

### Requirement: Present report-scoped conditional confirmation prices for a wait decision
For a manually generated AI market report whose decision is to wait and whose selected chart snapshot has a valid recent range, the system SHALL return an additive confirmation-level payload. It SHALL identify an upper bullish candidate and a lower bearish candidate using traceable snapshot boundaries, and SHALL state that each price is a confirmation price rather than a direct transaction price.

#### Scenario: Valid wait report presents both candidate prices
- **WHEN** a wait decision has a valid selected-snapshot recent low and high
- **THEN** the response includes distinct bullish and bearish candidate confirmation prices, each bound to the selected instrument, K-line period, and snapshot metadata

#### Scenario: Invalid range does not create a candidate price
- **WHEN** the selected chart snapshot lacks a valid recent range
- **THEN** the response marks confirmation levels unavailable and does not invent a price or candidate direction

### Requirement: State the complete confirmation and invalidation conditions
Each candidate direction SHALL expose reader-facing conditions in the fixed order of confirmation price, required completed K-line condition, volume and available trading-structure requirements, current candidate status, and invalidation rule. A touch or intraperiod move alone MUST NOT be represented as confirmation, and a return to the report range SHALL restore observation status.

#### Scenario: Price is inside the neutral range
- **WHEN** the selected-snapshot price remains inside the derived range
- **THEN** both candidates are labeled as awaiting confirmation and the report retains a current observation state

#### Scenario: Data is partial
- **WHEN** a required trading-structure metric is unavailable or partial
- **THEN** the relevant candidate states that complete confirmation is unavailable and does not claim the candidate is confirmed

#### Scenario: Price returns to the range after a boundary move
- **WHEN** the report evidence identifies a breakout followed by return to the derived range
- **THEN** the affected candidate exposes an invalidated status and directs the reader back to observation

### Requirement: Render confirmation prices as read-only next-step guidance
The AI outlook page SHALL render a compact current observation state followed by bullish and bearish candidate cards when confirmation levels are available. It SHALL visibly label each price as not a direct transaction price and SHALL surface chart-freshness warnings before any candidate conditions. The page MUST NOT add trading controls, position size, leverage, target price, stop-loss price, automatic alert, or automatic execution from these levels.

#### Scenario: Reader opens a current wait report
- **WHEN** a current wait report contains confirmation levels
- **THEN** the decision reference shows current observation status and both candidate cards without clipping, including confirmation, requirements, status, and invalidation details

#### Scenario: Chart data is newer than the report
- **WHEN** the selected chart has advanced beyond the report snapshot
- **THEN** the confirmation section identifies that the levels are older and asks the reader to refresh manually before relying on them
