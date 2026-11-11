## ADDED Requirements

### Requirement: Complete ticker snapshots survive transient bulk-refresh failure
The system SHALL retain and return the last validated complete bulk ticker snapshot when an OKX bulk ticker refresh ends with a transient transport failure, including an incomplete response.  The system MUST NOT merge or expose an incomplete response body as current ticker data.

#### Scenario: Refresh fails after a complete snapshot exists
- **WHEN** the bulk ticker refresh exhausts its request attempts with an incomplete response and a validated snapshot exists
- **THEN** `/api/tickers` returns the complete snapshot with a stale or backing-off refresh state instead of a page-level upstream exception

#### Scenario: First ticker load fails without a complete snapshot
- **WHEN** the bulk ticker refresh fails and neither memory nor persisted storage contains a validated snapshot
- **THEN** `/api/tickers` returns an explicit unavailable refresh state with no ticker rows

### Requirement: Bulk ticker recovery is bounded across consumers
The system SHALL schedule retry of a failed bulk ticker refresh with capped backoff shared by all `/api/tickers` consumers.  It MUST permit only one in-flight bulk refresh and MUST return an available complete snapshot without synchronously retrying while the next retry deadline has not elapsed.

#### Scenario: Repeated page polling during backoff
- **WHEN** multiple consumers request tickers while a previous bulk refresh has failed and the retry deadline has not elapsed
- **THEN** each response returns the retained complete snapshot and no additional bulk refresh is started

#### Scenario: Retry deadline is reached
- **WHEN** a retained ticker snapshot is stale and the shared retry deadline has elapsed
- **THEN** one background bulk refresh starts while consumers continue to receive the retained snapshot

### Requirement: Ticker freshness is understandable without raw transport errors
The system SHALL expose structured refresh metadata containing a state, snapshot timestamp or age, and next retry time when relevant.  The shared market workspace MUST render this metadata as a concise Chinese freshness status and MUST NOT show raw `IncompleteRead` or other upstream transport exception text to users when a complete snapshot is available.

#### Scenario: Stale snapshot with live selected-contract price
- **WHEN** the ticker list is retained from a complete snapshot and the selected contract is receiving WebSocket price events
- **THEN** the UI identifies the list as a prior complete snapshot and separately preserves the live price status without a raw transport-error banner

#### Scenario: No complete ticker snapshot is available
- **WHEN** the ticker refresh state is unavailable and no ticker rows are returned
- **THEN** the UI displays a prominent concise Chinese unavailable message and does not claim the data are current
