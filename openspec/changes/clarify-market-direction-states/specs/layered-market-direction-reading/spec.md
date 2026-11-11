## ADDED Requirements

### Requirement: AI outlook SHALL distinguish short-term bias from no direction
The AI outlook SHALL present a layered direction state derived from existing rule-based decision data. A weak upward or downward bias with an observed matching clue MUST be displayed as `短线偏多（未确认）` or `短线偏空（未确认）`. A conflict, missing critical evidence, or absence of a directional clue MUST NOT be displayed as a confirmed direction.

#### Scenario: Weak bearish bias has active selling evidence
- **WHEN** the chart has a weak bearish bias and active selling is observed but complete confirmation is absent
- **THEN** the summary SHALL display `短线偏空（未确认）` and identify the outstanding confirmation condition

#### Scenario: Evidence is split or absent
- **WHEN** the chart and trading structure conflict or no directional clue is available
- **THEN** the summary SHALL display `无明确方向` or `暂不追向` and explain the missing or conflicting evidence

### Requirement: Direction summary SHALL show compact completion evidence
The primary direction summary SHALL show one satisfied condition and one missing condition from the same snapshot. For unconfirmed price states, the missing condition MUST include the complete-candle close requirement and any data limitation that blocks confirmation.

#### Scenario: Price has not completed the lower-bound close
- **WHEN** bearish evidence is present but the current candle has not closed below the lower confirmation level
- **THEN** the summary SHALL show active selling as satisfied and the lower complete-candle close as missing

### Requirement: Layered direction states SHALL remain observational
The UI MUST mark non-confirmed bias as unconfirmed and preserve the non-execution market-snapshot boundary. It MUST NOT add order, leverage, position, or personalized investment language.

#### Scenario: User reads a short-term bias
- **WHEN** the summary renders a short-term directional bias
- **THEN** it SHALL visibly state that the bias is unconfirmed and not an order instruction
