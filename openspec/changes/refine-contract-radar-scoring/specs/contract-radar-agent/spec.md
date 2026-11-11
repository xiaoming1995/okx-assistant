## ADDED Requirements

### Requirement: Radar normalizes liquidity metrics
The radar API SHALL expose comparable liquidity metrics and the source unit used for each contract result.

#### Scenario: Quote turnover is available
- **WHEN** a USDT or USDC-settled SWAP ticker includes quote-currency 24h turnover
- **THEN** the radar result uses that value as the primary liquidity metric
- **AND** the result labels the liquidity basis as quote turnover

#### Scenario: Quote turnover is unavailable
- **WHEN** quote-currency 24h turnover is unavailable but another OKX volume field is available
- **THEN** the radar result includes the fallback value
- **AND** the result labels whether the fallback is base volume or contract volume
- **AND** the result lowers liquidity confidence compared with a result that has quote turnover

#### Scenario: Quote turnover can be estimated for linear swaps
- **WHEN** quote-currency 24h turnover is unavailable for a USDT or USDC-settled SWAP
- **AND** base-currency 24h volume and latest price are available
- **THEN** the radar result calculates estimated quote turnover from base volume and latest price
- **AND** the result labels the liquidity basis as estimated quote turnover
- **AND** the result treats the metric as comparable with medium confidence

#### Scenario: Liquidity value is displayed
- **WHEN** the frontend displays a radar row or detail panel
- **THEN** the UI shows the 24h liquidity value with a clear unit or basis label

### Requirement: Radar applies a tradability gate before default ranking
The radar SHALL classify each candidate's tradability before assigning its default rank.

#### Scenario: Contract passes tradability gate
- **WHEN** a contract is live, has sufficient comparable 24h liquidity, and has sufficient recent candle data
- **THEN** the radar marks the contract as playable
- **AND** the contract is eligible for the default top ranking

#### Scenario: Contract fails liquidity gate
- **WHEN** a contract has insufficient comparable 24h liquidity
- **THEN** the radar marks the contract as low-liquidity or watch-only
- **AND** the contract does not outrank playable contracts in the default ranking solely because volatility is high

#### Scenario: Contract has weak data quality
- **WHEN** a contract has missing ticker data, missing liquidity basis, or insufficient recent candles
- **THEN** the radar lowers the contract's tradability classification
- **AND** the radar includes a data-quality warning

### Requirement: Radar ranking explains its sort semantics
The radar SHALL make clear that the default ranking is a contract-selection ranking, not a raw volume or volatility ranking.

#### Scenario: Default ranking is returned
- **WHEN** the radar returns default results
- **THEN** playable contracts are ordered before non-playable contracts
- **AND** playable contracts are ordered by opportunity score, liquidity score, and volatility score in that priority order

#### Scenario: User reviews ranking in the UI
- **WHEN** the user opens the radar page
- **THEN** the UI indicates that the default rank combines tradability, liquidity, volatility, and risk
- **AND** the UI does not imply that the first result has the highest 24h volume

#### Scenario: Low-liquidity high-volatility contract is returned
- **WHEN** a low-liquidity contract appears in radar results because filters allow it
- **THEN** the UI labels it as watch-only or low-liquidity
- **AND** its warnings explain that volatility alone is not enough to make it a primary candidate

### Requirement: Radar preserves deterministic scoring boundaries
The radar MUST keep numeric scoring and ranking deterministic and independent from LLM-generated text.

#### Scenario: LLM explanation is enabled
- **WHEN** LLM explanations are enabled for radar results
- **THEN** the LLM may update reasons or warnings
- **AND** the LLM does not modify liquidity metrics, tradability classification, scores, or ranking order

#### Scenario: Same inputs are rescored
- **WHEN** the same instrument, ticker, candle, and filter inputs are processed
- **THEN** the radar returns the same tradability classification, liquidity basis, scores, and relative rank

## MODIFIED Requirements

### Requirement: Radar scan returns ranked contract candidates
The system SHALL provide a contract radar scan for OKX SWAP instruments that returns ranked contract candidates with normalized market metrics, liquidity basis, tradability classification, scores, tags, reasons, warnings, timestamp, source, and cache age.

#### Scenario: Successful radar scan
- **WHEN** the user requests a contract radar scan
- **THEN** the system returns a ranked list of SWAP contract candidates ordered by default contract-selection rank
- **AND** each result includes instrument id, latest price, 24h change, 24h liquidity value, liquidity basis, tradability classification, volatility score, opportunity score, risk level, tags, reasons, and warnings

#### Scenario: Empty market data
- **WHEN** OKX market data is unavailable and no cached radar snapshot exists
- **THEN** the system returns an empty radar result with a warning explaining that market data is unavailable

### Requirement: Radar scan filters unsuitable contracts
The system SHALL exclude, demote, or clearly label unsuitable contracts before ranking by opportunity.

#### Scenario: Non-live instruments are filtered
- **WHEN** an instrument is not in live state
- **THEN** the radar scan excludes the instrument from the default ranked results

#### Scenario: Low-volume instruments are demoted
- **WHEN** a contract has comparable liquidity below the configured tradability threshold
- **THEN** the radar scan marks it as low-liquidity or watch-only
- **AND** the default ranking places it below playable contracts even if its volatility score is high

#### Scenario: Missing candle data is penalized
- **WHEN** a candidate contract has missing or insufficient recent candles
- **THEN** the radar scan lowers its confidence or score and includes a data-quality warning
