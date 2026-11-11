## ADDED Requirements

### Requirement: Selected Contract Stats
The system SHALL provide trading statistics for the currently selected OKX SWAP contract on the market chart page.

#### Scenario: Load stats for selected contract
- **WHEN** the user opens the market chart page with `BTC-USDT-SWAP` selected
- **THEN** the system retrieves trading statistics for `BTC-USDT-SWAP`
- **AND** the displayed statistics are scoped to that selected contract rather than only the base currency.

#### Scenario: Change selected contract
- **WHEN** the user selects a different live SWAP contract from the market instrument list
- **THEN** the system reloads trading statistics for the newly selected contract
- **AND** stale statistics from the previous contract are not presented as current values for the new contract.

### Requirement: Contract Long Short Ratio
The system SHALL show the selected contract's long/short account ratio from a contract-level OKX Trading Statistics source.

#### Scenario: Display latest long short account ratio
- **WHEN** contract long/short account ratio data is available
- **THEN** the market chart page displays the latest ratio with a label that identifies it as a contract-level account ratio.
- **AND** the page provides a plain-language directional hint such as more net-long accounts, balanced accounts, or more net-short accounts.

#### Scenario: Distinguish contract and currency ratios
- **WHEN** the selected contract is `BTC-USDT-SWAP`
- **THEN** the primary long/short ratio uses data requested by `instId=BTC-USDT-SWAP`
- **AND** the page does not replace it with a currency-level ratio requested only by `ccy=BTC`.

### Requirement: Contract Taker Buy Sell Stats
The system SHALL show selected-contract taker buy and sell volume statistics.

#### Scenario: Display taker buy sell balance
- **WHEN** contract taker buy/sell data is available
- **THEN** the market chart page displays taker buy volume, taker sell volume, and derived active buy share or buy/sell ratio.
- **AND** the displayed labels make clear that the values represent active taker buying and selling, not total 24h ticker volume.

#### Scenario: Handle zero or missing side volume
- **WHEN** one side of taker volume is zero or unavailable
- **THEN** the system avoids invalid ratio output such as infinity or NaN
- **AND** the UI shows an understandable empty, unavailable, or one-sided state.

### Requirement: Contract Open Interest Stats
The system SHALL show selected-contract open interest history and latest open interest values.

#### Scenario: Display latest open interest
- **WHEN** contract open interest history is available
- **THEN** the market chart page displays the latest open interest in available units such as contracts, coin, or USD.
- **AND** the page shows whether open interest increased, decreased, or was flat over the returned series.

#### Scenario: Compare price and open interest without advice
- **WHEN** both candle price data and open interest data are available
- **THEN** the market chart page may describe the relationship as observation context
- **AND** the page must not phrase that relationship as a direct instruction to buy, sell, long, or short.

### Requirement: Stats Period Transparency
The system SHALL make the effective trading-statistics period visible whenever it may differ from the selected K-line period.

#### Scenario: One minute chart with five minute stats
- **WHEN** the chart period is `1m` and trading statistics are loaded using `5m`
- **THEN** the market chart page displays `5m` as the statistics period
- **AND** the page does not imply that statistics are sampled at the chart's `1m` cadence.

#### Scenario: Supported matching period
- **WHEN** the selected chart period is supported by all first-version trading-statistics metrics
- **THEN** the system may request statistics using the matching period
- **AND** the UI displays that shared period.

### Requirement: Stats Loading And Error States
The system SHALL keep the existing market chart usable when trading statistics are loading, partially unavailable, or failing.

#### Scenario: Statistics loading
- **WHEN** selected-contract trading statistics are still loading
- **THEN** the market chart and ticker values remain visible
- **AND** the statistics area displays a loading state scoped to statistics only.

#### Scenario: Partial metric failure
- **WHEN** one trading-statistics metric fails but other metrics succeed
- **THEN** the successful metrics remain visible
- **AND** the failed metric displays a metric-specific warning or unavailable state.

#### Scenario: All statistics unavailable
- **WHEN** OKX trading-statistics data cannot be loaded for the selected contract
- **THEN** the existing candles, ticker values, and instrument list remain usable
- **AND** the page displays a non-blocking warning for the statistics panel.
