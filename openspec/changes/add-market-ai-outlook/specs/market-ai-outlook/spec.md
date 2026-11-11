## ADDED Requirements

### Requirement: Manual Market AI Outlook
The system SHALL provide a manual AI outlook action for the selected market chart contract and K-line period.

#### Scenario: User requests an outlook from the chart page
- **WHEN** the user clicks the "AI看行情" action on the market chart page
- **THEN** the frontend MUST send the selected `instId` and `bar` to a read-only backend AI outlook endpoint
- **AND** the system MUST show a loading state until an outlook, fallback, or error response is returned

#### Scenario: The page loads or realtime market data updates
- **WHEN** the market chart page loads, the selected contract changes, or realtime ticker/candle events arrive
- **THEN** the system MUST NOT automatically call the LLM outlook endpoint
- **AND** the user MUST remain in control of when token-consuming AI analysis runs

### Requirement: Macro Evidence Collection
The backend SHALL collect time-sensitive US macro context before asking the LLM to analyze a contract outlook.

#### Scenario: Macro sources are available
- **WHEN** the backend builds an AI outlook request
- **THEN** it MUST include current or scheduled CPI context and Federal Reserve policy/FOMC context when available
- **AND** each macro evidence item MUST include a source name, source URL when available, publish or schedule time when available, freshness metadata, and a concise normalized summary

#### Scenario: Macro source data is partial
- **WHEN** one macro provider fails but other macro or market evidence is available
- **THEN** the backend MUST continue building the outlook payload with the available evidence
- **AND** the response MUST include user-visible warnings for unavailable or stale macro sources

#### Scenario: Market-implied policy expectations are included
- **WHEN** the implementation includes a market-implied source for rate-hike/cut probability
- **THEN** the response MUST label that evidence as market expectation rather than an official Federal Reserve decision

### Requirement: Selected Contract Technical Evidence
The backend SHALL include bounded selected-contract market evidence in the AI outlook request.

#### Scenario: Recent market data is available
- **WHEN** the backend builds an outlook for a selected contract
- **THEN** it MUST include the selected contract identity, instrument metadata, current ticker snapshot, recent candle summary, and a capped list of recent candles for the selected period
- **AND** it MUST include derived fields such as recent trend, recent high/low, latest candle change, volatility/range, and volume context

#### Scenario: Candle or ticker data is stale or unavailable
- **WHEN** fresh OKX market data cannot be fetched
- **THEN** the backend MUST use cached candle or ticker data when available
- **AND** it MUST mark the market evidence source and cache age in the outlook response
- **AND** it MUST return a clear fallback warning if insufficient market evidence remains

### Requirement: Structured Outlook Response
The AI outlook endpoint SHALL return a strict structured response suitable for predictable UI rendering.

#### Scenario: LLM returns valid JSON
- **WHEN** the LLM returns a parseable outlook
- **THEN** the backend MUST normalize it into a response containing stance, confidence, summary, macro assessment, technical assessment, observation suggestion, source references, generated time, cache metadata, and warnings
- **AND** stance MUST be limited to `bullish`, `bearish`, `neutral`, or `wait`
- **AND** confidence MUST be clamped to the range 0 through 100

#### Scenario: User report horizons are available
- **WHEN** the endpoint returns an AI outlook
- **THEN** it MUST include an `overall` report summary for the selected contract
- **AND** it MUST include `horizons` entries for `15m`, `1h`, and `today`
- **AND** each horizon MUST include a user-readable label, bias, confidence, summary, watch items, and risk note
- **AND** the horizon content MUST be phrased as market-reading reference rather than automated trading signals

#### Scenario: LLM is unavailable or returns invalid JSON
- **WHEN** the LLM configuration is missing, the LLM request fails, or the LLM response cannot be parsed
- **THEN** the endpoint MUST return a deterministic fallback outlook based on macro and market evidence when possible
- **AND** the response MUST identify the source as fallback and include a warning explaining why LLM analysis was not used
- **AND** the fallback MUST still include the three user-report horizons when market evidence is available

### Requirement: Safety and Non-Execution Boundary
The market AI outlook SHALL remain read-only and SHALL NOT execute or prepare trades.

#### Scenario: Outlook is generated successfully
- **WHEN** the endpoint returns an outlook
- **THEN** the system MUST NOT place orders, prefill an order ticket, create an automation strategy, change leverage, or mutate account/trading state
- **AND** the output MUST avoid guaranteed-profit language and mandatory buy/sell wording

#### Scenario: User views the AI outlook panel
- **WHEN** the frontend renders the outlook
- **THEN** it MUST display risk notes or invalidation conditions alongside any directional bias
- **AND** it MUST label the result as analysis or observation guidance rather than an executed or automated trading action
- **AND** it MUST make clear that the report is only for user reading reference and does not overlap with automated trading signals

### Requirement: Caching, Refresh, and Usage Logging
The system SHALL cache macro snapshots and AI outlook results separately and SHALL record LLM usage through the existing usage log pipeline.

#### Scenario: Cached outlook is fresh
- **WHEN** the user requests an outlook for the same contract, K-line period, latest candle timestamp, ticker snapshot, macro snapshot, and prompt schema version within the configured freshness window
- **THEN** the backend MAY return the cached outlook
- **AND** it MUST include source and cache-age metadata so the frontend can label the result correctly

#### Scenario: User forces a fresh AI outlook
- **WHEN** the user clicks a refresh action for the AI outlook
- **THEN** the backend MUST bypass the AI outlook cache
- **AND** it MUST still respect macro-provider cache rules unless the request explicitly asks to force macro refresh

#### Scenario: LLM call is attempted
- **WHEN** the backend calls the configured LLM provider for a market AI outlook
- **THEN** it MUST record prompt, completion, total token, duration, status, model, provider, request type, selected contract, and K-line period using the existing LLM usage logging system

### Requirement: Chart Page AI Outlook UX
The frontend SHALL render the AI outlook in the market chart page without disrupting realtime chart updates.

#### Scenario: Outlook result is available
- **WHEN** the backend returns an AI outlook
- **THEN** the chart page MUST show a compact panel containing overall view, reference confidence, summary, 15-minute view, 1-hour view, today view, macro drivers, technical drivers, focus items, reassessment triggers, reference notes, and source freshness
- **AND** the chart, contract list, ticker updates, and K-line realtime updates MUST remain visible and usable

#### Scenario: Outlook has warnings or fallback data
- **WHEN** the outlook response includes warnings, stale cache, partial macro data, or fallback analysis
- **THEN** the frontend MUST display those states clearly without using disruptive layout shifts or repeated flashing warnings
