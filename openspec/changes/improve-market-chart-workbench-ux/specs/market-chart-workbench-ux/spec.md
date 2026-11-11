## ADDED Requirements

### Requirement: Hierarchical Market Summary
The market chart workbench SHALL present selected-contract identity, latest price, signed 24-hour change, and compact 24-hour high, low, and turnover context as the persistent market summary. Transport source, freshness, and warning metadata MUST be visually separated from those market values.

#### Scenario: User opens a selected contract
- **WHEN** the market chart receives a ticker for the selected contract
- **THEN** the persistent summary displays the contract identity, latest price, signed 24-hour change, 24-hour high, 24-hour low, and turnover
- **AND** realtime source and freshness state are displayed as operational status rather than equal-weight market metric tiles

#### Scenario: Realtime source falls back or warns
- **WHEN** price or candle transport reports a fallback, warning, or unavailable state
- **THEN** the workbench displays the state visibly without hiding the available market summary or chart data

### Requirement: Contextual Candle Inspector
The market chart workbench SHALL expose the time, open, high, low, close, candle change, amplitude, and available volume values for the candle selected by the chart crosshair without reserving a permanent multi-row detail grid for every field.

#### Scenario: User inspects a historical candle
- **WHEN** the user moves the chart crosshair onto a candle
- **THEN** the contextual inspector displays values derived from that candle and its preceding candle where needed for change calculation
- **AND** the inspector identifies that it is showing the inspected candle rather than the newest candle

#### Scenario: No candle is selected
- **WHEN** the chart crosshair is not positioned on a candle
- **THEN** the contextual inspector displays the newest available candle values

### Requirement: Price and Volume Trend View
The market chart workbench SHALL render a candlestick price pane and a synchronized volume pane using the selected contract and bar period's existing candle data. The price pane MUST remain visually larger than the volume pane.

#### Scenario: Candles include volume
- **WHEN** candle data with volume is available
- **THEN** the workbench displays a time-synchronized volume histogram beneath the candlestick price pane
- **AND** volume columns use the corresponding candle direction color convention

#### Scenario: Candle source lacks a displayable volume value
- **WHEN** the selected candle source does not provide a valid volume value
- **THEN** the price pane remains usable
- **AND** the volume view communicates unavailable data without inventing a unit or value

### Requirement: User-Controlled Realtime Navigation
The market chart workbench SHALL preserve a user's manual time-scale view during realtime candle updates. It MUST only auto-follow new candles while the visible range ends within two bars of the newest available candle.

#### Scenario: Initial or changed chart context
- **WHEN** the user first opens the chart or changes the selected contract or bar period
- **THEN** the chart fits the available candle range and positions the newest candle at the current edge

#### Scenario: User is viewing the newest chart edge
- **WHEN** a realtime candle update arrives while the visible range ends within two bars of the newest candle
- **THEN** the chart follows the newest candle while retaining the active period and selected contract

#### Scenario: User is inspecting historical movement
- **WHEN** a realtime candle update arrives after the user has panned or zoomed so the visible range ends more than two bars before the newest candle
- **THEN** the chart preserves the user's visible time range
- **AND** the update does not call a full-content fit that discards the user's navigation

### Requirement: Responsive Desktop Chart Workbench
At desktop viewports of 1280x720 and 1440x900, the market chart workbench SHALL keep its persistent summary, bar-period controls, candlestick price pane, and volume pane visible in the right workbench without required vertical scrolling. Outside that supported baseline, the layout MUST compact secondary chrome before reducing core chart readability and MUST keep any overflow reachable rather than clipped.

#### Scenario: Desktop baseline viewport
- **WHEN** the market chart is rendered at 1280x720 or 1440x900 desktop viewport dimensions
- **THEN** the right workbench shows the persistent summary, bar-period controls, price pane, and volume pane in the viewport
- **AND** the right workbench does not require vertical scrolling to access those core elements

#### Scenario: Desktop viewport below the supported height
- **WHEN** the desktop viewport height is below 720 pixels
- **THEN** the workbench compacts secondary spacing or metadata before clipping a core chart element
- **AND** any remaining overflow is vertically reachable within the right workbench

#### Scenario: Narrow viewport fallback
- **WHEN** the viewport enters the existing narrow single-column layout
- **THEN** the market chart preserves access to its summary, chart, and candle inspection details without horizontal clipping

### Requirement: External Chart Attribution Remains Available
The market chart workbench SHALL retain the external TradingView attribution link in chart chrome and SHALL not render the library attribution icon inside the chart plot.

#### Scenario: Chart workbench renders
- **WHEN** the market chart is displayed
- **THEN** the chart header contains a usable TradingView attribution link
- **AND** the chart plot does not display the `tv-attr-logo` element
