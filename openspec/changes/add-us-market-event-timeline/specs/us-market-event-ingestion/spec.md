## ADDED Requirements

### Requirement: Canonical Official Event Lifecycle
The system SHALL normalize supported official U.S. market events into one canonical event record identified by provider and provider event key, with lifecycle states `scheduled`, `released`, `revised`, or `cancelled`.

#### Scenario: A provider first publishes a future event
- **WHEN** a supported official provider supplies a future event with a stable identity
- **THEN** the system SHALL persist or update one canonical `scheduled` record
- **AND** it SHALL retain the provider, provider event key, source URL, source timezone, scheduled UTC time or date-only state, category, and importance

#### Scenario: A provider publishes a result or correction
- **WHEN** a source adds an actual value or changes previously published event facts
- **THEN** the system SHALL update the canonical event to `released` or `revised` as applicable
- **AND** it SHALL retain a chronological normalized version of the observed source state

### Requirement: Bounded Official Source Set
The system SHALL ingest only the approved high-impact source categories for the first release: Federal Reserve monetary-policy events; selected BLS inflation and employment releases; selected BEA growth, consumption, and trade releases; and Treasury auction events only when their official schedule can be reliably normalized.

#### Scenario: An approved source provides an event
- **WHEN** an approved source provides a supported event type
- **THEN** the system SHALL classify it with a supported category and official source attribution
- **AND** it SHALL retain a direct source URL for user verification

#### Scenario: An unapproved general news item is encountered
- **WHEN** an item is from a general news, social, rumor, or unapproved forecast source
- **THEN** the first-release ingestion flow SHALL not persist it as a timeline event
- **AND** it SHALL not supply it to an AI evidence request

### Requirement: Figure Integrity
The system SHALL preserve only sourced `actual`, `forecast`, `previous`, `revision`, `unit`, and period-label values and SHALL represent unavailable values explicitly.

#### Scenario: Official source lacks a market forecast
- **WHEN** an official source provides no attributable market-consensus forecast
- **THEN** the normalized event forecast SHALL remain unavailable
- **AND** the system SHALL not calculate, infer, or ask an LLM to fill it

#### Scenario: Source reports a revised prior value
- **WHEN** a source identifies a revision to an earlier reported value
- **THEN** the event SHALL retain the prior value and the revision value/context separately
- **AND** the event detail SHALL retain the older normalized version

### Requirement: Date and Title Binding Integrity
The system SHALL bind a supported official schedule title only to the explicit date and time in the same source calendar entry.

#### Scenario: An official calendar groups several days in one table row
- **WHEN** an official calendar uses a multi-day container or separate date/title cells
- **THEN** the parser SHALL use an unambiguous same-entry binding or omit the ambiguous candidate
- **AND** it SHALL not assign a title from one date to another date

#### Scenario: A successful BLS schedule refresh supersedes an old future preview
- **WHEN** a BLS official schedule provides a bounded future set of supported entries
- **THEN** unmatched future `scheduled` BLS previews within that source coverage SHALL be removed
- **AND** released or revised records SHALL remain retained

### Requirement: Historical Official Value Backfill
The system SHALL use the official BLS calendar as the sole release-date authority and the BLS data API as the sole actual/previous-value authority when backfilling supported historical BLS releases.

#### Scenario: A supported historical BLS release has calendar and data evidence
- **WHEN** the previous or current official BLS calendar contains a past supported release and the BLS data API contains the corresponding ordered monthly observation
- **THEN** the system SHALL persist that event as `released` with sourced actual, previous, unit, and period-label fields
- **AND** it SHALL not derive a release date from the observation period alone

#### Scenario: A historic schedule refresh supersedes malformed retained previews
- **WHEN** an official BLS calendar refresh supplies a coverage range containing past supported events
- **THEN** unmatched `scheduled` BLS previews in that covered range SHALL be removed
- **AND** released or revised records SHALL remain retained even if a later source refresh is incomplete

### Requirement: Read-Only Event Browse API
The system SHALL expose a read-only date-window event listing API and read-only event-detail API with validated inputs and provenance/freshness metadata.

#### Scenario: Client requests a valid event window
- **WHEN** a client requests `GET /api/market/us-events` with a supported bounded date window and supported filters
- **THEN** the API SHALL return events ordered by scheduled time
- **AND** each response SHALL include generation time, source/freshness metadata, and deduplicated warnings

#### Scenario: Client requests an invalid or excessive event window
- **WHEN** a client supplies malformed dates, unsupported filters, or a date range beyond the configured maximum
- **THEN** the API SHALL reject the request with a validation error
- **AND** it SHALL not perform an unbounded provider refresh or database query

#### Scenario: Client requests event detail
- **WHEN** a client requests `GET /api/market/us-events/{eventId}` for a known event
- **THEN** the API SHALL return the canonical record, its observed versions, and source provenance
- **AND** it SHALL not mutate the event or any trading/account state

### Requirement: Provider Failure and Retained-Data Behavior
The ingestion layer SHALL isolate provider failures and return clearly labeled retained data when it is available. A single browse refresh SHALL apply one bounded overall wait budget across independent provider reads so a stalled official source cannot block the timeline API behind a proxy timeout.

#### Scenario: Provider fails with retained event data
- **WHEN** an approved provider cannot refresh but previously persisted events exist
- **THEN** the listing API SHALL return the retained events
- **AND** it SHALL include a warning and age/freshness metadata for the affected provider

#### Scenario: Provider fails with no retained event data
- **WHEN** an approved provider cannot refresh and no persisted events exist
- **THEN** the listing API SHALL return a partial result for other providers if available
- **AND** it SHALL identify the missing provider instead of fabricating event records

#### Scenario: One provider stalls while the others respond
- **WHEN** an independent provider read exceeds the refresh wait budget
- **THEN** the API SHALL return the completed provider results and retained records without waiting for the stalled read indefinitely
- **AND** it SHALL label the stalled provider as retained or unavailable
