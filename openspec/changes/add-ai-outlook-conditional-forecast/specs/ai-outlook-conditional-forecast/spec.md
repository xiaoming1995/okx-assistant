## ADDED Requirements

### Requirement: Conditional short-horizon outlook
The manual AI market report SHALL render a `条件推演` section when its response contains usable recognized horizon entries. The section MUST present at most the 15-minute, one-hour, and current-day entries in that order, and MUST identify each entry's timeframe, directional observation, and reference confidence.

#### Scenario: Report contains all supported horizons
- **WHEN** a manually generated report returns usable `15m`, `1h`, and `today` horizon entries
- **THEN** the report displays three compact conditional forecast cards in chronological order with their translated labels and confidence

#### Scenario: Report omits a horizon
- **WHEN** a manually generated report does not return a usable entry for one or more supported horizons
- **THEN** the report omits the unavailable entry and does not invent a forecast

### Requirement: Forecast remains chart-grounded and conditional
Each displayed forecast SHALL describe a scenario from the chart snapshot used by the report, include one concise condition or re-read cue when available, and MUST make clear that the outlook is conditional rather than a guaranteed price outcome. Raw implementation field names and external macro/source failures MUST NOT appear in a primary forecast card.

#### Scenario: Chart data supports a conditional outlook
- **WHEN** a horizon entry includes summary, watch, or risk text grounded in the current chart snapshot
- **THEN** the card presents reader-facing Chinese text and a concise condition or re-read cue

#### Scenario: External data is degraded
- **WHEN** supplementary macro or source data is unavailable while chart data remains usable
- **THEN** the forecast section remains readable from the chart snapshot and the external degradation remains in secondary supplemental details

### Requirement: Manual and read-only forecast behavior
The report SHALL only show forecasts after the user manually starts or refreshes analysis. It MUST retain the existing visible no-order, no-automation boundary and MUST NOT trigger an extra AI request when displaying, changing, or resizing forecast cards.

#### Scenario: First entry before analysis
- **WHEN** a user opens the AI market report before manually starting analysis
- **THEN** no forecast is generated or displayed as if it were current

#### Scenario: User reads the forecast
- **WHEN** a user views a displayed conditional forecast
- **THEN** the report continues to state that it is reading-only and does not submit or alter any order or automation
