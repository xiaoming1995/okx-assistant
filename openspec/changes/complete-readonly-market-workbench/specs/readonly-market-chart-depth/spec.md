## ADDED Requirements

### Requirement: Synchronized Price and Volume Reading
The market chart SHALL render a price pane and a smaller, time-synchronized candle-volume pane for the selected SWAP contract and period. It MUST label valid SWAP candle volume in contracts and MUST NOT invent a zero or another unit for missing volume.

#### Scenario: Valid candle volume is available
- **WHEN** the selected contract's candle snapshot contains valid volume values
- **THEN** the chart displays direction-colored volume columns aligned with their price candles
- **AND** the volume pane identifies its values as contracts (`张`)

#### Scenario: Volume is unavailable
- **WHEN** candle rows are missing a usable volume value
- **THEN** the price chart remains usable
- **AND** the volume region communicates that volume is unavailable without rendering a fabricated zero

#### Scenario: User inspects history during an update
- **WHEN** the user inspects or pans to a historical candle and a newer candle arrives
- **THEN** the inspector and volume reading refer to the inspected candle
- **AND** the update does not reset the user's historical view

### Requirement: Read-Only Selected-Contract Order Book
The chart route SHALL offer a public order-book snapshot for its selected SWAP contract, with the closest asks and bids, price, per-level quantity, cumulative quantity, spread where valid, and source snapshot time. All displayed quantities MUST have an explicit contract unit. The panel MUST NOT expose order submission controls.

#### Scenario: Complete order book arrives
- **WHEN** a fresh valid snapshot for the selected contract contains asks and bids
- **THEN** the panel displays up to 10 levels per side around a spread row
- **AND** labels ask and bid sides and both quantity columns in contracts (`张`)
- **AND** shows the snapshot time and a fresh status

#### Scenario: Contract changes while a request is pending
- **WHEN** the user selects another contract before an order-book request completes
- **THEN** rows from the previous contract are removed from the current panel
- **AND** any late response for the previous contract is ignored

#### Scenario: Spread cannot be trusted
- **WHEN** either side is missing, prices are invalid, or best ask is not above best bid
- **THEN** the panel does not display a normal positive spread
- **AND** it communicates that the spread is unavailable or the snapshot is abnormal

### Requirement: Bounded Order-Book Freshness
The system SHALL fetch order-book data only for the selected visible chart, share a bounded backend cache for concurrent viewers, and expose source time and cache age. It MUST distinguish initial loading, updating, retained cache, completed empty, and unavailable states. It MUST NOT show a snapshot older than 15 seconds as current depth.

#### Scenario: First snapshot is loading
- **WHEN** the selected contract has no complete order-book snapshot and its first request is pending
- **THEN** the panel displays a labelled loading state rather than empty rows

#### Scenario: Refresh is in progress
- **WHEN** a previously complete snapshot refreshes before its maximum retained age
- **THEN** the rows remain visible with an updating or cached label and source time

#### Scenario: Refresh fails with retained data
- **WHEN** the public source fails and a complete snapshot is no more than 15 seconds old
- **THEN** the panel may retain those rows with a clearly labelled cache age and retry status
- **AND** it does not expose the raw upstream exception

#### Scenario: Snapshot expires or no data exists
- **WHEN** no usable snapshot exists or the last complete snapshot is older than 15 seconds
- **THEN** the panel hides stale price levels and displays an unavailable or completed-empty state with a recovery hint

#### Scenario: Chart is hidden
- **WHEN** the chart route is unmounted or the browser document is hidden
- **THEN** the frontend stops its order-book polling until the chart becomes visible again

### Requirement: Explicit Market Summary Basis
The chart summary and shared contract rail SHALL identify the period and unit of 24-hour activity and change metrics. `24h 成交额` MUST use a verified 24-hour quote-turnover value in the selected contract's quote currency. When only base-currency or contract volume is available, the label MUST change to `24h 成交量` with that actual unit. `今日涨跌（UTC+8）` MUST use the UTC+8 start-of-day price. No metric may silently fall back to a different period or unit.

#### Scenario: Complete ticker fields exist
- **WHEN** the selected ticker has `volCcyQuote24h` and `sodUtc8`
- **THEN** the summary displays `24h 成交额` with the quote currency and today change with an explicit UTC+8 basis

#### Scenario: Only 24-hour base or contract volume exists
- **WHEN** quote turnover is absent but `volCcy24h` or `vol24h` exists
- **THEN** the summary and contract rail show `24h 成交量` in base currency or contracts, respectively
- **AND** they do not display a quote-currency symbol for that value

#### Scenario: A required ticker field is missing
- **WHEN** all 24-hour activity fields or the UTC+8 day-open field are absent
- **THEN** the corresponding metric displays an unavailable state
- **AND** no single-candle, base-volume, contract-volume, UTC+0, or rolling-24-hour value appears under that metric's label

### Requirement: Responsive Chart and Depth Layout
The chart route SHALL preserve readable price and volume panes as its primary content and place the order book beside them only when available main-content width permits. At narrower widths it SHALL present the order book after the chart in a natural reading flow, without document-wide horizontal overflow.

#### Scenario: Wide desktop content area
- **WHEN** the main workbench has enough width for chart and depth to coexist
- **THEN** the chart remains the larger region and the depth panel appears beside it

#### Scenario: Constrained desktop or narrow viewport
- **WHEN** the chart and depth cannot coexist at readable widths
- **THEN** the order book flows below the price and volume panes
- **AND** the contract summary, period controls, chart, volume, and depth remain reachable in that order

#### Scenario: Data states and keyboard use
- **WHEN** the panel is loading, empty, cached, unavailable, or focused by keyboard
- **THEN** its status and any available action have readable text and visible focus treatment consistent with the frontend design guide
