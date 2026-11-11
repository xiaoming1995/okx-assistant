## ADDED Requirements

### Requirement: AI outlook SHALL present a direction-first market observation
The AI outlook SHALL expose one deterministic direction-first summary derived from the existing rule-based decision and report snapshot. Its headline MUST be exactly one of `偏多观察`, `偏空观察`, or `暂不追向`. The summary MUST use a confirmed-direction presentation only when the existing chart and trading-structure confirmation criteria are already satisfied.

#### Scenario: Upward direction has complete confirmation
- **WHEN** the chart direction and the required complete trading-structure evidence meet the existing upward confirmation criteria
- **THEN** the summary SHALL present `偏多观察` as confirmed and identify the supporting rule-based evidence

#### Scenario: Direction is not fully confirmed
- **WHEN** price or trading-structure evidence does not meet the existing confirmation criteria
- **THEN** the summary SHALL present `暂不追向` and SHALL NOT present a confirmed directional outcome

### Requirement: Direction-first summary SHALL state one reason and one next condition
The direction-first summary SHALL include a readable primary reason and one next condition from the same chart snapshot. For an unconfirmed range or split state, the next condition MUST name a complete-candle close price condition. When missing data blocks confirmation, the next condition MUST identify that limitation.

#### Scenario: Price remains within the observation range
- **WHEN** the last close remains between the upper and lower confirmation levels
- **THEN** the summary SHALL name the observed range state and provide the nearest relevant upper or lower complete-candle close condition

#### Scenario: Required trading data is unavailable
- **WHEN** a required directional trading-structure input is unavailable
- **THEN** the summary SHALL state that the input limits direction confirmation even if a price condition is reached

### Requirement: Direction-first result SHALL preserve read-only market-analysis boundaries
The direction-first headline, reason, and price condition SHALL be presented as market-observation information from a timestamped snapshot. The UI MUST NOT use order-execution language or collect user risk, account, position, leverage, stop-loss, or profit-target information.

#### Scenario: User reads the compact outcome
- **WHEN** the AI outlook renders a direction-first summary
- **THEN** it SHALL visibly identify its chart period and include a concise non-execution boundary while retaining access to detailed scenarios and evidence
