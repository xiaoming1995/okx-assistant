## ADDED Requirements

### Requirement: AI market analysis is manually triggered

The system SHALL run LLM market analysis only after the user explicitly requests AI analysis from the Contract Radar experience.

#### Scenario: Radar page opens without AI call

- **WHEN** the user opens Contract Radar
- **THEN** the system SHALL NOT call the LLM for market analysis automatically

#### Scenario: User requests AI market analysis

- **WHEN** the user clicks the AI market analysis action after a radar scan is available
- **THEN** the system SHALL request market analysis for the current radar scan context

### Requirement: System builds a compact market summary

The system SHALL build a bounded structured summary from market data before calling the LLM.

#### Scenario: Summary contains market breadth and leaders

- **WHEN** AI market analysis is requested
- **THEN** the summary SHALL include scan counts, freshness timestamp, market breadth, liquidity distribution, volatility distribution, risk counts, and deterministic radar leaders

#### Scenario: Summary avoids unbounded raw rows

- **WHEN** the market universe contains many contracts or candles
- **THEN** the LLM payload SHALL cap top lists and SHALL NOT include raw rows for every contract or every candle

### Requirement: LLM returns market-level analysis

The system SHALL return structured market-level analysis grounded in the supplied summary data.

#### Scenario: Successful LLM analysis

- **WHEN** the LLM returns a valid analysis response
- **THEN** the response SHALL include market regime, confidence, concise summary, highlights, watchlist, risk warnings, generated time, source, and warnings

#### Scenario: Watchlist explains evidence

- **WHEN** the response includes watchlist contracts
- **THEN** each watchlist item SHALL include a contract identifier, reason, and risk note based on supplied radar metrics

### Requirement: LLM does not control ranking or trading

The system SHALL keep deterministic radar scoring, ranking, tradability status, and trading actions outside LLM control.

#### Scenario: AI analysis completes

- **WHEN** AI market analysis returns successfully
- **THEN** existing radar candidate scores, rank order, tradability status, liquidity labels, and risk labels SHALL remain unchanged

#### Scenario: AI analysis suggests contracts

- **WHEN** the LLM returns watchlist or suggested filter content
- **THEN** the system SHALL NOT place orders, create strategies, or emit direct buy/sell instructions from that content

### Requirement: Analysis handles missing or failed LLM calls

The system SHALL return a usable fallback analysis when LLM configuration is missing, the LLM request fails, or the LLM response cannot be parsed.

#### Scenario: LLM unavailable

- **WHEN** the user requests AI market analysis and LLM configuration is unavailable
- **THEN** the system SHALL return deterministic metric-based fallback analysis with a warning that AI analysis was not available

#### Scenario: LLM response invalid

- **WHEN** the LLM response cannot be parsed into the required structure
- **THEN** the system SHALL return fallback analysis and SHALL include a warning describing the fallback condition

### Requirement: Analysis includes freshness and cache metadata

The system SHALL expose freshness metadata for AI market analysis responses.

#### Scenario: Fresh cached analysis exists

- **WHEN** the user requests analysis for an unchanged scan context with a fresh cached result
- **THEN** the system SHALL return the cached analysis with cache age and source metadata

#### Scenario: User forces refresh

- **WHEN** the user explicitly requests fresh AI analysis
- **THEN** the system SHALL attempt a new LLM analysis for the current scan context

### Requirement: Frontend presents concise AI market analysis

The Contract Radar UI SHALL present AI market analysis as a compact, clearly separated decision-support panel.

#### Scenario: Analysis panel renders

- **WHEN** AI market analysis is available
- **THEN** the UI SHALL show market regime, confidence, summary, key highlights, watchlist, risks, freshness, and warning metadata without replacing the deterministic ranking table

#### Scenario: Analysis is loading or unavailable

- **WHEN** AI market analysis is loading or unavailable
- **THEN** the UI SHALL show a clear loading, empty, or fallback state without auto-triggering another LLM request
