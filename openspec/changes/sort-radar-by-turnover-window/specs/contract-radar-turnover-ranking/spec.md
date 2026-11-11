## ADDED Requirements

### Requirement: Radar defaults to descending completed one-hour turnover
The system SHALL resolve a Contract Radar scan without an explicit sort key to `turnover_1h` and SHALL order comparable candidate results by their completed one-hour quote turnover in descending order. It SHALL return the resolved sort key, human-readable sort label, and turnover-window metadata with the scan.

#### Scenario: Default scan has comparable one-hour values
- **WHEN** a user starts a radar scan without selecting a sort mode and multiple screened candidates have valid completed one-hour quote turnover
- **THEN** the returned list SHALL order those candidates from the highest one-hour turnover to the lowest
- **AND** the response and candidate-list UI SHALL identify the order as `1小时成交额`

#### Scenario: Equal one-hour turnover is deterministic
- **WHEN** two candidates have equal valid one-hour turnover in the same scan
- **THEN** the system SHALL apply deterministic documented tie breaking without using LLM output

### Requirement: Radar provides an explicit twenty-four-hour turnover alternative
The system SHALL accept `turnover_24h` as a radar sort key and SHALL order comparable candidate results by the existing normalized twenty-four-hour turnover in descending order. The frontend SHALL expose `24小时成交额` as an explicit alternative to the default one-hour control.

#### Scenario: User selects twenty-four-hour turnover
- **WHEN** a user selects `24小时成交额` and starts or refreshes a scan
- **THEN** the request SHALL use the twenty-four-hour turnover sort key
- **AND** the returned candidate rows SHALL be ordered by comparable twenty-four-hour turnover from high to low
- **AND** the list header and active control SHALL identify the twenty-four-hour basis

#### Scenario: User switches turnover window after a completed scan
- **WHEN** a user selects a different turnover window while a complete dual-ranking radar snapshot is visible
- **THEN** the frontend SHALL immediately render that window's ranking from the same scan snapshot without requesting Radar or K-line data
- **AND** the selected control, status, candidate header, row amounts, and selected-contract metric SHALL all use the selected window
- **AND** it SHALL not show a scanning state or start AI analysis

### Requirement: One-hour turnover uses only completed comparable candles
The system SHALL derive a candidate's one-hour turnover by summing the quote turnover of its four latest confirmed 15-minute candles. It MUST exclude an in-progress candle and MUST NOT estimate a one-hour amount from daily turnover, contract count, or base-coin quantity.

#### Scenario: Four completed 15-minute candles are available
- **WHEN** a screened candidate has four latest confirmed 15-minute candles with valid comparable quote turnover
- **THEN** the radar result SHALL expose their sum as one-hour turnover
- **AND** the result SHALL identify that the window contains four completed 15-minute candles

#### Scenario: One-hour candle data is incomplete or incomparable
- **WHEN** a screened candidate lacks four confirmed usable 15-minute quote-volume candles or its quote-volume unit cannot be compared
- **THEN** the result SHALL mark its one-hour turnover unavailable with a Chinese limitation message
- **AND** the default one-hour list SHALL place it after candidates with comparable one-hour turnover

### Requirement: Turnover rank is transparent and remains decision support
The system SHALL preserve existing minimum twenty-four-hour-turnover, live-instrument, risk, tradability, opportunity-score, and entry-assessment behavior while making the selected turnover window authoritative for the visible order of comparable rows. It SHALL continue to communicate that activity ranking and entry assessment are market observations rather than trade instructions.

#### Scenario: A high-turnover candidate has a risk or tradability warning
- **WHEN** a candidate ranks highly by the selected turnover window but has a non-playable tradability status, risk warning, or conservative entry assessment
- **THEN** the list and detail view SHALL retain the corresponding readable status and warning
- **AND** the system SHALL NOT replace it with a buy, sell, or execution instruction

#### Scenario: Manual AI analysis is requested after a turnover scan
- **WHEN** a user manually requests AI market analysis for a scan using either turnover sort mode
- **THEN** the analysis SHALL use that scan context
- **AND** AI output SHALL NOT change the deterministic turnover order, turnover values, scores, risk labels, or trading state

### Requirement: Bounded candidate-pool scope and cache state are explicit
The system SHALL continue to calculate one-hour turnover only for the filtered, bounded candidate pool chosen by comparable twenty-four-hour turnover. It SHALL expose the candidate-pool count and cache freshness, and each complete scan snapshot SHALL contain accurate bounded Top rankings for both supported turnover windows.

#### Scenario: Candidate population exceeds the configured limit
- **WHEN** filtered live instruments exceed the configured radar candidate limit
- **THEN** the response and UI SHALL identify the displayed one-hour ranking as being within the screened candidate pool
- **AND** the system SHALL NOT describe it as a full-market one-hour leaderboard

#### Scenario: User switches a complete dual-ranking snapshot
- **WHEN** a user has completed one scan and changes between `1小时成交额` and `24小时成交额`
- **THEN** each selected list SHALL come from the same scan timestamp and screened candidate pool
- **AND** the frontend SHALL NOT issue a second Radar request merely for the display switch

#### Scenario: Legacy cached scan lacks turnover-window fields
- **WHEN** a cached radar payload predates turnover-window metadata
- **THEN** the frontend SHALL preserve usable legacy data where possible
- **AND** it SHALL clearly request a rescan before presenting it as a one-hour turnover ranking

### Requirement: K-line refresh is bounded and respects the selected turnover need
The system SHALL collect the K-line evidence needed to derive the one-hour turnover during each manual radar scan, so both turnover rankings can be switched locally from a complete snapshot. It SHALL use bounded K-line refresh concurrency and one lower-concurrency recovery pass for requests that exhaust the client's retry policy. Only contracts that still cannot refresh SHALL use cached/degraded data and contribute to the compact aggregate warning; raw transport errors MUST remain server-side.

#### Scenario: Dual-ranking scan has incomplete one-hour evidence
- **WHEN** a manual scan includes a candidate with sufficient persisted 15-minute K-line history but without four comparable quote-turnover candles
- **THEN** the system SHALL keep that candidate's one-hour amount unavailable rather than estimate it
- **AND** the twenty-four-hour ranking SHALL remain based on current ticker turnover
- **AND** the result SHALL surface a concise data-limitation state without blocking the complete snapshot

#### Scenario: Transient candle refresh succeeds during recovery
- **WHEN** a bounded primary K-line refresh exhausts its client retry policy and the lower-concurrency recovery pass succeeds
- **THEN** the system SHALL use the recovered rows
- **AND** that contract SHALL NOT contribute to the user-facing cache/degraded warning

#### Scenario: Candle refresh remains unavailable after recovery
- **WHEN** a candidate still cannot refresh after the bounded recovery pass
- **THEN** the system SHALL retain any safely available local K-line data and show only the compact Chinese aggregate availability warning
- **AND** diagnostic logs MAY contain limited contract and transport context without returning raw upstream exception text to the user

### Requirement: Structure risk and market condition are independently legible
The system SHALL present the existing low/medium/high risk classification as `结构风险`, limited to its deterministic data, liquidity, contract-state, and extreme-range checks. It SHALL expose a separate market-condition descriptor from recent completed candles, including a `横盘震荡` state when recent directional displacement is small relative to its observed range. A `横盘震荡` result SHALL explain that direction remains unconfirmed and that a user should not treat low structural risk as a direct-entry signal.

#### Scenario: Liquid contract is moving sideways without structural warnings
- **WHEN** a live candidate has comparable sufficient liquidity and K-line data, no extreme range or structural warning, and recent completed candles show small net displacement within a meaningful range
- **THEN** its structure-risk label SHALL remain `结构风险低`
- **AND** its market-condition label SHALL be `横盘震荡`
- **AND** the detailed risk context SHALL state that the direction is unconfirmed and that breakout chasing should wait for volume and candle-close confirmation

#### Scenario: User filters by structural risk
- **WHEN** a user opens the radar risk filter
- **THEN** its label and options SHALL identify the filter as `结构风险`
- **AND** the filter SHALL keep its existing deterministic behavior without treating a standalone sideways condition as a hidden structural-risk penalty

### Requirement: Radar scan loading is concise, accessible, and preserves complete results
The frontend SHALL render a visible, Chinese, accessible loading state while the first radar scan is in progress. It SHALL use compact skeletons for both the candidate list and selected-detail workspace rather than leaving the workbench blank. When a complete radar payload already exists, a subsequent scan SHALL retain that content and show only compact updating feedback; it MUST NOT replace retained results with skeletons.

#### Scenario: User starts the first radar scan
- **WHEN** the user starts a radar scan before any complete payload exists
- **THEN** the candidate-list and detail workspaces SHALL show a visible loading state with low-motion skeleton placeholders
- **AND** assistive technology SHALL receive a concise Chinese scanning status
- **AND** the scan action SHALL remain disabled until the request resolves

#### Scenario: User refreshes a completed radar scan
- **WHEN** the user starts another scan while a complete candidate list is visible
- **THEN** the existing candidate list and selected detail SHALL remain visible
- **AND** the status SHALL state that the requested ranking is updating
- **AND** no initial-load skeleton SHALL replace the retained content

### Requirement: Turnover controls remain accessible across responsive layouts
The frontend SHALL provide a keyboard-operable compact turnover-sort control with an explicit selected state, visible focus feedback, and a disabled scanning state. The active sort, ranking status, and core scan action SHALL remain visible and usable at desktop and narrow breakpoints.

#### Scenario: Keyboard user changes the sort selection
- **WHEN** a keyboard user focuses the turnover control and selects a different supported window with a complete dual-ranking snapshot available
- **THEN** the selected state, accessible label, and rendered ranking SHALL update without a network request
- **AND** the next manual scan SHALL refresh both supported windows

#### Scenario: Scan is in progress on a narrow viewport
- **WHEN** a radar scan is in progress at a narrow breakpoint
- **THEN** the active turnover label and scanning-disabled control SHALL remain visible
- **AND** existing rows or a clear loading state SHALL communicate the refresh state without hiding the core action

### Requirement: Completed radar snapshots support local volatility and turnover filtering
After a complete radar scan, the frontend SHALL provide a compact, explicitly scoped `结果筛选` control for volatility level and minimum comparable 24-hour turnover. It SHALL start as a compact candidate-panel-header disclosure, so it does not duplicate the next-scan controls in the initial viewport. These filters SHALL operate only on the active turnover ranking in the current scan snapshot; they MUST NOT issue a Radar or K-line request, alter the saved scan criteria, or imply a market-wide search.

#### Scenario: User filters a completed ranking by volatility or turnover
- **WHEN** a user changes the local volatility selection or enters a minimum 24-hour turnover after a complete scan
- **THEN** the visible candidate rows and selected detail SHALL update immediately from the existing snapshot
- **AND** the selected turnover ordering SHALL remain authoritative within the visible rows
- **AND** the UI SHALL identify the filter as applying to the current scan result and show the visible-row count relative to that snapshot
- **AND** no scanning or AI-analysis state SHALL start

#### Scenario: Completed snapshot has no local result filter
- **WHEN** a completed radar snapshot has no local result filter active
- **THEN** its candidate-panel header SHALL show the visible/total count and a compact keyboard-operable `结果筛选` disclosure
- **AND** the volatility and turnover inputs SHALL remain collapsed until the user opens that disclosure
- **AND** the next-scan toolbar controls SHALL remain visually distinct from the local result filter

#### Scenario: Local result filters exclude every current row
- **WHEN** the active snapshot has candidates but none match the local result filters
- **THEN** the list and detail workspace SHALL show a concise Chinese empty state that identifies the local filters as the cause
- **AND** the user SHALL have a keyboard-operable `清除结果筛选` action
- **AND** the original scan snapshot SHALL remain retained for immediate restoration

#### Scenario: User changes turnover window with local result filters active
- **WHEN** a user changes between `1小时成交额` and `24小时成交额` while local result filters are active
- **THEN** the frontend SHALL first select the matching locally held ranking and then apply the existing local result filters
- **AND** it SHALL not issue a Radar or K-line request

### Requirement: Radar scanned workspace is compact and progressively disclosed
The frontend SHALL keep the two turnover choices, scan control, selected-contract headline metrics, entry assessment, and contract handoffs readable without unnecessary vertical expansion at desktop widths. It SHALL retain warnings and AI waiting state as concise readable feedback, and SHALL provide secondary reason/risk prose in a keyboard-operable disclosure rather than removing it.

#### Scenario: Desktop user has a completed scan
- **WHEN** a completed radar scan is rendered at a desktop width
- **THEN** the `1小时成交额` and `24小时成交额` choices SHALL remain in one readable sort-control row
- **AND** the candidate list and selected-contract key metrics and entry assessment SHALL be visible together without the secondary prose consuming the initial detail view

#### Scenario: User needs supporting reasons and risks
- **WHEN** a user focuses or activates the supporting-reasons disclosure
- **THEN** the detailed attention reasons and risk prompts SHALL be revealed
- **AND** activating it again SHALL restore the compact overview without changing selection, ranking, or scan data
