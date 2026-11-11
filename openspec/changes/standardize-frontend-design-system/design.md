## Context

`frontend/src/main.tsx` and `frontend/src/styles.css` contain the user-visible application. The stylesheet already provides a color palette, radii, shadows, control heights, a global focus ring, and desktop/narrow responsive layouts, but these are incomplete as a system: spacing values are page-local, AI reporting has its own spacing tokens, the US market timeline still uses undefined legacy variables, and interaction motion is limited to one feature.

The repository's frontend design guide defines a simple, tool-oriented style. The implementation must preserve market, account, manual-trading, and automation behavior, preserve the shared market workbench's selected contract and rail context, and avoid a wholesale component rewrite.

## Goals / Non-Goals

**Goals:**

- Turn the documented spacing, sizing, surface, semantic-color, motion, and layer rules into globally reusable CSS tokens.
- Make shared controls and feedback states consistently accessible and visually restrained.
- Correct known noncompliant stylesheet patterns while keeping all routes and business behavior stable.
- Add static regression coverage for the design-system contract and run the existing frontend validation suite.

**Non-Goals:**

- Redesigning information architecture, changing backend APIs, changing trading permissions or order behavior, or introducing a component library.
- Rewriting every page or replacing all existing selectors in one pass.
- Removing existing product-specific content, charts, or safety notices solely for visual uniformity.

## Decisions

### 1. Extend the existing global CSS root instead of introducing a dependency

The project has one stylesheet and no current component-library dependency. Add semantic tokens for the 4px spacing scale, standard sizes, restrained transitions, and layer levels alongside the existing palette. Existing color/radius tokens remain the canonical values; aliases are added only where they make legacy cleanup safe.

**Alternative considered:** Adopt a third-party design system. This would create unnecessary dependency, markup, and visual migration work for a local workbench.

### 2. Preserve density through named compact and standard values

The contract rail, tables, and transaction form need compact controls, while reports and summaries need more breathing room. Global token values will support both instead of applying one larger spacing value everywhere.

**Alternative considered:** Normalize every current spacing value mechanically. This would risk clipping dense market controls and change useful layout behavior without a user-facing benefit.

### 3. Apply simple interaction rules at shared selector boundaries

Shared buttons, tabs, instrument rows, selectable cards, and popovers receive short, non-layout-shifting transitions and a visible `:active` state. Existing reduced-motion behavior expands to the shared motion contract. Local feature animation remains limited to loading feedback.

**Alternative considered:** Add route transitions or animated cards. These would conflict with the guide's low-noise requirement and add instability to data-dense screens.

### 4. Correct the timeline through compatibility aliases and local token usage

The US market timeline uses legacy `--text`, `--muted`, `--panel`, `--soft`, `--border`, and semantic variables that are not defined in the root. Define compatibility aliases to the canonical tokens, then update the timeline's local values to use the same semantic vocabulary. This is safer than a large timeline markup rewrite.

### 5. Make state patterns explicit without changing data flows

Use existing Chinese fallback/cached-data wording and status-pill patterns. Add only CSS and small accessibility attributes where an interaction control is already present; do not alter refresh, route, market-subscription, or order-execution code.

## Risks / Trade-offs

- [Global selector changes can affect dense pages unexpectedly] → Limit shared changes to base classes already used across pages; validate static tests, build, and representative routes at desktop and narrow widths.
- [A token migration may leave legacy literals behind] → Audit approved value families with targeted searches and add static regression assertions for the important contract.
- [Uniform motion can conflict with accessibility or perceived performance] → Keep transition duration short, avoid layout motion, and honor `prefers-reduced-motion`.
- [Existing functional OpenSpec changes remain in progress] → Do not change their task files; retain market rail ownership, selected-contract behavior, and current breakpoints.

## Migration Plan

1. Add global tokens and shared interaction/focus foundations.
2. Normalize representative shared surfaces, controls, feedback, and responsive page padding.
3. Repair timeline compatibility and tighten focused markup accessibility where needed.
4. Add static checks, run frontend tests and production build, then inspect representative routes when runtime services are available.

Rollback is a source-only revert of this change's frontend and OpenSpec files; no data migration or API rollback is required.

## Open Questions

- None. The documented guide supplies the visual decisions; implementation will retain route-specific density where the guide explicitly permits it.
