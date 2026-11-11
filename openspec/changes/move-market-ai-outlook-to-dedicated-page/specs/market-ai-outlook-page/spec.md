## ADDED Requirements

### Requirement: Dedicated Market AI Outlook Page
The system SHALL provide a dedicated market subpage for viewing AI market-reading reports.

#### Scenario: User opens the AI outlook route
- **WHEN** the user navigates to `#/market/ai-outlook`
- **THEN** the application MUST render an AI market outlook page under the market section
- **AND** the market secondary navigation MUST show `AI看行情` as the active page
- **AND** the page MUST use the default contract when no valid `inst` query parameter is present

#### Scenario: Route includes selected contract and period
- **WHEN** the user navigates to `#/market/ai-outlook?inst=ETH-USDT-SWAP&bar=5m`
- **THEN** the page MUST select `ETH-USDT-SWAP`
- **AND** it MUST select the `5m` K-line period for the AI outlook request

### Requirement: Chart Page AI Entry
The market chart page SHALL act as an entry point to the dedicated AI outlook page.

#### Scenario: User clicks AI entry from chart page
- **WHEN** the user clicks `AI看行情` on the market chart page
- **THEN** the application MUST navigate to `#/market/ai-outlook` with the currently selected `inst` and `bar` query parameters
- **AND** the chart page MUST NOT render the full AI report inline

#### Scenario: Chart page receives realtime updates
- **WHEN** realtime ticker or candle updates arrive on the chart page
- **THEN** the chart page MUST NOT call the AI outlook endpoint automatically
- **AND** it MUST keep the K-line chart and selected-contract market data usable

### Requirement: Manual AI Report Execution
The dedicated AI outlook page SHALL only request AI analysis after an explicit user action.

#### Scenario: AI outlook page loads
- **WHEN** the dedicated AI outlook page loads
- **THEN** it MUST show an idle or previously selected state without automatically calling `POST /api/market/ai-outlook`
- **AND** it MUST provide a visible manual action to start analysis

#### Scenario: User starts analysis
- **WHEN** the user clicks `开始分析` or `刷新AI`
- **THEN** the frontend MUST call `POST /api/market/ai-outlook` with the selected `instId`, selected `bar`, bounded candle limit, and requested force flags
- **AND** it MUST show loading, success, fallback, warning, and error states without navigating away

#### Scenario: User changes contract or period
- **WHEN** the user selects a different contract or K-line period on the AI outlook page
- **THEN** the route query MUST update to reflect the new selection
- **AND** the page MUST NOT automatically call the AI outlook endpoint for the new selection

### Requirement: Full Report Layout
The dedicated AI outlook page SHALL render the complete user-reference report in a stable full-page layout.

#### Scenario: Report result is available
- **WHEN** the backend returns an AI outlook response
- **THEN** the page MUST show overall view, reference confidence, summary, future 15-minute view, future 1-hour view, today view, key factors, K-line factors, focus items, reassessment conditions, source references, warnings, and reference notes
- **AND** the three horizon views MUST remain visually distinct from order, automation, and signal controls

#### Scenario: Report contains warnings or fallback data
- **WHEN** the outlook response contains warnings, cached analysis, partial macro data, fallback analysis, or source freshness metadata
- **THEN** the page MUST display that context clearly
- **AND** it MUST avoid disruptive repeated flashing or large layout shifts while data changes

### Requirement: Read-Only Safety Boundary
The dedicated AI outlook page SHALL remain observational and SHALL NOT execute or prepare trading actions.

#### Scenario: User views or refreshes an AI report
- **WHEN** the user generates or refreshes an AI market outlook
- **THEN** the system MUST NOT place orders, prefill a trade ticket, create an automation strategy, change leverage, or mutate account/trading state
- **AND** the page MUST label the report as user reading reference that does not affect automated trading

#### Scenario: Report uses directional wording
- **WHEN** the report includes directional bias or horizon views
- **THEN** the UI MUST present them as reference views rather than trade signals, entry triggers, or execution instructions
