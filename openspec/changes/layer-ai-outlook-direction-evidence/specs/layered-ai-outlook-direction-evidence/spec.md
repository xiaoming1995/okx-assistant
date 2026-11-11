## ADDED Requirements

### Requirement: Direction conclusions SHALL use readable layers
The AI outlook report SHALL classify its conclusion as a confirmed direction, weak directional bias, conflicting signals, or neutral observation. A confirmed direction MUST continue to require an explicit chart direction and at least two complete, aligned directional trading-structure signals. Every non-confirmed layer MUST remain an observation result rather than an order or individualized investment instruction.

#### Scenario: Chart and structure evidence fully align
- **WHEN** the chart has a confirmed upward or downward direction and at least two available trading-structure signals align with it
- **THEN** the report SHALL show the corresponding confirmed direction and identify the aligned evidence

#### Scenario: Evidence shows a bias but lacks full confirmation
- **WHEN** the chart has a weak or incomplete directional bias without conflicting structure evidence, or it has a confirmed chart direction with fewer than two aligned structure signals
- **THEN** the report SHALL show a weak directional bias, state that confirmation is incomplete, and list the missing evidence

#### Scenario: Evidence conflicts or remains balanced
- **WHEN** available chart and trading-structure signals conflict
- **THEN** the report SHALL show conflicting signals and identify the conflict

#### Scenario: No directional evidence is present
- **WHEN** neither chart nor available trading-structure evidence supplies a directional bias
- **THEN** the report SHALL show neutral observation and explain that the market is currently balanced rather than implying data is absent

### Requirement: Evidence gaps SHALL be inspectable
For each chart and trading-structure input used in the direction conclusion, the report SHALL provide a user-readable current value, confirmation threshold or condition, current status, contribution to the conclusion, and the remaining gap whenever it is not confirmed.

#### Scenario: A metric is just below a directional threshold
- **WHEN** active buying is 54.93% and the upward threshold is 55%
- **THEN** the report SHALL identify the metric as unconfirmed and display that it is 0.07 percentage points below the threshold

#### Scenario: A metric is balanced
- **WHEN** a long-short account ratio is between its bearish and bullish thresholds
- **THEN** the report SHALL identify it as balanced and state that it currently contributes no directional confirmation

### Requirement: Period provenance SHALL be visible
The report SHALL display the chart snapshot period and the requested and effective trading-structure periods. If a requested period is unavailable and a fallback is used, the report SHALL explicitly mark the fallback.

#### Scenario: One-minute chart uses five-minute structure statistics
- **WHEN** the selected chart period is 1m and the effective structure period is 5m
- **THEN** the report SHALL show that the chart is 1m while trading-structure evidence is calculated on 5m statistics

### Requirement: Conditional levels SHALL explain remaining confirmation
When a report remains observational, each conditional confirmation price SHALL identify the relevant price-close requirement and the evidence gaps that still need to be resolved. The report MUST state that a confirmation price is not a direct execution or order price.

#### Scenario: Price remains within the observation range
- **WHEN** the last close remains between the derived lower and upper conditional confirmation prices
- **THEN** the report SHALL show both conditional candidates, their required full-candle close, and their remaining structure confirmation gaps

### Requirement: Confidence SHALL be explained as evidence sufficiency
The report SHALL label its confidence value as evidence sufficiency and SHALL state that it is not a price-direction probability or return expectation. The explanation SHALL identify the conclusion layer and the material missing or conflicting evidence.

#### Scenario: Neutral evidence is capped
- **WHEN** a neutral observation result has incomplete direction confirmation
- **THEN** the report SHALL explain that its lower evidence-sufficiency value results from missing directional confirmation rather than a predicted probability
