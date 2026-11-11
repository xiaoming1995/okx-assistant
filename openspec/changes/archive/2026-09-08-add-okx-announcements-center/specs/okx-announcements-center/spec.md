## ADDED Requirements

### Requirement: Announcement Types

The system SHALL expose official OKX announcement types through a read-only backend API without requiring OKX account credentials.

#### Scenario: Load announcement types

- **WHEN** the frontend requests announcement types
- **THEN** the backend returns a list of type identifiers and display labels from OKX
- **AND** the request to OKX does not include private API authentication headers

#### Scenario: Type endpoint rate limit fallback

- **WHEN** OKX rejects a type refresh because the request frequency is too high
- **THEN** the backend returns the latest cached type list when available
- **AND** the response includes stale-cache source metadata and a warning

### Requirement: Announcement List

The system SHALL expose a paged official OKX announcement list with optional type filtering.

#### Scenario: Load filtered announcements

- **WHEN** the frontend requests page 1 for an OKX announcement type
- **THEN** the backend requests `GET /api/v5/support/announcements` with that `annType` and `page`
- **AND** the response includes normalized announcement title, type, URL, first publish time, display publish time, total pages, source, timestamp, and cache age

#### Scenario: Load all announcements

- **WHEN** the frontend requests announcements without an `annType`
- **THEN** the backend returns announcements across all available types

#### Scenario: Announcement refresh fallback

- **WHEN** OKX announcement refresh fails after a matching page was previously loaded
- **THEN** the backend returns the matching cached announcement page
- **AND** the response includes a warning describing the refresh failure

### Requirement: Announcement Language

The system SHALL request Chinese OKX announcements by default.

#### Scenario: Chinese default

- **WHEN** the backend requests announcement types or announcements from OKX
- **THEN** the OKX request includes `Accept-Language: zh-CN` unless another supported language is explicitly requested

### Requirement: Announcement Page UI

The system SHALL provide a market-section announcement page for browsing official OKX notices.

#### Scenario: Market announcement tab

- **WHEN** the user opens the market section
- **THEN** the secondary navigation includes a `公告` tab
- **AND** selecting it renders the announcement page

#### Scenario: Display announcement rows

- **WHEN** announcements are loaded
- **THEN** the page displays each announcement title, type label, display publish time, first publish time, and an OKX source link

#### Scenario: Cache warning display

- **WHEN** the backend returns stale-cache or unavailable metadata
- **THEN** the page displays a visible warning without hiding the cached announcement rows
