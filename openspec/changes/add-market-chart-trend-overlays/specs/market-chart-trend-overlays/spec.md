## ADDED Requirements

### Requirement: Default Moving-Average Trend Overlays
The market chart SHALL render MA5, MA10, and MA20 simple moving-average overlays in the price pane whenever the normalized retained candle history contains sufficient valid closes for the corresponding period. MA5, MA10, and MA20 SHALL use stable, mutually distinguishable yellow, rose, and cyan visual treatments, respectively. The overlays SHALL be derived locally from retained candle close values and SHALL NOT alter candle, volume, realtime, or API data.

#### Scenario: Sufficient candle history is displayed
- **WHEN** a selected contract and bar period have at least 20 normalized candles with valid close values
- **THEN** the price pane displays MA5, MA10, and MA20 over the candlesticks
- **AND** each line value derives from its matching simple moving-average lookback
- **AND** the volume pane remains time-synchronized with the candlestick and moving-average data

#### Scenario: Short candle history is displayed
- **WHEN** a selected contract and bar period have fewer valid closes than one or more moving-average periods
- **THEN** the chart displays its available candlesticks and any moving-average lines with sufficient lookback history
- **AND** it omits unavailable moving-average values without synthesizing data or treating the history as an error

### Requirement: Contextual Trend Legend
The market chart SHALL present a compact in-plot legend that identifies MA5, MA10, and MA20 using the same colors as their overlays. The legend SHALL show values for the crosshair-selected candle when one is selected, and otherwise SHALL show values for the newest candle. An unavailable moving-average value SHALL be represented as unavailable rather than as zero or an inferred value.

#### Scenario: User inspects a historical candle
- **WHEN** the crosshair selects a candle with available moving-average values
- **THEN** the candle inspector identifies that historical candle
- **AND** the trend legend shows MA values computed at that same candle timestamp

#### Scenario: No historical candle is selected
- **WHEN** the crosshair is not selecting a historical candle
- **THEN** the trend legend shows the newest candle's available MA values
- **AND** it does not obscure the latest price label or the primary price action

### Requirement: Focused Recent Trend View
The market chart SHALL retain the full loaded candle buffer while initially focusing a new contract or bar-period context on no more than the newest 48 candles, with the newest edge visible. The `最新` control SHALL restore that same focused window without refetching data or changing the selected contract, period, indicator values, or retained historical candles.

#### Scenario: User opens a 15-minute chart
- **WHEN** normalized candles become available for a newly opened or changed 15-minute chart context
- **THEN** the visible logical range includes at most the newest 48 loaded candles and a small latest-edge margin
- **AND** candle bodies, wicks, moving-average lines, and synchronized volume remain visually distinguishable

#### Scenario: User returns from history to the newest view
- **WHEN** a user has panned or zoomed to historical candles and activates `最新`
- **THEN** the chart returns to the newest focused window
- **AND** the selected instrument, bar period, retained history, and realtime subscription remain unchanged

### Requirement: Active Price and Visible-Range Context
The market chart SHALL preserve a latest-price anchor in the price pane and SHALL display a countdown to close only while the newest candle is unconfirmed and its selected bar duration can be determined. It SHALL annotate no more than one highest-price point and one lowest-price point within the current visible candle range, without creating trade recommendations or price predictions.

#### Scenario: Current candle remains open
- **WHEN** the newest candle is unconfirmed and has a valid timestamp for the selected bar period
- **THEN** the chart shows the latest price anchor and a countdown to that candle's scheduled close
- **AND** the countdown updates without changing the candle's reported market values

#### Scenario: User changes the visible chart range
- **WHEN** a user pans, zooms, changes period, or the chart receives replacement candle data
- **THEN** the high and low annotations are recalculated from normalized candles in the visible range
- **AND** the chart shows no more than one high annotation and one low annotation

#### Scenario: Historical exploration receives a realtime update
- **WHEN** a user is viewing a historical range and a realtime candle update arrives
- **THEN** the historical visible range remains in place
- **AND** its visible-range annotations remain based on that historical range until the user changes the range or activates `最新`

### Requirement: Read-Only Trend Interpretation Boundaries
The market chart SHALL present these overlays and annotations as descriptive market data only. It MUST NOT use moving-average crosses, extrema, countdowns, or price placement to render buy/sell calls, automated signals, order-entry actions, forecasts, or investment recommendations.

#### Scenario: Trend overlays are visible
- **WHEN** a user views MA lines, a current-price anchor, or high/low annotations
- **THEN** the page describes the displayed values as chart context
- **AND** it does not render an action recommendation or an order-execution control as a consequence of those values
