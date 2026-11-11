## ADDED Requirements

### Requirement: OKX platform activity is accurately scoped
The system SHALL show OKX platform rolling 24-hour order-book trading volume in USD from the documented public endpoint, with source and update time. It MUST NOT label this value as global cryptocurrency turnover or market capitalization.

#### Scenario: Complete platform response
- **WHEN** OKX returns a valid `volUsd` and timestamp
- **THEN** the overview shows the value under `OKX 平台 24 小时成交额（USD）` with an update time

#### Scenario: Incomplete platform response
- **WHEN** the platform response has no valid USD volume or timestamp
- **THEN** the overview shows an unavailable state and does not display zero as a substitute

### Requirement: Overview sections remain independent
The overview SHALL reuse the existing ticker and US event endpoints and SHALL identify their different sources and scopes. A failure or empty result in one section MUST NOT hide valid data in another.

#### Scenario: Tickers available and events unavailable
- **WHEN** the ticker snapshot contains a featured perpetual contract but the event feed fails
- **THEN** that contract remains visible and the event section shows a local error state

#### Scenario: Upcoming events available
- **WHEN** the event feed returns future events
- **THEN** the overview shows the nearest events with Shanghai-time labels and a link to the full timeline

### Requirement: Freshness and responsive states are explicit
The overview SHALL show loading, fresh, cached, empty, and unavailable states where applicable, retain complete values while refreshing, and remain usable at desktop and narrow widths.

#### Scenario: Platform refresh fails with recent cache
- **WHEN** OKX platform volume refresh fails and a complete snapshot is less than 15 minutes old
- **THEN** the previous value remains visible with a cached label and original update time

#### Scenario: Cache expired
- **WHEN** the last complete platform snapshot exceeds 15 minutes and the refresh fails
- **THEN** the platform value is hidden and the section shows an unavailable state

#### Scenario: Narrow display
- **WHEN** the page is viewed at a width of 390 pixels
- **THEN** all three sections, source labels, update states, and navigation remain readable without page-level horizontal overflow
