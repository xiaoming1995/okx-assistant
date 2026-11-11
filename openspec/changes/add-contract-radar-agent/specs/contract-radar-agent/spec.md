## ADDED Requirements

### Requirement: Radar scan returns ranked contract candidates

The system SHALL provide a contract radar scan for OKX SWAP instruments that returns ranked contract candidates with normalized market metrics, scores, tags, reasons, warnings, timestamp, source, and cache age.

#### Scenario: Successful radar scan
- **WHEN** the user requests a contract radar scan
- **THEN** the system returns a ranked list of SWAP contract candidates ordered by opportunity score descending
- **AND** each result includes instrument id, latest price, 24h change, 24h volume, tradability score, volatility score, opportunity score, risk level, tags, reasons, and warnings

#### Scenario: Empty market data
- **WHEN** OKX market data is unavailable and no cached radar snapshot exists
- **THEN** the system returns an empty radar result with a warning explaining that market data is unavailable

### Requirement: Radar scan filters unsuitable contracts

The system SHALL exclude or penalize unsuitable contracts before ranking by opportunity.

#### Scenario: Non-live instruments are filtered
- **WHEN** an instrument is not in live state
- **THEN** the radar scan excludes the instrument from the default ranked results

#### Scenario: Low-volume instruments are penalized
- **WHEN** a contract has volume below the configured minimum threshold
- **THEN** the radar scan either excludes it or marks it with a high-risk warning before it can appear in results

#### Scenario: Missing candle data is penalized
- **WHEN** a candidate contract has missing or insufficient recent candles
- **THEN** the radar scan lowers its confidence or score and includes a data-quality warning

### Requirement: Radar scoring is deterministic

The system MUST compute numeric radar scores from market data using deterministic scoring logic before any LLM explanation is requested.

#### Scenario: Same data produces same scores
- **WHEN** the same instruments, tickers, candles, and scan settings are provided
- **THEN** the radar scoring returns the same tradability, volatility, risk, and opportunity scores

#### Scenario: LLM does not alter numeric rank
- **WHEN** LLM explanations are enabled for a radar scan
- **THEN** the LLM output does not change numeric scores or ranking order

### Requirement: Radar uses staged market data collection

The system SHALL first use instrument and ticker data to select a bounded candidate set, then fetch recent candle data only for candidates that pass the initial filter.

#### Scenario: Candidate set is bounded
- **WHEN** the market contains more contracts than the configured radar candidate limit
- **THEN** the system fetches candle data only for the bounded candidate set selected by initial ticker and instrument filters

#### Scenario: User changes filters
- **WHEN** the user changes settlement currency, minimum volume, volatility, or risk filters
- **THEN** the radar returns results that match the selected filters without requiring unrelated contract pages to reload

### Requirement: Radar explanations are concise and evidence-based

The system SHALL provide concise explanations for top radar candidates using only metrics included in the scan payload.

#### Scenario: Explanation generated for top candidates
- **WHEN** LLM explanations are enabled and the scan has eligible top candidates
- **THEN** each explained candidate includes short reasons and risk notes grounded in the provided market metrics

#### Scenario: Explanation fallback
- **WHEN** LLM configuration is missing or the LLM request fails
- **THEN** the radar still returns deterministic scores and metric-based fallback reasons

### Requirement: Radar results are cached

The system SHALL cache or persist radar scan snapshots with freshness metadata to avoid repeated full scans on frequent refreshes.

#### Scenario: Fresh cache is available
- **WHEN** the user requests radar results within the configured freshness window
- **THEN** the system returns the cached radar snapshot with source and cache age metadata

#### Scenario: Force refresh
- **WHEN** the user explicitly requests a force refresh
- **THEN** the system attempts a fresh scan and updates the cached snapshot if the scan succeeds

#### Scenario: Fresh scan fails with stale cache
- **WHEN** a fresh scan fails but a previous radar snapshot exists
- **THEN** the system returns the stale snapshot with a warning describing the failure

### Requirement: Radar UI presents a clear contract selection workflow

The frontend SHALL provide a contract radar view that is simple to scan and supports choosing a contract for further review.

#### Scenario: User reviews ranked contracts
- **WHEN** the user opens the contract radar view
- **THEN** the UI displays summary status, filters, ranked contract rows, score values, key metrics, tags, and warnings without requiring the user to open each chart

#### Scenario: User opens contract details
- **WHEN** the user selects a radar result
- **THEN** the UI shows a focused detail area with the contract's key reasons, risk warnings, and recent market metrics

#### Scenario: User continues to existing workflows
- **WHEN** the user chooses an action from a radar result
- **THEN** the system opens the existing market, manual trade, or automation workflow with that contract selected

### Requirement: Radar communicates limitations

The system MUST communicate that radar scores indicate market suitability and volatility, not guaranteed profit or a direct trading instruction.

#### Scenario: Score labeling avoids trade guarantees
- **WHEN** radar scores or explanations are shown
- **THEN** labels and text describe contracts as suitable to watch, active, volatile, risky, or not recommended rather than guaranteed profitable
