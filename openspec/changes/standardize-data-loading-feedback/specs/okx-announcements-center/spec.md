## MODIFIED Requirements

### Requirement: Announcement Page UI

The system SHALL provide a market-section announcement page for browsing official OKX notices and SHALL distinguish initial loading, retained-row refresh, and completed empty states.

#### Scenario: Market announcement tab

- **WHEN** the user opens the market section
- **THEN** the secondary navigation includes a `公告` tab
- **AND** selecting it renders the announcement page

#### Scenario: Display announcement rows

- **WHEN** announcements are loaded
- **THEN** the page displays each announcement title, type label, display publish time, first publish time, and an OKX source link

#### Scenario: Initial announcement loading

- **WHEN** announcement rows or type labels are requested for the first time
- **THEN** the affected list displays a labelled loading state
- **AND** it SHALL NOT present the pending result as a completed empty list

#### Scenario: Announcement refresh feedback

- **WHEN** announcement rows are refreshed after a page has been loaded
- **THEN** the existing rows remain visible
- **AND** the page displays a concise Chinese updating status

#### Scenario: Cache warning display

- **WHEN** the backend returns stale-cache or unavailable metadata
- **THEN** the page displays a visible warning without hiding the cached announcement rows
