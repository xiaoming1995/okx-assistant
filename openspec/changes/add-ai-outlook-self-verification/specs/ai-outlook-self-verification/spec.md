## ADDED Requirements

### Requirement: Every new AI outlook has durable, deduplicated samples
The system SHALL persist structured samples for the main-chart stance and the 15m price-plan direction when a new manual AI outlook is generated. It SHALL retain non-directional and unavailable judgments as unscored records and SHALL NOT count cached reuse or an identical prediction from the same snapshot twice.

#### Scenario: New directional report
- **WHEN** a user generates a new report with a bullish or bearish stance and a long or short price plan
- **THEN** the system stores both predictions with their original direction, baseline complete candle, snapshot, rule and prompt versions, source, and due time; the price plan also freezes its entry condition, entry price, exit target and stop prices, and validity deadline

#### Scenario: Cached report or neutral stance
- **WHEN** an existing report is served from cache or a new report has no defensible direction
- **THEN** cache reuse does not create a duplicate sample, while a new neutral judgment remains visible as not scored
- **AND** a new quote timestamp or changed quote-based entry and target price produces a distinct versioned price-plan sample

### Requirement: Verification uses a matching future complete candle
The system SHALL check due samples without a user action. It SHALL settle a directional sample only from the next candle for the same instrument and period whose timestamp matches the recorded target and whose confirmation flag is complete. It MUST distinguish hit, miss, flat and insufficient-data outcomes and preserve the observed price, timestamp, source and evaluation time.

#### Scenario: Significant directional move
- **WHEN** the target complete candle closes beyond the frozen significance threshold in the predicted direction or the opposite direction
- **THEN** the sample is settled respectively as hit or miss

#### Scenario: Small move or missing complete candle
- **WHEN** the target close does not pass the significance threshold
- **THEN** the result is flat and excluded from the hit-rate denominator
- **WHEN** the matching complete candle is unavailable after the bounded retry window
- **THEN** the result is insufficient data and excluded from the denominator

### Requirement: History is usable by users and later analyses
The system SHALL expose read-only sample history and scoped statistics for the selected contract. A subsequent AI outlook SHALL receive only bounded, verified, same-contract and same-version sample evidence, and MUST NOT treat this history as model training, a guarantee, or permission to change server-computed prices.

#### Scenario: Valid history exists
- **WHEN** at least five scored samples exist for the current contract and prompt version
- **THEN** the page shows the hit count, scored denominator, and direction hit rate with recent sample statuses, and the next analysis can read a bounded summary

#### Scenario: History is too small
- **WHEN** fewer than five scored samples exist
- **THEN** the page explains that the sample is insufficient without displaying a misleading percentage

### Requirement: Verification remains read-only and explainable
The system SHALL keep prediction verification separate from trading execution and SHALL identify the frozen criterion used for each result. It MUST NOT describe a direction hit or plan entry observation as a filled or profitable trade.

#### Scenario: Plan boundary observed
- **WHEN** the target complete candle's high-low range contains a plan entry, stop or target reference price
- **THEN** the record states which reference prices were touched, while explicitly not claiming their order, an order fill, take-profit or net return

#### Scenario: Verify predicted take-profit after the report
- **WHEN** a new quote-based priced plan reaches its deadline and complete 1m candles are available after the report time
- **THEN** the record shows the frozen analysis-time ask or bid quote and states whether the predicted take-profit level was reached in the observable interval
- **AND** it does not require a later re-touch of that quote to check the target
- **AND** it marks a valid quote-then-target price path only when no stop was observed earlier; a stop and target in the same minute leave their order unknown
- **AND** a report-minute touch or missing minute data remains explicitly uncertain rather than being counted as a completed trade
- **AND** legacy breakout plans still require an observed entry touch before a later target touch
- **AND** older settled records retain their original whole-candle touch result and do not claim post-report ordering

#### Scenario: Show a price-plan percentage after verification
- **WHEN** a directional 15m price-plan sample has a valid frozen entry reference price and verified target close
- **THEN** the report and history show the signed, two-decimal hypothetical percentage from entry reference to target close, reversing the price move for a short plan
- **AND** the percentage is labeled as a no-cost price comparison, with entry-touch and unconfirmed-condition limitations visible beside it
- **AND** for legacy plans when entry was not touched, the primary result says there was no verified entry; for quote-based plans it says the quote was recorded but fill was not verified
- **AND** the theoretical percentage remains a secondary comparison rather than a trading loss or gain
- **AND** a new watch plan identifies a wide quote spread; legacy watch plans retain their frozen completed-candle explanation without inventing unknown causes
- **WHEN** the sample is pending, unscored, missing a complete close, or missing a valid entry price
- **THEN** no percentage is invented

### Requirement: Users can manage prediction history from a dedicated page
The market navigation SHALL provide a dedicated read-only prediction-record page. It SHALL list samples across instruments, allow filtering by contract, prediction type and verification result, paginate the history, and expose each sample's original prediction and subsequent observation without requiring an AI report to be open.

#### Scenario: Review a past prediction
- **WHEN** a user opens the prediction-record page and expands a sample
- **THEN** the page shows the report and sample identifiers, generation and evaluation times, frozen price references, observed close and direction result, with a clear distinction between reference-price touch and an actual trade

#### Scenario: Read the planned buy and exit path
- **WHEN** a user views a saved 15m price-plan sample
- **THEN** the list directly states the quote time for a new plan or the entry observation window for a legacy plan, long-buy or short-sell reference price, conditional take-profit and stop exit prices with the deadline, and the later target observation
- **AND** it does not invent an exact future exit timestamp or imply that candle-range touches prove entry happened before exit

#### Scenario: Scan the current report and history
- **WHEN** a report has a directional price plan and a saved verification sample
- **THEN** the report and record page place generation time, entry window, primary buy or sell price, conditional exit prices, and verification result in that reading order, with the current report's matching verification summary visible without expansion
- **WHEN** no directional price plan is available
- **THEN** the report states that no buy or sell price was generated, and the record page allows the user to include or exclude these unscored samples

#### Scenario: Filtered history is empty or unavailable
- **WHEN** a filter has no matching records or the list request fails
- **THEN** the page shows a scoped Chinese empty or retry state, without inventing results or erasing an already loaded page during a retry
