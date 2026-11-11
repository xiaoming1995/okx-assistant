## Context

The frontend is a Vite and React 19 single-page application whose visible UI is concentrated in `frontend/src/main.tsx` and `frontend/src/styles.css`. The existing stylesheet exposes a documented simple-tool token baseline, but route-local markup and CSS still independently define navigation, filters, panels, data rows, controls, overlays, and feedback. This makes a consistent product experience difficult to enforce and expensive to extend.

The dashboard is a data-dense operational tool. It must preserve the current hash routes, API contracts, selected-market context, cache and refresh behavior, manual read-only AI-analysis boundary, and trading or automation safety behavior. The repository design guide remains authoritative: it requires restrained surfaces, compact controls, readable status cues beyond color, Chinese feedback, desktop and narrow layouts, keyboard focus, and reduced-motion support.

## Goals / Non-Goals

**Goals:**

- Make Mantine the single UI component and theme authority for all user-visible frontend controls and layout primitives.
- Encode the repository's existing simple-tool visual decisions in one Mantine theme and reusable frontend patterns.
- Migrate every route to a common application shell and shared component vocabulary without changing user-facing business behavior.
- Preserve compact market and transaction density while improving hierarchy, scanning, keyboard interaction, responsive behavior, and state feedback consistency.
- Remove legacy page-local presentation code only after its replacement renders and is verified.

**Non-Goals:**

- Replacing `lightweight-charts`, `lucide-react`, backend APIs, hash routing, market subscriptions, or data/cache ownership.
- Adding order-placement capabilities, automatic AI analysis, automated financial actions, or changing trading and automation permissions.
- Adopting an external component CDN, a second general-purpose UI library, Tailwind, or a generic dashboard template.
- Redesigning product information architecture merely to match a library's default examples.

## Decisions

### 1. Adopt Mantine as the one complete frontend UI system

Install Mantine Core, Hooks, and Notifications through `frontend/package.json` and lock the resulting dependency graph in `package-lock.json`. Add only route-specific Mantine packages that replace an existing behavior; date controls are an example, while charts and icons remain on their current integrations. Import library CSS through the application bundle, never by external runtime URL.

Mantine provides a complete Vite-compatible component set, theme provider, responsive primitives, focus behavior, overlays, loading feedback, and data-presentation building blocks. A complete system is needed because the goal is whole-site convergence, not a collection of bespoke primitives.

**Alternatives considered:** Ant Design is comprehensive but its enterprise-admin defaults would need extensive suppression to avoid replacing one generic visual identity with another. Material UI would bring an equally strong Material visual language that is a poor default for a compact financial workspace. Radix/shadcn would preserve greater low-level visual control but would still require maintaining a bespoke component layer and does not meet the requested single full-system migration.

### 2. Encode the existing design guide in a single Mantine theme

Create an application theme module and mount one `MantineProvider` at the frontend root. It SHALL define the documented spacing scale, 8px radius, compact/standard/primary control heights, low-elevation surface treatment, typography hierarchy, monospace numeric style, breakpoints, visible keyboard focus, and reduced-motion behavior. The theme SHALL distinguish product primary actions from semantic market or status colors; green and red SHALL not become generic primary-button colors.

Component defaults and variants will encode the visual contract for `Button`, `ActionIcon`, `TextInput`, `Select`, `Tabs`, `Badge`, `Alert`, `Paper`, `Table`, `Menu`, `Popover`, `Modal`, `Drawer`, `Skeleton`, and notifications. This prevents each route from recreating a near-but-not-identical component rule.

**Alternative considered:** Keep the CSS token layer and style Mantine ad hoc per page. That would preserve the present fragmentation and produce a prolonged mixed system.

### 3. Migrate through shared shell and domain patterns, with one final visual system

Build a Mantine application shell, page header, status area, dense toolbar, data-table wrapper, empty/error/cache feedback, and confirmation/overlay patterns before migrating routes. Use `AppShell`, `NavLink`, and context-level tabs for navigation rather than retaining multiple unrelated rounded navigation bars. Use `Paper` only for meaningful surfaces; dense table and contract rows use separators, aligned columns, selection treatment, and restrained hover states instead of becoming a stack of cards.

Migration will be delivered in small verifiable domain batches, but the target state permits no user-visible mix of legacy bespoke controls and Mantine equivalents within a screen. A shared pattern is completed and validated before a domain starts consuming it. Legacy CSS is deleted only once every consumer is migrated.

**Alternative considered:** Rewrite the entire `main.tsx` and stylesheet in one change. That would make review, state-regression diagnosis, and rollback unnecessarily risky for data and trade-adjacent pages.

### 4. Preserve behavioral ownership while replacing presentation

Existing route, selection, filter, subscription, refresh, cache, and disabled-state ownership stays with the current domain components. Mantine components receive that state and expose it through their supported controlled APIs. The market workbench retains the shared contract rail's selected instrument, filters, sorting, watchlist, and chart-period state; narrow layouts make the rail accessible through the standardized responsive pattern rather than discarding context.

Complete visible snapshots remain on screen during background refresh, with concise Chinese feedback. Empty, cached, error, disabled, keyboard-focus, and loading states are visually and semantically represented through the shared patterns.

**Alternative considered:** Let component defaults dictate refresh and empty states. This would regress the existing retained-data resilience contract.

### 5. Verify visual consistency as a runtime requirement

Maintain focused static regression coverage for theme contracts and route behaviors, then validate representative routes in a running browser at desktop and narrow breakpoints. Verification covers navigation, focus, disabled controls, loading, retained refresh, empty, cache, and error states where applicable. Build output and source-level tests alone do not establish that the visual migration is complete.

## Risks / Trade-offs

- [Mantine defaults leak a generic dashboard aesthetic] → Encode all product tokens and component defaults before migrating routes; prohibit default-gradient, heavy-shadow, and card-per-row patterns in shared patterns.
- [Global CSS and component styles conflict during migration] → Scope remaining local CSS to charts and documented exceptional layouts; migrate and delete route-local selectors domain by domain instead of adding overrides.
- [Dense market and trade controls become too spacious] → Configure compact control sizes and validate market rail, order form, table, and 767px layouts against the current behavioral density.
- [Overlay, menu, and controlled-input migration loses existing state] → Replace presentation around existing state owners and add focused interaction tests before retiring the legacy control.
- [Large migration obscures functional regressions] → Keep changes domain-batched, preserve routes and API payload contracts, and run browser acceptance checks after each batch.
- [New dependencies enlarge the bundle] → Install only core packages and behavior-justified extensions, rely on the normal build pipeline, and review production build output before release.

## Migration Plan

1. Record the accepted theme and shared-pattern contract, inventory existing routes and their UI-state requirements, and add the versioned Mantine dependencies.
2. Add the root provider, application theme, global CSS bridge, notification host, and shared UI pattern modules while retaining behavior owners.
3. Replace the application shell and navigation, then migrate shared feedback and controls so domains consume one vocabulary.
4. Migrate market workbench and contract-rail presentation first, followed by trading, automation, account, information, and settings domains; validate each domain before moving on.
5. Remove obsolete selector families and component markup after every consumer is on the shared pattern, then run full frontend tests, production build, strict OpenSpec validation, and browser checks.

Rollback is source-only: restore the prior frontend dependency manifest, shared theme/components, and migrated route markup/CSS together. No database, API, route, or backend rollback is required.

## Open Questions

- None. The selected component system is Mantine; the existing design guide supplies the product-level visual constraints that its theme must implement.
