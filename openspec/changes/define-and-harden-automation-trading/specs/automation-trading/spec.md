## ADDED Requirements

### Requirement: Automation execution modes are explicit and bounded
The system SHALL support automated strategy execution modes with clear safety boundaries and SHALL NOT provide real-money automatic order submission in this capability.

#### Scenario: Strategy runs in signal-only mode
- **WHEN** a strategy in `signal_only` mode produces a long or short signal
- **THEN** the system SHALL record the signal
- **AND** the system SHALL NOT submit any OKX order

#### Scenario: Strategy runs in simulated automatic mode
- **WHEN** a strategy in `simulated_auto` mode produces a long or short signal
- **AND** all global and strategy risk checks pass
- **THEN** the system MAY submit an OKX simulated trading order
- **AND** the system SHALL record the execution decision and result

#### Scenario: Live automatic execution is requested
- **WHEN** automation execution modes are listed or validated
- **THEN** live automatic trading SHALL NOT be available
- **AND** real-money trading SHALL remain manual-only

### Requirement: Global automation safety controls take precedence
The system SHALL provide global automation safety controls that override individual strategy enabled state.

#### Scenario: Global pause is active
- **WHEN** any strategy is enabled
- **AND** the automation loop evaluates the strategy
- **THEN** the system SHALL NOT submit orders
- **AND** the system SHALL record the signal as blocked by global pause when a signal is produced

#### Scenario: Circuit breaker is active
- **WHEN** the circuit breaker has been triggered
- **THEN** all automated execution SHALL remain blocked
- **AND** recovery SHALL require an explicit manual resume action

#### Scenario: Global safety status is displayed
- **WHEN** the user opens the automation overview
- **THEN** the system SHALL show whether automation is normal, globally paused, or circuit-breaker blocked
- **AND** active global safety reasons SHALL be visible

### Requirement: Strategy risk checks are persisted
The system SHALL persist the risk checks used to decide whether an executable signal can place an order.

#### Scenario: Executable signal is evaluated
- **WHEN** a long or short signal is produced
- **THEN** the system SHALL evaluate global pause, circuit breaker, execution mode, credentials, LLM confidence, order size, position limits, cooldown, and account state
- **AND** the system SHALL persist each check with key, label, status, message, and value
- **AND** any blocking check SHALL prevent order submission

#### Scenario: Risk checks are unavailable for a legacy signal
- **WHEN** the user opens a signal that was created before risk snapshots existed
- **THEN** the system SHALL keep the signal viewable
- **AND** the system SHALL show that structured risk snapshot data is unavailable

### Requirement: Automation alerts are durable
The system SHALL store automation alerts separately from transient status warnings.

#### Scenario: Automation failure occurs
- **WHEN** the engine, OKX request, LLM request, risk check, or order submission fails
- **THEN** the system SHALL create an alert with severity, source, message, created time, and related strategy or signal id when available

#### Scenario: User acknowledges an alert
- **WHEN** the user marks an alert as acknowledged
- **THEN** the alert SHALL remain in history
- **AND** the alert SHALL no longer count as active

#### Scenario: Automation overview has active alerts
- **WHEN** active alerts exist
- **THEN** the automation overview SHALL show the active alert count
- **AND** recent critical or warning alerts SHALL be visible from the overview

### Requirement: Signal details expose audit trail
The system SHALL let users understand why each automation signal was observed, blocked, skipped, failed, or submitted.

#### Scenario: User opens signal detail
- **WHEN** a signal has associated risk checks
- **THEN** the detail view SHALL show the risk snapshot
- **AND** the detail view SHALL show the final execution decision

#### Scenario: Signal submitted or attempted an order
- **WHEN** a signal includes execution steps
- **THEN** the detail view SHALL show each step, including close-position, reverse, open order, skip, or failure result

#### Scenario: Signal was blocked
- **WHEN** a signal was blocked by global controls or strategy risk checks
- **THEN** the detail view SHALL show the blocking reason
- **AND** the detail view SHALL show that no order was submitted

### Requirement: Strategies can be archived without losing history
The system SHALL support archiving strategies while preserving historical signals and audit records.

#### Scenario: Strategy is archived
- **WHEN** the user archives a strategy
- **THEN** the strategy SHALL be excluded from automation polling
- **AND** the strategy SHALL be hidden from active strategy lists by default
- **AND** its historical signals SHALL remain viewable

#### Scenario: Archived strategy is restored
- **WHEN** the user restores an archived strategy
- **THEN** the strategy SHALL return in paused state
- **AND** the strategy SHALL NOT automatically resume execution

### Requirement: Radar handoff remains advisory
The system SHALL treat Contract Radar as a decision-support source, not an automatic execution trigger.

#### Scenario: User opens automation from radar
- **WHEN** the user opens an automation workflow from a radar candidate
- **THEN** the strategy form MAY be prefilled with the selected contract
- **AND** the system SHALL NOT auto-start the strategy
- **AND** the strategy SHALL still require risk checks before simulated execution

#### Scenario: Radar result is high risk
- **WHEN** a radar handoff includes high-risk or stale market evidence
- **THEN** the system SHALL keep the evidence advisory
- **AND** the system SHALL NOT bypass automation risk checks

### Requirement: Backtesting boundaries are explicit
The system SHALL label automation backtesting as an estimate unless it models fees, funding, slippage, and real execution behavior.

#### Scenario: MA strategy backtest runs
- **WHEN** the user runs a moving-average strategy backtest
- **THEN** the system SHALL show that the result is estimated from recent candle data
- **AND** the system SHALL disclose when fees, funding, slippage, or real matching are not included

#### Scenario: LLM direct strategy backtest is requested
- **WHEN** the user requests historical backtesting for an LLM direct strategy
- **THEN** the system SHALL NOT replay historical model calls unless a separate implementation supports it
- **AND** the system SHALL explain that LLM historical replay is unavailable
