## Context

`MarketInstrumentRail` is shared by the market chart, AI outlook, and trading-data pages, but each page currently mounts its own instance and owns separate search, filter, sort, list-ticker, and selection-adjacent state. In the supplied desktop view, this makes the rail look shared while switching tabs can reset the user's browsing context.

The rail already has client-side filtering, relevance sorting, local watched state, direct-route selection, and an empty-state recovery action. The current chart-only default is `watch`; the next design must preserve that state behavior while simplifying how users understand and operate the rail.

## Goals / Non-Goals

**Goals:**

- Make the first visible decision a fast choice between locally followed contracts and the complete list.
- Move low-frequency range filters and non-default sorting behind concise, discoverable controls.
- Make count labels, current range, local-followed semantics, and row hierarchy easy to scan.
- Preserve search, direct links, current selection, realtime subscriptions, and local star actions across all rail consumers.
- Keep the rail mounted as the stable left side of a market workbench while chart, AI, and trading-data content changes on the right.
- Let Radar candidates open a chosen contract directly in any market-workbench view.
- Keep the same usable hierarchy on narrow layouts without horizontal clipping.

**Non-Goals:**

- Do not add an API for, or imply support for, synchronizing favorites from the OKX App or website.
- Do not change the instrument API, watchlist API, database schema, chart data, trading actions, or route format.
- Do not remove USDT-settled, coin-settled, or tradable-only browsing; only change their presentation.
- Do not change a page's direct-entry default filter or replace a directly selected non-followed contract.

## Decisions

### 1. Use progressive disclosure for range and sort controls

The persistent rail controls will be: a search field, primary `已关注` and `全部` range buttons, and compact `筛选` and `排序：<当前值>` triggers. The `筛选` popover contains `USDT本位`、`可交易`、`币本位`; the sort popover contains `默认`、`涨跌`、`成交量`.

When an advanced range is active, the filter trigger MUST show the active range and the two primary range buttons MUST not falsely appear selected. Selecting any range continues to use the existing single local filter state.

Alternative considered: retain all filters and sorting as visible chips. This makes every option discoverable but gives low-frequency controls equal visual weight to choosing a contract.

### 2. Describe the local watchlist truthfully and compactly

The `watch` filter will be labeled `已关注` in this rail. The panel summary will show local counts in a readable form such as `已关注 2 · 全部 454`, rather than an ambiguous fraction such as `2/2`. Empty messaging will retain a short explanation that the list is local and keep the existing `查看全部合约` recovery action.

Alternative considered: retain `自选` everywhere. It is familiar exchange vocabulary, but in this product it can imply an unsupported synchronization with a user's OKX App favorites.

### 3. Treat each row as a self-contained comparison unit

Remove the list legend. Each row will maintain the existing two-column information structure: left side for code, perpetual/type context, and readable asset name; right side for last price and daily change; star action remains isolated at the edge. Secondary content truncates rather than increasing row height unpredictably.

Alternative considered: preserve the list legend to explain columns. It duplicates the stable row layout and adds a line between controls and the data users came to compare.

### 4. Introduce a stable market workbench boundary

A `MarketContractWorkspace` will own one mounted rail, its loaded instruments and ticker snapshot, ticker update/source/connection state, local watch mutation, search, filter, and sort state. `App` remains the owner of the route-level `selectedContract`, so deep links, Radar actions, and the workbench all use one selected contract. The chart, AI outlook, and trading-data panels consume this same workbench snapshot rather than reloading or subscribing to a second instrument/ticker state. They remain separate right-side consumers because their candle, AI, and trading-statistics requests have different lifecycles; only the chart retains a candle realtime subscription.

The workbench receives an initial range that preserves the current direct-entry behavior: the chart starts in local-followed mode, while a direct AI or trading-data entry starts in its existing USDT-settled mode. Once mounted, moving among those three views preserves the shared rail state.

Alternative considered: retain three mounted rail instances and lift only filter values to `App`. This would preserve some visible controls but would still duplicate ticker snapshots, refreshes, watch mutations, and scroll lifecycle, making the left column feel inconsistent.

### 5. Treat Radar as a discovery source, not a fourth rail consumer

Radar keeps its candidate scan, scoring controls, and local result selection. Its open actions write the chosen instrument to the route-level selected contract and then navigate to a target workbench view: chart, AI outlook, or trading data. Manual trade and automation actions continue to use the same selected-contract handoff without inheriting the market workbench rail.

Alternative considered: render the full market rail inside Radar. That would duplicate the discovery list beside the ranked candidate list and blur the distinction between discovering a contract and inspecting a chosen one.

### 6. Preserve Radar candidate visibility at the workbench handoff

Radar opens a candidate for inspection, so its chart, AI outlook, and trading-data actions will initialize a newly mounted workbench in the `全部` range. This is an entry-specific one-shot initial range: it does not replace the existing direct-entry defaults (`已关注` for chart and `USDT本位` for direct AI outlook or trading-data entry), and it does not reset a workbench that is already mounted while the user changes tabs. The existing relevance sort keeps the selected Radar candidate near the top of that complete result set.

The compact controls will use two visual rows in the desktop rail as well as narrow layouts: the persistent `已关注`/`全部` choices form the first row and the on-demand range/sort triggers form the second. This keeps an active label such as `筛选：USDT本位` readable without shrinking or colliding with its neighboring control.

Alternative considered: use the target page's direct-entry default for Radar handoff. A coin-settled Radar candidate can then be absent from the AI or trading-data rail's `USDT本位` range, which makes the selected right-side contract and the left rail disagree.

### 7. Collapse the desktop rail without resetting its workbench context

`MarketContractWorkspace` will own a transient `railCollapsed` state. On desktop, a labelled left/right chevron control changes only the workbench grid from the normal rail width to a narrow toggle strip; the rail's search, filter, sort, loaded instruments, ticker snapshot, local-watch mutation state, and selected contract stay mounted in the same workbench. The control will remain available via tooltip and `aria-label` in both states.

At the existing single-column breakpoint, the rail remains visibly expanded above the right-side content regardless of the desktop collapse preference, because there is no horizontal content area to reclaim. Returning to a desktop width restores the user's current workbench collapse preference. The preference is intentionally not persisted across a new workbench mount or page reload in this iteration.

Alternative considered: conditionally unmount the rail on collapse. That would unnecessarily interrupt visible-list state and makes reopening the rail look like a new page load despite the shared workbench being designed to retain continuity.

## Risks / Trade-offs

- [Advanced filters are less immediately visible] → The `筛选` trigger will state its active condition, and its popover will include all previous ranges with accessible labels.
- [Users confuse `已关注` with OKX favorites] → Use local-followed wording and explicit empty-state copy; do not claim external synchronization.
- [Shared-workbench changes affect three pages] → Add focused tests for cross-tab state continuity, direct-entry defaults, and the single rail mount.
- [Radar navigation sends the wrong contract or target] → Centralize Radar target routing at the existing route-level selected-contract handoff and cover every market target.
- [Popover interaction regresses keyboard or outside-click behavior] → Use semantic buttons, focus management, Escape/outside-close behavior, and accessible menu/listbox roles.
- [Smaller widths lose clarity] → Keep controls wrapping or stacking within the rail and verify no horizontal clipping at the existing responsive breakpoint.
- [Radar handoff leaks into a later direct entry] → Keep the `全部` initial range as ephemeral App state and clear it for direct navigation and hash-route application.
- [Collapsed rail hides a keyboard focus target] → Keep a labelled expand control visible in the narrow desktop strip, and use responsive CSS to expose the full rail in single-column layouts.

## Migration Plan

1. Add focused coverage for primary range selection, advanced range/sort selection, visible active-state labels, local-followed copy, and selection/watchlist independence.
2. Refactor shared rail presentation while reusing the existing filter and sort enum values.
3. Preserve the current chart-only empty-state recovery and test it alongside the compact rail.
4. Rebuild the frontend and validate all three market-page consumers in a browser at desktop and narrow widths.
5. Roll back by restoring the current always-visible `filterTabs`, `sortBar`, and list legend; no persisted data migration is required.

## Open Questions

- None. The proposal deliberately treats this product's star list as local until an official, supported OKX favorite-sync API is available.
