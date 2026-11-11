## Context

The frontend currently keeps page selection in React state and renders a large top navigation with individual entries for market, radar, trade, automation, strategies, signals, positions, LLM config, AI usage, and account. This exposes implementation-level pages as primary destinations and makes the header dense.

The app has clearer product areas now: market selection, trading, automation, account state, and settings. Navigation should reflect those user workflows rather than internal page components.

## Goals / Non-Goals

**Goals:**

- Reduce the top navigation to five primary sections: Market, Trade, Automation, Account, and Settings.
- Move secondary destinations into their parent section as tabs or contextual controls.
- Keep Contract Radar as the default Market view because it helps users choose a contract before opening a chart.
- Preserve current page components and API behavior where possible.
- Preserve selected-contract handoff from radar to market, trade, and automation.
- Keep the UI compact and readable on desktop and mobile.

**Non-Goals:**

- Do not add a new routing library.
- Do not change backend APIs.
- Do not remove existing functionality.
- Do not redesign the individual page contents beyond the navigation shell needed to group them.
- Do not archive completed OpenSpec changes as part of this change.

## Decisions

### Decision: Use primary sections plus secondary tabs

Represent the UI as five top-level sections and render secondary tabs within Market, Automation, Account, and Settings.

Target grouping:

- Market: Contract Radar, Market Chart.
- Trade: Manual Trade.
- Automation: Overview, Strategies, Signals.
- Account: Positions, Account.
- Settings: AI Config, AI Usage.

Rationale: this matches the user's mental model and cuts primary navigation from ten entries to five without hiding features.

Alternative considered: put all secondary destinations in a dropdown menu from the header. This keeps the header compact, but makes common flows less visible and harder to scan.

### Decision: Keep existing page components

Reuse existing page components and wrap them in section-level containers rather than merging component internals immediately.

Rationale: this keeps implementation scope small and reduces regression risk. The main change is information architecture, not page behavior.

Alternative considered: physically merge page components into larger components. That could reduce duplicated state later, but it is a larger refactor and not necessary for the first navigation cleanup.

### Decision: Keep page state local to App

Continue using React state in `App` for navigation, but move from flat page entries to a primary section plus secondary page state.

Rationale: the project already uses local state, and this change does not require URL routing.

Alternative considered: introduce React Router or URL query state. That would improve deep linking but adds dependency and scope.

### Decision: Make Radar the Market default

When users open Market, show Contract Radar first and expose Market Chart as a secondary tab.

Rationale: the product flow starts with selecting a contract. A radar-first market section supports discovery before chart inspection.

Alternative considered: keep Market Chart as the default and expose Radar as a secondary tab. This preserves old behavior but weakens the new selection workflow.

## Risks / Trade-offs

- [Risk] Users may miss pages that moved out of the top nav. -> Mitigation: use visible secondary tabs with clear labels in each section.
- [Risk] Existing tests may look for old top-level labels. -> Mitigation: update smoke tests to assert the new top-level labels and secondary access.
- [Risk] Selected signal detail needs a place after Signal Logs moves under Automation. -> Mitigation: keep Signal Detail within the Automation section and preserve back navigation to Signals.
- [Risk] AI Usage may feel hidden under Settings. -> Mitigation: use Settings tabs with both AI Config and AI Usage visible.
- [Risk] Mobile header can still overflow if labels are too long. -> Mitigation: keep five short labels and let secondary tabs wrap or scroll within the content area.

## Migration Plan

1. Introduce primary section and secondary tab state in the frontend.
2. Replace top navigation buttons with the five primary sections.
3. Add secondary tab controls inside Market, Automation, Account, and Settings.
4. Wire existing page components into their new section containers.
5. Update frontend smoke tests and production build validation.

Rollback can restore the previous flat `Page` union and header button list because this change is frontend-only.
