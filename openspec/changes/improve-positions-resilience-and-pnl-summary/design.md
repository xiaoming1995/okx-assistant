## Context

`GET /api/account` obtains balance and positions sequentially from OKX. A transport interruption after the client-level retries currently reaches the browser as the raw `OkxError` text. The server already persists successful account and position snapshots, but account refreshes have no bounded retry schedule or display-safe refresh metadata. On the frontend, positions are calculated from the OKX `upl` field, but table styles override the generic colour classes that were intended to communicate sign.

## Goals / Non-Goals

**Goals:**

- Preserve the last complete account-and-position snapshot during transient upstream failures and explain freshness without leaking transport details.
- Bound repeated refresh work across polling and real-time snapshot requests.
- Make current open-position floating P&L legible, signed, and consistently colour-coded.
- Present an explicit, explainable aggregate of the current open positions.

**Non-Goals:**

- Guarantee OKX availability, replace its HTTP client, or treat a partial response as a valid snapshot.
- Place, cancel, or otherwise change trades.
- Present a lifetime or tax P&L. The first summary is only the current open-position sum of OKX `upl`.
- Combine `upl` with `realizedPnl`, fees, or funding fees, because their time scopes differ from current floating P&L.

## Decisions

### Return complete account snapshots first and refresh them in the background

The account cache will store a complete combined balance/positions payload, its timestamp, a bounded failure count, the next eligible retry time, and a display-safe refresh state. When a complete memory or persisted snapshot exists, `/api/account` will return it immediately and start at most one background refresh once the shared retry deadline permits. A failed job increments capped exponential backoff; a successful job clears that state.

This matches the resilient ticker behaviour without sharing its cache, because account data is private and separated by active trading environment. The existing client-level retry remains a single refresh attempt; the new backoff is between background jobs.

Alternative considered: return HTTP 502 on every failed forced refresh. This discards usable position information, amplifies polling retries, and makes realtime events less reliable in degraded networks.

### Keep transport exceptions server-side and expose structured freshness metadata

The API will expose a `refresh` object containing a safe state, cache age, retry timing, and a Chinese status label. The legacy `warning` field remains compatible but will contain only a display-safe message. The server logs raw upstream errors for diagnosis. If no complete snapshot exists, the API returns an explicit unavailable state with no raw exception text.

Alternative considered: suppress degradation messages entirely. Users need to know whether displayed holdings are current, so the UI must keep freshness visible without showing protocol internals.

### Define the new aggregate as open-position floating P&L

The positions page will calculate `Σ upl` over open positions only. It will display the signed aggregate, counts of positive/negative/zero P&L positions, total margin, and total notional USD. The summary is independent of the table’s search and side filters so it describes the account’s actual open exposure. It will be named “未实现盈亏汇总” and show snapshot freshness/source beside it.

Alternative considered: add `upl`, `realizedPnl`, funding, and fees. Those values have different settlement windows and would make the number look like a complete account history when it is not.

### Use scoped semantic P&L classes rather than generic colour utilities

The positions table and summary will use explicit positive, negative, and neutral P&L classes whose selectors outrank generic table typography. Positive values include a `+` sign and green treatment; negative values retain their minus sign and use red; zero or unavailable values use neutral styling. This applies to both value and ratio.

Alternative considered: raise the specificity of the global `.up` and `.down` utilities. That can unexpectedly recolour unrelated tables, badges, and future widgets.

## Risks / Trade-offs

- [A long OKX outage leaves account data old] → surface cache age, source, refresh state, and bounded retry timing rather than labeling it current.
- [A forced real-time update causes request storms] → use one shared refresh job and a retry deadline per environment.
- [A position value is missing or not numeric] → classify it as neutral/unavailable and exclude it from numerical totals rather than treating it as profit.
- [Users read floating P&L as realized return] → label it explicitly as “未实现盈亏” and keep realized/fee/funding values out of the first summary.

## Migration Plan

1. Extend the account response with backward-compatible refresh metadata and safe messages.
2. Update the positions UI to consume metadata with fallbacks for older responses, then render the scoped P&L summary and styles.
3. Add deterministic backend and frontend regression coverage for cache fallback, retry state, numeric aggregation, and semantic classes.
4. Rebuild the local containers and validate a live account response plus a forced interrupted-refresh test path.
5. Roll back by reverting the account cache metadata and positions UI changes; existing persisted complete snapshots remain compatible.

## Open Questions

- None. The implemented aggregate is the requested current holding profit/loss, defined as floating P&L only.
