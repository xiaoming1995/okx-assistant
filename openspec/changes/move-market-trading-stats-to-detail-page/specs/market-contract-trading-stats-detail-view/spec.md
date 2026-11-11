## ADDED Requirements

### Requirement: Market Chart Stats Summary Entry
The system SHALL keep the market chart page focused by showing selected-contract trading statistics as a compact summary with an entry to full details.

#### Scenario: Chart page shows compact trading summary
- **WHEN** the user opens the market chart page for a selected SWAP contract
- **THEN** the page displays a compact trading-structure summary near the selected contract and K-line context
- **AND** the page does not require the full trading-statistics trend panels to fit below the K-line.

#### Scenario: Navigate from chart summary to full stats
- **WHEN** the user activates the trading data entry from the chart summary
- **THEN** the system opens the full contract trading data view for the currently selected contract
- **AND** the selected contract identity is preserved in the destination view.

### Requirement: Dedicated Contract Trading Data View
The system SHALL provide a dedicated page for complete selected-contract trading statistics.

#### Scenario: Load full trading data for selected contract
- **WHEN** the user opens the contract trading data view with an `inst` route parameter
- **THEN** the system loads trading statistics for that SWAP contract using the existing normalized market stats API
- **AND** the page displays current summary metrics plus detailed long/short ratio, taker buy/sell, and open interest trend sections.

#### Scenario: Change contract in trading data view
- **WHEN** the user selects a different live SWAP contract from the trading data view
- **THEN** the system reloads statistics for the newly selected contract
- **AND** stale data from the previous contract is not presented as current.

#### Scenario: Preserve observational language
- **WHEN** the trading data view displays long/short account ratio, active buy/sell balance, or open interest changes
- **THEN** the copy remains observational
- **AND** the page does not phrase those values as direct instructions to buy, sell, long, or short.

### Requirement: Trading Data Layout Completeness
The system SHALL avoid clipping full trading-statistics content on common desktop and mobile viewport sizes.

#### Scenario: Desktop viewport can access complete content
- **WHEN** the full trading data page is viewed on a common desktop viewport
- **THEN** all summary and detail sections are reachable without being hidden by a non-scrollable parent container.

#### Scenario: Chart viewport remains focused
- **WHEN** the market chart page is viewed on a common desktop viewport
- **THEN** the chart remains visible with the compact trading summary
- **AND** moved detailed statistics no longer force the chart page to clip lower content.
