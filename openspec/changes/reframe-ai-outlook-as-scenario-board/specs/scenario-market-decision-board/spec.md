## ADDED Requirements

### Requirement: AI outlook SHALL present one deterministic scenario evidence score
The AI outlook SHALL expose a deterministic scenario evidence score derived from the report snapshot's rule-based decision. The primary AI outlook header and scenario board MUST use this score when describing evidence sufficiency. An LLM-generated overall confidence value MUST NOT be presented as the same evidence-sufficiency measure.

#### Scenario: Narrative and rule score differ
- **WHEN** an LLM narrative contains an overall confidence of 58 while the deterministic neutral decision is capped at 45
- **THEN** the primary report SHALL show 45 as the scenario evidence score and SHALL not label 58 as evidence sufficiency

### Requirement: AI outlook SHALL present current state and two conditional scenarios
The AI outlook SHALL render the current price state plus a bullish and bearish conditional scenario from the same chart snapshot. Each scenario MUST include an explicit complete-candle close condition, the relevant available or missing structure evidence, and an invalidation or re-read condition. Conditions MUST be labelled as market-observation conditions rather than execution instructions.

#### Scenario: Price remains inside the observation range
- **WHEN** the last close remains between the snapshot's recent lower and upper levels
- **THEN** the board SHALL identify the market as inside the observation range and show both upper and lower conditional scenarios with their confirmation prices

#### Scenario: A directional structure clue is present without price confirmation
- **WHEN** active selling is below its bearish threshold but the price has not completed a lower-bound close
- **THEN** the board SHALL identify selling pressure as an observed clue while retaining a conditional bearish scenario rather than a confirmed direction

### Requirement: Missing data SHALL visibly limit scenario confirmation
The AI outlook SHALL identify missing directional inputs as a scenario limitation. If required directional trading-structure evidence is unavailable, the relevant candidate scenario MUST state that reaching its price condition alone cannot create a complete confirmation.

#### Scenario: Long-short account data is unavailable
- **WHEN** long-short account data is unavailable for the report snapshot
- **THEN** both scenario cards SHALL name the missing data and state its effect on complete direction confirmation

### Requirement: Evidence detail SHALL remain inspectable without crowding the decision path
The AI outlook SHALL place the scenario board before detailed evidence. Detailed thresholds, evidence gaps, AI narrative metadata, and source details MUST remain available in a secondary detail area. Reports cached before the scenario board fields existed MUST render a safe refresh-oriented fallback.

#### Scenario: Older cached report is opened
- **WHEN** a cached AI outlook lacks scenario-board fields
- **THEN** the page SHALL preserve the older report, show its available conditional levels, and explain that refreshing produces the complete scenario board
