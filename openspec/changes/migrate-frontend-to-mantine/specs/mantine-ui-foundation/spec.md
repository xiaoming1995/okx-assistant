## ADDED Requirements

### Requirement: Mantine is the single user-interface foundation
The frontend SHALL install Mantine through its versioned package manifest and SHALL render every common user-visible control, feedback surface, overlay, and layout primitive through Mantine-based shared patterns. The frontend SHALL NOT load a general-purpose UI component system from an external runtime CDN or introduce a second general-purpose UI library.

#### Scenario: A frontend route renders a common control
- **WHEN** a user-visible route renders a button, input, select, tab, menu, popover, dialog, drawer, panel, table, badge, alert, loading indicator, or notification
- **THEN** it uses the shared Mantine-based pattern for that control instead of route-local bespoke markup and styling

#### Scenario: The frontend is built for deployment
- **WHEN** the production frontend build is created
- **THEN** the Mantine assets are resolved from the versioned application dependency graph and no UI component asset is requested from a third-party runtime CDN

### Requirement: The application theme expresses the simple-tool visual contract
The frontend SHALL mount one Mantine provider with a single application theme that implements the documented 4px spacing scale, 8px default radius, restrained surfaces, compact and standard control density, readable typography, monospace numeric data, visible keyboard focus, semantic status colors, and reduced-motion behavior. Product primary action styling SHALL remain distinct from green, red, amber, and neutral market/status semantics.

#### Scenario: A shared component uses a size or visual variant
- **WHEN** a shared Mantine-based component is rendered with a documented size or variant
- **THEN** its spacing, height, radius, focus treatment, motion, and semantic color resolve through the application theme rather than route-specific arbitrary values

#### Scenario: A keyboard or reduced-motion user opens the application
- **WHEN** a user navigates shared controls by keyboard or requests reduced motion in the operating system
- **THEN** focus remains visibly indicated and non-essential interaction or loading motion is reduced without hiding the control or status meaning

### Requirement: Shared feedback and data presentation remain understandable
The frontend SHALL render loading, refreshing, cached, empty, error, selected, and disabled states through shared Mantine-based patterns with Chinese text and state cues beyond color alone. Data-dense rows and tables SHALL use aligned columns, separators, and restrained selection/hover treatment rather than rendering every row as an independent elevated card.

#### Scenario: A complete snapshot refreshes in the background
- **WHEN** a user-visible data area refreshes while it already has complete data
- **THEN** the existing data remains visible and the shared feedback pattern communicates a concise Chinese refreshing or freshness state

#### Scenario: A dense data list renders a selected row
- **WHEN** a user selects a contract, position, order, signal, or other row in a dense list
- **THEN** the shared data pattern exposes selection through readable text or semantics plus restrained background, border, or leading-marker treatment without relying on color alone
