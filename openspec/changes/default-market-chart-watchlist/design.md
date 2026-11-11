## Context

`MarketInstrumentRail` is shared by the market chart, AI outlook, and trading-data pages. Each page holds its own `filter` state and currently initializes it as `usdt`. The instruments API already returns a persistent `watched` flag, and the rail can filter that flag with its existing `watch` filter. The watchlist endpoints already add and remove favorites.

The requested optimization concerns the market-chart workbench shown in the supplied screenshot. Applying a default to the shared rail itself would unintentionally change the first view of the adjacent AI and trading-data workflows, so the default belongs in the chart page's local state rather than the shared component.

## Goals / Non-Goals

**Goals:**

- Open the market-chart page directly into the user's persisted self-selected contracts.
- Make an empty self-selected list explain itself and offer a single-step way to resume browsing all contracts.
- Preserve a directly supplied or previously selected contract in the chart workbench even when it is not self-selected.
- Leave manual filters, search, sorting, favorites, realtime subscriptions, and adjacent market pages unchanged.

**Non-Goals:**

- Do not alter AI outlook or trading-data initial filters.
- Do not automatically add a viewed contract to the watchlist, rewrite the route, or replace it with the first favorite.
- Do not add a new API, persistence field, user preference, external dependency, or trading behavior.

## Decisions

### 1. Set the default only in MarketPage

`MarketPage` initializes its local filter to `watch`; the shared list hook and rail remain filter-agnostic. This delivers the requested default precisely where shown while keeping the existing defaults for `MarketAiOutlookPage` and `MarketStatsPage`.

Alternative considered: change `MarketInstrumentRail` or `useMarketInstrumentRows` to default to `watch`. Those are shared and would silently alter unrelated market-page entry behavior.

### 2. Treat an empty watchlist as an intentional recoverable state

When instruments finish loading and the active filter is `watch` with no matching rows, the rail explains that no contracts are self-selected and provides `查看全部合约`. The action changes only the local filter to `all`; it does not modify the watchlist or selected contract.

Alternative considered: automatically fall back to all contracts. This would hide the distinction between an empty watchlist and a populated default and would make the active `自选` filter misleading.

### 3. Keep selection independent from the left filter

The chart's selected contract remains the route/current-workbench contract. When it is not a favorite, the right-side chart remains visible and the left rail is allowed to show only favorites. It is not injected into the watchlist result and is not implicitly starred.

Alternative considered: automatically select the first favorite. This changes a user-requested or deep-linked chart without consent.

## Risks / Trade-offs

- [A new user has no self-selected contracts] → Show a clear empty state with `查看全部合约`, rather than a blank list or automatic fallback.
- [A direct link selects a non-favorite contract] → Preserve the right-side selection and leave the left self-selected list unchanged.
- [A user removes the final favorite] → The rail transitions to the same empty self-selected state after the existing refresh completes.
- [The shared rail later gains new default behavior] → Keep the market-chart default in local `MarketPage` state and cover adjacent page defaults with focused tests.

## Migration Plan

1. Add focused assertions for the chart-only initial filter, empty self-selected state, restore action, and selection independence.
2. Update the chart page state and rail empty-state presentation without changing API behavior.
3. Verify the populated, empty, direct-link, watch/unwatch, and manual-filter paths in a browser.
4. Roll back by restoring the chart page's local initial filter to `usdt`; all stored favorites remain intact.

## Open Questions

- None. This change intentionally does not persist a user's most recently selected filter; it provides a stable `自选` default for the chart page only.
