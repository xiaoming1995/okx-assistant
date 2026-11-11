## ADDED Requirements

### Requirement: Default market list prioritizes common tradable contracts
The system SHALL default the market instrument list to a common tradable view that prioritizes USDT-settled live swap contracts without deleting or disabling other contract types.

#### Scenario: User opens the market chart tab
- **WHEN** the market chart page first renders
- **THEN** the instrument list defaults to the USDT-settled filter
- **AND** the user can switch to all instruments or coin-settled instruments

### Requirement: Search filters loaded instruments predictably
The system SHALL filter the already loaded market instrument set in response to search input so typing a query does not require a new instrument-list request for every keystroke.

#### Scenario: User types a symbol query
- **WHEN** the user types `BTC` into the market instrument search field
- **THEN** the visible instrument rows update from the current loaded instrument set
- **AND** the manual refresh control remains available for explicitly reloading instrument metadata

### Requirement: Similar symbols are clearly distinguished
The system SHALL display enough contract metadata for users to distinguish instruments with the same base symbol but different settlement or contract-value semantics.

#### Scenario: Search returns USDT-settled and coin-settled BTC swaps
- **WHEN** search results include both `BTC-USDT-SWAP` and `BTC-USD-SWAP`
- **THEN** each result shows a human-readable settlement type
- **AND** each result exposes contract-value context
- **AND** neither valid contract is hidden solely because another result shares the same base symbol

### Requirement: Instrument ordering follows selection intent
The system SHALL order market instrument rows by selection relevance before falling back to lexical order.

#### Scenario: Default sorted results are shown
- **WHEN** the market list uses default sorting
- **THEN** the selected instrument appears first when present
- **AND** watched instruments are prioritized
- **AND** USDT-settled live contracts are prioritized ahead of less common alternatives

### Requirement: Contract metadata is consistent across entry points
The system SHALL use consistent user-facing contract metadata semantics across the market list, manual trading picker, and automation picker.

#### Scenario: Same contract appears in multiple pickers
- **WHEN** a contract appears in the market list and in a trade or automation contract picker
- **THEN** the displayed settlement type and contract-value meaning are consistent across those entry points
