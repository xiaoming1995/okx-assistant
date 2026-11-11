## Why

The dashboard currently renders its user-visible interface through a large, page-local JSX and CSS surface. Although shared tokens and interaction rules exist, the navigation, filters, panels, tables, and feedback patterns still vary enough that the product reads as a collection of assembled screens rather than one trustworthy professional workspace.

The product needs one complete, themeable React component system so that future pages inherit the same visual density, state feedback, accessibility behavior, and responsive structure instead of recreating them with page-specific CSS.

## What Changes

- Introduce Mantine as the single general-purpose component and theming system for the frontend, installed and versioned through the existing package manager rather than loaded from a remote CDN.
- Define a Mantine application theme that encodes the documented simple-tool visual baseline: compact and standard control sizes, 4px-based spacing, 8px radii, restrained surfaces, semantic market/status colors, monospace numeric data, visible focus, and reduced-motion support.
- Replace the existing application shell, navigation, common actions, form controls, menus, panels, status labels, tables, dialogs, drawers, notifications, loading states, and empty/error/cache feedback with shared Mantine-based patterns across market, trading, automation, account, settings, announcements, and US-market-event pages.
- Rework the market workbench and contract rail to use the shared shell and compact data-list patterns while retaining the selected contract, filters, chart period, and current data-refresh behavior.
- Retire superseded page-local control and surface styles after all consuming screens use the shared component system. **BREAKING**: frontend markup and CSS class contracts are internal implementation details and will be replaced; externally visible routes, backend APIs, and product behavior remain unchanged.

## Capabilities

### New Capabilities

- `mantine-ui-foundation`: A centrally themed, accessible Mantine component foundation for all common frontend controls, feedback states, and data presentation patterns.
- `unified-frontend-workspaces`: A consistent application shell and responsive workspace layout for every user-visible dashboard route, including the dense market workbench.

### Modified Capabilities

- None.

## Impact

- Affected code: `frontend/package.json`, `frontend/package-lock.json`, `frontend/src/main.tsx`, `frontend/src/styles.css`, and newly extracted frontend theme/shared-component modules and focused frontend tests.
- New dependencies: Mantine Core, Hooks, Notifications, and only route-specific Mantine packages justified by existing behavior (for example, date controls); `lightweight-charts` and `lucide-react` remain the charting and icon integrations.
- Unchanged systems: frontend hash routes, backend APIs, market subscriptions, snapshot/cache ownership, manual read-only AI analysis behavior, and trading/automation safety boundaries.
- Validation must cover desktop and narrow breakpoints, keyboard focus, disabled controls, loading, refresh-with-retained-data, empty, cache, and error states for representative pages before retiring legacy styles.
