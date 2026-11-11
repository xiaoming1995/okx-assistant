## 1. Baseline and dependency setup

- [x] 1.1 Inventory every user-visible route, existing shared control, data-state pattern, and responsive behavior; record the target Mantine replacement and preserve its current route/API/state owner.
- [x] 1.2 Add the approved Mantine Core, Hooks, and Notifications dependencies and bundled styles through the frontend package manifest; add a route-specific Mantine package only when it replaces an already-existing behavior.
- [x] 1.3 Add focused dependency and static-regression coverage that rejects a general-purpose UI CDN or a second general-purpose UI library.

## 2. Mantine theme and shared UI foundation

- [x] 2.1 Create the root Mantine provider and application theme with the documented spacing, radii, control density, typography, numeric font, surfaces, semantic colors, focus treatment, and reduced-motion rules.
- [x] 2.2 Configure shared Mantine defaults and variants for buttons, icon buttons, inputs, selects, tabs, badges, alerts, papers, menus, popovers, modals, drawers, skeletons, tables, and notifications without importing a generic-template visual language.
- [x] 2.3 Extract shared page-header, toolbar, status, data-table, row-selection, loading, refresh, cache, empty, error, disabled, and confirmation patterns backed by Mantine components.
- [x] 2.4 Add focused tests for the application theme, compact controls, semantic state cues, keyboard focus, reduced motion, retained-data refresh, and dense row selection contracts.

## 3. Application shell and navigation migration

- [x] 3.1 Replace the existing top-level application shell with a Mantine AppShell that preserves all current primary and route-context hash destinations.
- [x] 3.2 Migrate primary navigation, market secondary navigation, active-route state, compact actions, and page-status placement to shared Mantine navigation patterns.
- [x] 3.3 Implement the shared desktop, intermediate, and narrow-width shell layouts so page actions, statuses, and route context remain visible and operable.
- [x] 3.4 Verify keyboard navigation, focus visibility, disabled navigation states where applicable, and narrow shell behavior in a running browser.

## 4. Market workspace migration

- [x] 4.1 Migrate the contract rail search, range switch, filters, sorting, watchlist controls, compact contract rows, and refresh feedback to the shared Mantine patterns.
- [x] 4.2 Migrate market chart headers, period controls, ticker/summary panels, chart inspector, trading-statistics surfaces, and AI-outlook entry actions without replacing the chart integration or changing state ownership.
- [x] 4.3 Migrate AI-outlook report, radar, announcement, and US-market-event controls, data surfaces, loading, cached, empty, and error feedback to the shared patterns.
- [x] 4.4 Verify the market workbench at desktop and narrow widths, including rail context preservation, retained refresh, chart-period selection, keyboard focus, disabled actions, cache, empty, and error states.

## 5. Trading, automation, and account migrations

- [x] 5.1 Migrate manual-trading forms, order lists, fills, position views, and their confirmation, validation, empty, disabled, and error presentations to the shared Mantine patterns without changing order behavior or safety boundaries.
- [x] 5.2 Migrate automation overview, strategy, signal, log, and detail views to the common page, toolbar, table, status, dialog, and feedback patterns without changing automation permissions or actions.
- [x] 5.3 Migrate account overview, balances, positions, Earn, PnL summaries, LLM usage, and configuration screens to the common component system while preserving existing cache and unavailable-data semantics.
- [x] 5.4 Verify representative trading, automation, and account flows in a running browser at desktop and narrow widths, including keyboard focus, disabled controls, retained refresh, cache, empty, and error behavior.

## 6. Information and settings migrations

- [x] 6.1 Migrate announcement, US-market-event, settings, and other remaining information/configuration routes to the shared Mantine page, table, filter, date-control, feedback, and overlay patterns.
- [x] 6.2 Verify every user-visible hash route consumes the shared application shell and does not present a legacy bespoke equivalent of a common control or feedback surface.

## 7. Legacy retirement and release verification

- [x] 7.1 Remove obsolete route-local UI markup, component styles, and selector families after confirming every consumer uses the new shared Mantine pattern; retain only chart integration and documented exceptional-layout styles.
- [x] 7.2 Run the full frontend test suite, production build, focused regression checks, and strict OpenSpec validation; resolve migration-introduced failures.
- [x] 7.3 Perform final browser acceptance across representative market, trading, automation, account, information, and settings routes at desktop and narrow breakpoints, including loading, refresh, cache, empty, error, focus, selected, and disabled states.
