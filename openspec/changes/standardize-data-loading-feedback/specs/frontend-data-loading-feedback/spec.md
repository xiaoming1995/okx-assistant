## ADDED Requirements

### Requirement: Initial data loading feedback

The frontend SHALL render a labelled, content-shaped loading state for a data region while its first request is in progress and no complete result is available.

#### Scenario: Shared market workspace starts
- **WHEN** the contract list, ticker snapshot, or selected K-line snapshot has not returned a complete result
- **THEN** the relevant rail, market summary, or chart region displays a labelled loading state
- **AND** the UI SHALL NOT present that pending state as an empty contract list or completed market value

#### Scenario: Account or list page starts
- **WHEN** a page-level list or account request is in progress with no prior result
- **THEN** its primary data region displays a loading state distinct from its completed empty state

### Requirement: Non-blocking refresh feedback

The frontend SHALL preserve the last complete data result during a subsequent refresh and expose a concise refresh state.

#### Scenario: Statistics refreshes
- **WHEN** a selected contract's trading statistics refresh after a complete result exists
- **THEN** the previous metric values remain visible while the request is in progress
- **AND** the statistics status identifies that an update is in progress

#### Scenario: Cached list refreshes
- **WHEN** a data list refreshes after complete rows are visible
- **THEN** the visible rows remain available
- **AND** the page exposes a non-blocking Chinese refresh status

### Requirement: Loading controls and accessibility

The frontend SHALL prevent an action that requires unfinished prerequisite data and provide accessible request feedback.

#### Scenario: AI analysis waits for a chart snapshot
- **WHEN** the AI-outlook page has not received a usable chart snapshot
- **THEN** the analysis action is disabled with text explaining that the chart is preparing
- **AND** it becomes enabled once the snapshot is usable

#### Scenario: Loading status is announced
- **WHEN** a user-visible data request begins or changes between initial loading and refresh
- **THEN** the relevant status text is exposed through a polite status announcement
- **AND** decorative loading shapes are excluded from repeated announcement
