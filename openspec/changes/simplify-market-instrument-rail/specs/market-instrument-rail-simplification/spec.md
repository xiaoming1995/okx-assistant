## ADDED Requirements

### Requirement: Concise primary contract range selection
The shared market instrument rail SHALL present local followed contracts and all loaded contracts as the two persistent primary range choices. It SHALL use `已关注` to describe the local watched list and SHALL display an understandable local followed/total count summary instead of an ambiguous fraction.

#### Scenario: User opens a chart with local followed contracts
- **WHEN** the market chart opens with its existing local watched filter and watched instruments are present
- **THEN** the rail SHALL show `已关注` as the active primary range and SHALL show a readable summary of local followed and total loaded contract counts

#### Scenario: User switches to all contracts
- **WHEN** the user selects `全部`
- **THEN** the rail SHALL display all loaded contracts according to the existing search and sort state without changing the current selected contract or local watchlist

### Requirement: On-demand advanced ranges and sorting
The rail SHALL place `USDT本位`、`可交易`、`币本位` ranges and `默认`、`涨跌`、`成交量` sort modes behind compact, keyboard-accessible on-demand controls. The active advanced range or sort mode SHALL remain visible in its trigger after the control closes.

#### Scenario: User selects an advanced range
- **WHEN** the user selects `USDT本位`、`可交易` or `币本位` from the filter control
- **THEN** the rail SHALL apply the existing corresponding local filter, show that range in the filter trigger, and not mark `已关注` or `全部` as active

#### Scenario: User changes sort mode
- **WHEN** the user selects `涨跌` or `成交量` from the sort control
- **THEN** the displayed rows SHALL use the existing relevance sort behavior for that mode and the sort trigger SHALL identify the selected mode

#### Scenario: User closes a compact control without a choice
- **WHEN** the user closes a filter or sort control with Escape or an outside interaction without selecting an option
- **THEN** the rail SHALL preserve the active filter, sort mode, current search text, and selected contract

### Requirement: Scannable contract rows without redundant legend
The shared rail SHALL remove the standalone list-column legend and SHALL present each contract row with contract code, readable asset name, compact perpetual/settlement context, last price, daily change, and an isolated local watch action. Secondary text SHALL truncate rather than cause horizontal clipping or uncontrolled row growth.

#### Scenario: User scans similar contracts
- **WHEN** similar contracts appear in the rail
- **THEN** each row SHALL retain enough settlement and contract context to distinguish them while keeping price and daily change visually aligned for comparison

#### Scenario: User toggles a local followed contract
- **WHEN** the user activates a row's star action
- **THEN** the rail SHALL use the existing local add/remove watch behavior and SHALL not change the current selected contract solely because the row's watch state changed

### Requirement: Local-followed empty-state recovery and selection independence
The rail SHALL retain the market-chart empty local-followed state and its `查看全部合约` recovery action. Filtering the rail SHALL remain independent from the selected contract shown in the consuming page.

#### Scenario: No local followed contracts exist
- **WHEN** the chart page's active range is `已关注`, instruments have loaded, and no local watched instruments match
- **THEN** the rail SHALL explain that there are no local followed contracts and SHALL offer `查看全部合约`

#### Scenario: User restores all contracts from empty state
- **WHEN** the user activates `查看全部合约`
- **THEN** the rail SHALL switch only its local range to all contracts and SHALL not add or remove a watched contract or replace the currently selected chart contract

#### Scenario: Directly selected contract is not locally followed
- **WHEN** a page opens a directly selected contract that is absent from the local followed range
- **THEN** the consuming page SHALL continue to show that contract while the rail remains filtered to its active range

### Requirement: Shared market-workbench continuity and responsive access
The concise rail SHALL be mounted once as the stable left side of the market chart, AI outlook, and trading-data workbench. Those views SHALL share the current selected contract, search text, range, sort mode, loaded rail ticker snapshot, refresh behavior, and local watch mutation state while the workbench remains open. At narrow widths, all rail controls and rows SHALL remain reachable without horizontal clipping.

#### Scenario: User moves between market workbench views
- **WHEN** the user changes from the chart to AI outlook or trading data after searching, filtering, or sorting the rail
- **THEN** the destination view SHALL retain the same selected contract and rail search, range, sort, ticker, and local-watch context

#### Scenario: A shared ticker snapshot updates the selected contract
- **WHEN** the workbench receives a ticker snapshot or realtime ticker update for the selected contract
- **THEN** the rail and the chart, AI outlook, and trading-data summaries SHALL read that same instrument and ticker snapshot without a page-specific ticker subscription or duplicate instrument-list request

#### Scenario: User enters a market view directly
- **WHEN** the user opens a chart, AI outlook, or trading-data deep link without an existing mounted workbench
- **THEN** the view SHALL retain its existing initial range behavior and use the deep-linked selected contract

#### Scenario: Radar opens a chosen candidate in the workbench
- **WHEN** the user chooses chart, AI outlook, or trading data for a Radar candidate
- **THEN** the application SHALL navigate to the requested workbench view with that candidate as the selected contract and SHALL initialize a newly mounted rail in the `全部` range so that candidate is visible regardless of settlement type

#### Scenario: User enters AI outlook or trading data directly after a Radar handoff
- **WHEN** a user opens AI outlook or trading data directly, without a currently mounted workbench and not through a Radar candidate action
- **THEN** the rail SHALL retain that view's existing USDT-settled initial range rather than reuse a previous Radar handoff range

#### Scenario: User views a narrow layout
- **WHEN** the viewport reaches the existing narrow-layout breakpoint
- **THEN** the rail controls and contract rows SHALL wrap or stack within the available width and remain operable without horizontal page clipping

#### Scenario: Active advanced range remains readable in the desktop rail
- **WHEN** an advanced range such as `USDT本位` is active at a desktop rail width
- **THEN** the primary range choices and advanced range/sort triggers SHALL occupy separate compact rows so the active trigger label remains readable without horizontal overlap or clipping

### Requirement: Collapsible desktop contract rail
The shared market workbench SHALL provide an accessible control to collapse or expand its left contract rail in a desktop two-column layout. Collapsing the rail SHALL increase the horizontal space available to the right-side market view without resetting the shared workbench's selected contract, search text, range, sort mode, loaded instruments, ticker snapshot, or local watch state.

#### Scenario: User collapses the rail while inspecting a contract
- **WHEN** the user activates the labelled collapse control in a desktop two-column market workbench
- **THEN** the rail SHALL become a narrow visible expand strip, the right-side view SHALL gain the released horizontal space, and the currently selected contract SHALL remain shown

#### Scenario: User reopens the rail after filtering or changing market tabs
- **WHEN** the user expands a previously collapsed rail in the same mounted workbench
- **THEN** the prior search, range, sort, contract rows, and local watch context SHALL be available without an additional instrument-list request

#### Scenario: User views the single-column layout
- **WHEN** the viewport reaches the existing single-column workbench breakpoint
- **THEN** the full rail content SHALL remain visible above the market view and the desktop collapse control SHALL not hide that content
