## ADDED Requirements

### Requirement: Market daily change uses the OKX day-open baseline
The system SHALL calculate every market-facing \"今日涨跌\" percentage as `(last - sodUtc8) / sodUtc8 * 100` when the ticker has a valid non-zero `last` and `sodUtc8` value.

#### Scenario: UTC+8 daily baseline is available
- **WHEN** a ticker provides `last` 77,263.7 and `sodUtc8` 77,682.0
- **THEN** the market-facing daily change SHALL be displayed and sorted as approximately `-0.54%`

#### Scenario: Daily baseline cannot be calculated
- **WHEN** the ticker has no valid non-zero last price or no valid non-zero day-open fallback
- **THEN** the system SHALL not invent an absolute or percentage change value

### Requirement: Daily change has deterministic fallback behavior
When `sodUtc8` is unavailable or invalid, the system SHALL calculate the market-facing daily change from the first valid non-zero value in this order: `sodUtc0`, then `open24h`.

#### Scenario: UTC+8 day-open is absent
- **WHEN** a ticker has no valid `sodUtc8` but has valid `last` and `sodUtc0` values
- **THEN** the system SHALL use `sodUtc0` as the daily-change baseline

#### Scenario: Both daily-open fields are absent
- **WHEN** a ticker has no valid `sodUtc8` or `sodUtc0` but has valid `last` and `open24h` values
- **THEN** the system SHALL use `open24h` as the final daily-change fallback

### Requirement: Daily market surfaces and sorting remain consistent
The system SHALL use the same daily-change calculation for all market-facing contract-list values, daily-change sorting, market summary movement, and contract-selection values.

#### Scenario: User sorts the contract list by change
- **WHEN** the user selects daily-change sorting
- **THEN** contracts SHALL be ordered by the same percentage shown on their market-facing rows

#### Scenario: The same contract appears in multiple market controls
- **WHEN** a contract is shown in a market list and a market-related selection control
- **THEN** both controls SHALL show the same daily percentage for the same ticker snapshot

### Requirement: Explicit 24-hour analytics retain rolling-window semantics
The system SHALL continue to calculate Radar and AI values explicitly labelled \"24h 涨跌\" from `open24h`, independently of the market-facing daily-change calculation.

#### Scenario: Daily display and 24-hour analytics have different baselines
- **WHEN** a ticker's `sodUtc8` and `open24h` values differ
- **THEN** the market-facing daily percentage SHALL use `sodUtc8` while the explicitly labelled 24-hour analytic percentage SHALL use `open24h`
