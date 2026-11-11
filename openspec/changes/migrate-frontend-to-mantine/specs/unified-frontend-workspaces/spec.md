## ADDED Requirements

### Requirement: All dashboard routes use one application shell
The frontend SHALL render market, trading, automation, account, settings, announcements, and US-market-event routes within one Mantine-based application shell. The shell SHALL provide consistent product identification, primary navigation, route context, page action placement, page-status placement, and responsive behavior without changing existing route destinations.

#### Scenario: A user changes primary navigation sections
- **WHEN** a user navigates between a primary dashboard section and one of its route-context destinations
- **THEN** the destination route remains unchanged while the active navigation and page context are presented through the shared shell patterns

#### Scenario: A page has an available primary action
- **WHEN** a route exposes an action that advances its current task
- **THEN** the shared page header renders at most one visually primary action and renders supporting actions with the documented secondary treatment

### Requirement: Responsive workspaces preserve content and context
The frontend SHALL use shared Mantine responsive layout patterns at desktop, intermediate, and narrow widths. It SHALL retain core information, state, and actions without relying on a fixed viewport height; dense tables may scroll horizontally when necessary.

#### Scenario: A narrow viewport displays a dashboard route
- **WHEN** the viewport width is at or below 767px
- **THEN** page headers stack predictably, core actions and status remain available, compact controls remain operable, and primary content follows natural document flow

#### Scenario: A market workspace reaches a narrow layout
- **WHEN** the market workbench changes from desktop to its narrow layout
- **THEN** the contract rail remains accessible and preserves the selected contract, watchlist, filters, sorting, and chart-period context

### Requirement: Domain migrations retain product behavior and safety boundaries
The frontend SHALL replace domain presentation without changing API contracts, data ownership, subscriptions, cache behavior, hash routes, trading permissions, automation permissions, or manual read-only AI-analysis behavior. Chart rendering SHALL remain on the existing chart integration and icon rendering SHALL remain on the existing icon integration unless a separately approved change modifies either boundary.

#### Scenario: A migrated market or account screen receives data-state changes
- **WHEN** its existing data owner reports loading, refreshing, cache, error, or unavailable state
- **THEN** the Mantine-based presentation reflects that state while preserving the pre-existing data and recovery behavior

#### Scenario: A user opens a migrated AI or trading screen
- **WHEN** the user selects a contract, changes a chart period, or enters a migrated trading workspace
- **THEN** the migration does not create an AI request, order, leverage change, position change, or automated action that was not available before the migration
