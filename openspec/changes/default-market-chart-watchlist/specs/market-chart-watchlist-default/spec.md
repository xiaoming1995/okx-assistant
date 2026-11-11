## ADDED Requirements

### Requirement: Chart Page Defaults to Self-Selected Contracts
The market-chart page SHALL initialize its left contract rail with the existing `自选` filter. The filter SHALL use the persistent watched status returned for instruments, and it SHALL not change the initial filter of AI outlook or trading-data pages.

#### Scenario: User has self-selected contracts
- **WHEN** the user opens the market-chart page and one or more instruments have watched status
- **THEN** the left rail displays only those self-selected contracts by default
- **AND** the `自选` filter is visibly active
- **AND** the user can still choose the existing other filters

#### Scenario: User opens adjacent market pages
- **WHEN** the user opens the AI outlook page or trading-data page
- **THEN** those pages retain their existing initial filter behavior
- **AND** the market-chart default does not leak through the shared rail component

### Requirement: Recoverable Empty Self-Selected State
The market-chart rail SHALL render a clear empty state when the active `自选` filter has no matching contracts after instrument loading. It SHALL provide a `查看全部合约` action that changes only the chart page's local filter to `全部`.

#### Scenario: User has no self-selected contracts
- **WHEN** instrument loading finishes while the active chart filter is `自选` and no instrument is watched
- **THEN** the rail states that there are no self-selected contracts
- **AND** it offers `查看全部合约`

#### Scenario: User recovers from empty self-selected state
- **WHEN** the user activates `查看全部合约`
- **THEN** the rail displays all available contracts
- **AND** the action does not add, remove, or otherwise change any watchlist item

### Requirement: Current Chart Selection Is Independent of Self-Selected Filtering
The market-chart page SHALL preserve its selected contract when the active self-selected filter does not include that contract. It MUST NOT automatically add the selected contract to the watchlist, select the first watched contract, or rewrite a direct chart route solely because the rail filter is `自选`.

#### Scenario: Direct link targets a non-self-selected contract
- **WHEN** a user opens the chart through a route targeting a contract that is not watched
- **THEN** the right-side chart continues to show that targeted contract
- **AND** the left rail remains filtered to self-selected contracts
- **AND** no watchlist mutation occurs

#### Scenario: User removes the active contract from self-selected contracts
- **WHEN** the user removes the currently selected contract's star while the chart filter is `自选`
- **THEN** the selected chart remains visible
- **AND** the rail refreshes to the remaining self-selected contracts or the empty self-selected state
