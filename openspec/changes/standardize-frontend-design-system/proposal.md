## Why

The frontend has a sound visual base but accumulated page-local spacing, color, elevation, and interaction decisions. This makes the local trading workbench feel less coherent and raises the cost and risk of future UI changes.

## What Changes

- Establish one token-based implementation of the repository's simple, tool-oriented frontend design standard.
- Normalize shared page layout, card, button, control, status, table, and feedback patterns without changing market, account, trading, or automation business behavior.
- Remove legacy and page-local visual values that conflict with the documented standard, including undefined legacy color variables in the US market timeline.
- Add targeted static regression coverage for the shared design tokens, accessibility interaction hooks, and responsive layout contracts.

## Capabilities

### New Capabilities

- `frontend-design-system`: A consistent, accessible, responsive visual and interaction foundation for all user-visible frontend workspaces.

### Modified Capabilities

- None.

## Impact

- Affected code: `frontend/src/styles.css`, user-visible markup and focused frontend static tests in `frontend/src/`.
- Affected documentation: `docs/frontend-design-guidelines.md` remains the governing design baseline.
- No backend API, data model, trading behavior, route, or dependency changes are required.
