## ADDED Requirements

### Requirement: Forecast cards use their available report width
The manual AI outlook SHALL lay out one, two, or three usable conditional forecast cards according to the number of recognized horizons returned for the current chart snapshot. The layout MUST not reserve an empty forecast column for an absent horizon.

#### Scenario: Two forecast horizons are available
- **WHEN** the report contains usable `15m` and `1h` forecasts but no usable `today` forecast
- **THEN** the two forecast cards occupy equal columns across the available forecast row

#### Scenario: One forecast horizon is available
- **WHEN** the report contains exactly one usable recognized forecast
- **THEN** that forecast card occupies the available forecast row without an adjacent empty track

#### Scenario: Narrow display preserves readability
- **WHEN** the available display width cannot preserve a readable forecast card width
- **THEN** the forecast cards stack into one column without clipping their content

### Requirement: Forecast cards present a compact reading hierarchy
Each conditional forecast card SHALL present its human-readable horizon and confidence together, then its directional observation, chart-grounded summary, and one re-read condition. The report MUST retain the conditional-prediction notice and the existing no-trading safety boundary.

#### Scenario: User scans a generated forecast
- **WHEN** a user views a generated conditional forecast card
- **THEN** the timeframe, confidence, directional observation, summary, and re-read condition are readable without redundant vertically stacked metadata

#### Scenario: Forecast content is lengthy
- **WHEN** a forecast summary or re-read condition contains a longer chart-grounded explanation
- **THEN** the card remains content-sized and displays the complete explanation rather than hiding it through truncation
