## ADDED Requirements

### Requirement: A manual AI outlook includes one priced 15m plan
The system SHALL derive a single primary long or short plan from independently fetched 15m completed candles, with 1H and 1D direction context. A plan SHALL state its direction, status, entry reference price, stop trigger price, take-profit reference price, instrument, source bar, source timestamp, validity deadline, and evidence. The report MUST remain read-only and MUST NOT place or prepare an order.

#### Scenario: Directional candidate
- **WHEN** the user manually generates an AI outlook and fresh completed 15m candles support a directional candidate
- **THEN** the report shows one long or short plan with all three prices and whether its entry condition is met
- **AND** it displays the independent 1H and 1D context without treating them as 15m candles

#### Scenario: No defensible primary side
- **WHEN** direction evidence is tied or materially conflicting
- **THEN** the report does not invent a primary trade and shows both numeric re-evaluation boundaries when available

### Requirement: Price levels are verifiable and bounded
The system SHALL use the analysis-time ask quote as the estimated long entry and the analysis-time bid quote as the estimated short entry, freezing the quote timestamp. The quote MUST be fresh and aligned with the instrument tick size. A 20-candle boundary that excludes the signal and incomplete candles MAY be displayed only as a re-evaluation level. The response SHALL describe the basis of its entry, stop and target levels and MUST NOT present them as guaranteed execution prices.

#### Scenario: Fresh quote for a directional plan
- **WHEN** fresh bid and ask quotes and a completed-candle directional signal are available
- **THEN** a long plan uses the ask and a short plan uses the bid as its estimated entry
- **AND** the plan stores the quote timestamp separately from the re-evaluation boundary

#### Scenario: Open candle crosses a boundary
- **WHEN** only an incomplete 15m candle crosses the boundary
- **THEN** that crossing does not replace the analysis-time bid or ask quote as the entry price

#### Scenario: Invalid price inputs
- **WHEN** there are fewer than 21 complete 15m candles, no valid tick size, a stale 15m snapshot, or inconsistent levels
- **THEN** no entry, stop or target prices are fabricated and the affected data requirement is explained

### Requirement: Every priced plan explains its calculations
The system SHALL freeze a plain-language calculation trail together with each new priced plan and its verification sample. It SHALL identify the directional evidence and score, the side and timestamp of the entry quote, the completed-candle extreme and tick used for the stop, the entry-to-stop risk distance and fixed two-risk-distance target, and the verification deadline. A historical sample lacking these original inputs MUST NOT be retroactively given invented calculation details.

#### Scenario: Inspect a new plan and its record
- **WHEN** a user reads a newly generated priced plan or its saved prediction record
- **THEN** the same frozen calculation trail explains the displayed entry, stop and target prices with the actual numeric inputs
- **AND** the record keeps this trail after the market changes or the plan expires

#### Scenario: Inspect a legacy record
- **WHEN** a saved record predates the calculation trail
- **THEN** the page states that the original detailed inputs were not saved and does not substitute current quotes or candles

### Requirement: Plan validity and quote context are explicit
The system SHALL bind each plan to its source snapshot and expire it at the next 15m close. It SHALL distinguish the frozen bid/ask quote from an actual fill price. Stale reports, wide spreads, or missing quotes MUST NOT be labeled immediately executable.

#### Scenario: Prior report during refresh
- **WHEN** the user refreshes an existing report
- **THEN** the previous plan remains visible with its original timestamp and deadline until the new result arrives
- **AND** an expired prior plan is visibly marked expired

#### Scenario: Quote becomes stale
- **WHEN** the frozen quote is more than 30 seconds old
- **THEN** the report marks the quote as historical and prompts a new analysis

### Requirement: The first screen presents the price plan clearly
The system SHALL show the direction, entry, stop, take-profit, condition, expiry and read-only nature in the AI outlook's primary reading area on desktop and narrow screens. Loading, error, cached and unavailable states MUST remain understandable and keyboard accessible.

#### Scenario: Narrow screen with an available plan
- **WHEN** a user views a generated plan at a narrow viewport
- **THEN** all three prices, the status, validity and refresh control remain readable without horizontal clipping

#### Scenario: Old response without pricePlan
- **WHEN** a cached response predates this capability
- **THEN** the page prompts the user to refresh for a price plan without showing invented prices
