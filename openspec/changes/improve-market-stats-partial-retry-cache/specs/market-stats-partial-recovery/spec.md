## ADDED Requirements

### Requirement: Preserve and Recover Individual Trading Statistics
The system SHALL treat each contract trading-statistics metric as independently recoverable for the selected SWAP contract, effective period, and limit.

#### Scenario: One OKX statistics metric fails
- **WHEN** one statistics metric request fails but other metric requests succeed
- **THEN** the response MUST include the successful current metrics and a warning naming the failed metric

#### Scenario: Failed metric has prior matching cache
- **WHEN** a metric request fails and a previous successful value exists for the same contract, effective period, limit, and metric
- **THEN** the response MUST include that cached metric value and a warning that the metric is showing last cached data

#### Scenario: Failed metric has no prior matching cache
- **WHEN** a metric request fails and no matching cached metric value exists
- **THEN** the response MUST keep that metric in its unavailable shape and continue returning any successful sibling metrics

### Requirement: Retry Partial Trading Statistics From UI
The system SHALL provide a visible retry action when trading statistics are loading, partial, or failed.

#### Scenario: User retries trading statistics
- **WHEN** the user activates the retry action for the selected contract and statistics period
- **THEN** the frontend MUST call the market stats API with `force=true` without requiring a full page reload
