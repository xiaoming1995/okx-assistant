## ADDED Requirements

### Requirement: Quiet Routine Market Status
The market chart workbench SHALL not render a title-area subtitle whose text changes for routine ticker, candle, or successful connection events. It MUST retain visible operational source and freshness state, and it MUST present fallback or warning conditions through an actionable status or warning surface.

#### Scenario: Routine ticker update arrives
- **WHEN** the selected-contract ticker updates successfully
- **THEN** the latest market values update without a changing gray subtitle beneath the market-chart title
- **AND** the operational status controls remain available

#### Scenario: Candle source falls back
- **WHEN** the candle transport reports fallback, stale, or unavailable data
- **THEN** the workbench identifies the degraded source or warning visibly
- **AND** it does not rely on a routine title subtitle as the only indication

### Requirement: Suitable Candle Seed Presentation
The system SHALL normalize candle batches by timestamp before using them for chart presentation. A cached batch SHALL be used as a normal initial chart seed only when it is ordered, de-duplicated, valid for the selected bar interval, sufficiently recent, and does not contain an interval-sized internal discontinuity beyond the configured tolerance.

#### Scenario: Cached seed is suitable
- **WHEN** the selected contract and bar have a recent, continuous cached candle batch
- **THEN** the realtime channel may present that normalized batch as a cache seed
- **AND** a subsequent REST or WebSocket batch replaces or extends it without duplicate timestamps

#### Scenario: Cached seed is stale or discontinuous
- **WHEN** the cached candle batch is invalid, stale, or contains a gap beyond the selected bar tolerance
- **THEN** the system MUST NOT present it as a complete normal chart seed
- **AND** it MUST request or await a current REST seed before presenting normal trend data

#### Scenario: Current seed is unavailable
- **WHEN** a current REST seed cannot be obtained and persisted candles are the only available history
- **THEN** the workbench may display normalized persisted candles
- **AND** it MUST identify the data as degraded with a visible warning rather than treating it as a complete realtime trend

### Requirement: Recent Trend Focus and Return Control
The market chart workbench SHALL retain its complete loaded candle history while focusing a new contract or bar-period view on the most recent 80 normalized candles. It MUST provide an explicit control that returns the chart to that newest focused window.

#### Scenario: User opens or changes chart context
- **WHEN** normalized candles become available after the selected contract or bar period changes
- **THEN** the chart retains the loaded historical buffer
- **AND** the visible logical range is focused on the newest 80 candles with the newest edge visible

#### Scenario: User returns to the current trend
- **WHEN** the user has panned or zoomed into historical candles and activates the newest-view control
- **THEN** the chart returns to the newest 80-candle focused window
- **AND** the selected contract, bar period, and loaded candle history remain unchanged

#### Scenario: Realtime update reaches a historical view
- **WHEN** a realtime candle update arrives while the visible range is away from the newest edge
- **THEN** the chart preserves the user-controlled historical view
- **AND** it does not activate the newest focused window automatically

### Requirement: Scannable Contextual Candle Reading
The market chart workbench SHALL present the selected or newest candle's timestamp, OHLC values, signed candle change, and volume as the primary contextual reading. It MUST preserve access to amplitude and quote-turnover data without requiring every secondary value to occupy the primary reading row.

#### Scenario: User inspects a historical candle
- **WHEN** the crosshair selects a historical candle
- **THEN** the primary contextual reading identifies the inspected timestamp and its OHLC, signed change, and volume
- **AND** secondary amplitude and quote-turnover values remain reachable from the contextual reading surface

#### Scenario: No historical candle is selected
- **WHEN** the crosshair is not positioned on a historical candle
- **THEN** the contextual reading displays the newest available candle
- **AND** the primary reading remains scannable at the supported desktop viewport baseline

### Requirement: Existing Chart Trust Signals Remain Available
The market chart workbench SHALL retain the synchronized volume pane, user-controlled realtime navigation behavior, header TradingView attribution link, and absence of the library attribution logo inside the chart plot.

#### Scenario: Readability controls are used
- **WHEN** the user changes period, returns to the newest view, or inspects historical candles
- **THEN** the volume pane stays time-synchronized with the price pane
- **AND** the header TradingView link remains usable
- **AND** the chart plot does not render the `tv-attr-logo` element
