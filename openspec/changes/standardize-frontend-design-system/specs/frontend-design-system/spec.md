## ADDED Requirements

### Requirement: Shared frontend token foundation
The frontend SHALL expose globally reusable tokens for the documented spacing scale, compact/standard/control sizes, surface layers, semantic colors, focus treatment, motion, and stacking layers. User-visible frontend styles SHALL use those tokens for new shared layout and interaction decisions.

#### Scenario: A shared component needs spacing or an interaction transition
- **WHEN** a developer adds or modifies a shared user-visible frontend control or layout
- **THEN** the implementation uses the documented token scale and does not introduce arbitrary page-local visual values without a documented exception

#### Scenario: Legacy semantic variables are rendered in the timeline
- **WHEN** the US market timeline uses a semantic color or surface variable
- **THEN** that variable resolves to the canonical global token vocabulary

### Requirement: Simple and consistent shared controls
The frontend SHALL render common buttons, tabs, icon buttons, selectable rows, cards, popovers, and status labels with restrained surfaces, consistent dimensions, visible focus feedback, and non-layout-shifting interaction feedback.

#### Scenario: A keyboard user focuses a shared control
- **WHEN** focus reaches a button, input, select, textarea, or interactive shared control by keyboard
- **THEN** a visible focus indicator is rendered without relying on hover-only feedback

#### Scenario: A user points to or activates a selectable control
- **WHEN** the user hovers or presses a shared button, tab, instrument row, or selectable card
- **THEN** the state changes through a short, restrained visual transition without moving adjacent layout

### Requirement: Responsive workbench preservation
The frontend SHALL retain core page content, state, and actions at desktop and narrow breakpoints while using the design guide's standardized page and module spacing.

#### Scenario: A market workbench reaches the single-column breakpoint
- **WHEN** viewport width is at or below the existing market single-column breakpoint
- **THEN** the full contract rail remains available and selected-contract, filter, and tab context remain intact

#### Scenario: A narrow page displays controls and feedback
- **WHEN** a user views a frontend workspace at the narrow breakpoint
- **THEN** page actions, statuses, loading/empty/error feedback, and keyboard interaction remain visible and operable

### Requirement: Accessible and understandable feedback
The frontend SHALL present loading, refreshing, cached, empty, error, selected, and disabled states in Chinese with readable state cues beyond color alone. Motion used for feedback SHALL respect reduced-motion preferences.

#### Scenario: Data refreshes while a complete snapshot is visible
- **WHEN** a user-visible data region refreshes in the background
- **THEN** the complete visible snapshot remains readable and a concise Chinese refreshing or freshness cue is shown

#### Scenario: A user enables reduced motion
- **WHEN** the operating system requests reduced motion
- **THEN** non-essential loading and interaction animation is disabled or reduced without hiding state feedback
