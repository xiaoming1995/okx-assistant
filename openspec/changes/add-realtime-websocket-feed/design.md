## Context

The app already exposes `/ws/candles` for a selected contract and bar. That endpoint seeds the browser with cached/REST candle data, then forwards OKX public WebSocket candle and ticker events, falling back to REST when the upstream WebSocket is unavailable.

Other realtime-looking views still poll REST endpoints: market lists poll tickers, trade polls orders/tickers/account/leverage, account and positions poll account data, and automation pages poll status/signals/alerts. Some of those resources are naturally streaming, while others are query or configuration workflows that should remain REST-first.

OKX separates public WebSocket channels from private channels. Public channels can deliver tickers, candles, trades, and depth without authentication. Private account, position, and order channels require backend login and must never expose API credentials to browser clients.

## Goals / Non-Goals

**Goals:**

- Provide a reusable backend-managed realtime feed for browser clients.
- Reuse the existing public market WebSocket behavior while avoiding a separate upstream OKX connection per browser tab where practical.
- Add backend support for OKX private WebSocket login and subscription to account, positions, and orders when credentials are configured.
- Push internal automation status, alert, and signal-created events from the backend to visible clients.
- Keep REST snapshot APIs for initial load, filters, pagination, manual refresh, and reconnect recovery.
- Give the frontend one shared realtime client pattern with heartbeat, backoff, throttling, stale-state display, and REST fallback.

**Non-Goals:**

- Replacing all REST APIs with WebSocket.
- Moving OKX private WebSocket signing or credentials into frontend code.
- Implementing WebSocket order placement, amend, or cancel paths in this change.
- Streaming low-frequency or query-oriented resources such as announcements, Earn data, leverage configuration, settings, historical orders, and paged signal logs as primary data sources.
- Enabling live automatic trading. Existing safety boundaries for live/manual and simulated automation remain unchanged.

## Decisions

### Use a backend realtime hub instead of direct browser-to-OKX connections

The backend will expose one local feed endpoint, tentatively `/ws/realtime`, that accepts browser subscription messages and sends normalized events. The backend owns OKX upstream connections, signing, environment selection, fanout, and reconnect handling.

Alternatives considered:

- Direct browser connection to OKX public WebSocket. This can work for public market data, but creates more browser-specific connection handling and does not help private channels.
- Direct browser connection to OKX private WebSocket. Rejected because credentials and signing must remain backend-only.
- Server-Sent Events. SSE is simpler for one-way backend events, but a WebSocket feed better matches existing code and supports dynamic subscribe/unsubscribe messages from the browser.

### Keep REST snapshot plus WebSocket delta

Each page will continue to load an initial REST snapshot before attaching realtime updates. On WebSocket reconnect, subscription changes, environment switches, or stale sequence detection, the page will refresh its REST snapshot and then resume applying deltas.

This preserves search and pagination correctness. Historical order records and signal logs remain REST-queryable, while WebSocket events can notify the UI that new records exist or update the visible first page.

### Split public, private, and internal event sources

The backend hub will normalize three event classes:

- `market.*`: public ticker/candle/depth-style updates from OKX public WebSocket.
- `account.*`, `position.*`, `order.*`: private updates from OKX private WebSocket when credentials exist.
- `automation.*`: app-generated events for automation status, alerts, strategy state, signal creation, and execution-path changes.

Private event subscriptions must respect the selected trading environment. Demo and live environments need separate private WebSocket URLs and credentials, with live data available only when live credentials are configured. Missing credentials should result in a typed feed warning while REST fallback continues.

### Do not stream configuration-only workflows

Leverage remains REST-driven because it is scoped by instrument, margin mode, and position side, and the user explicitly changes it through a submit action. Announcements and Earn data remain REST/cached because they are low-frequency, paged/query resources. Settings remain REST because they describe configuration state and security-sensitive capabilities.

### Preserve persisted state as source of truth

The backend will still persist local order records, automation signals, alerts, and risk/audit details before or alongside broadcasting events. Browser state derived from WebSocket messages is an optimization for freshness, not the audit record.

### Throttle high-frequency UI updates

Market events can arrive faster than React views need to render. The shared frontend realtime hook should batch or throttle updates per subscription, especially for ticker lists and radar pages. Candle chart updates can use the current selected instrument/bar stream and should not trigger full list rerenders for every tick.

## Risks / Trade-offs

- OKX private WebSocket login or subscription failure -> keep REST polling fallback, expose a visible feed warning, and avoid marking data as live.
- Missed events during disconnect -> refresh REST snapshots on reconnect before applying new deltas.
- Too many upstream OKX connections from multiple tabs -> centralize upstream connections in the backend and fan out to local browser clients.
- High-frequency ticker updates causing UI churn -> throttle, batch, and scope subscriptions to visible instruments.
- Event ordering differences between REST snapshots and deltas -> include event timestamps/source metadata and favor snapshot state after reconnect or filter changes.
- Real-money safety expectations expanding implicitly -> keep WebSocket order placement out of scope and preserve existing manual/live safety controls.
- Private channel limits and heartbeat requirements -> implement ping/pong, reconnect backoff, resubscription, and channel-count error handling in the backend.

## Migration Plan

1. Add backend configuration for public/private WebSocket URLs across live and demo environments.
2. Introduce the realtime hub endpoint and normalized event schema while leaving existing polling untouched.
3. Migrate public market data first: selected trade ticker and visible market ticker updates.
4. Add private account, position, and order subscriptions with REST fallback and disabled-state events when credentials are missing.
5. Broadcast internal automation status, alert, and signal-created events from the backend after persistence.
6. Remove or lengthen frontend polling only after each page has snapshot, reconnect, stale-state, and manual refresh coverage.
7. Validate with backend unit tests, frontend static tests, build, and Docker smoke checks.

Rollback is straightforward because REST endpoints remain the authoritative path. If the realtime hub is disabled or unavailable, pages continue to load snapshots and can keep their existing polling behavior.

## Open Questions

- Should the first implementation expose only one `/ws/realtime` endpoint, or keep `/ws/candles` for charts and add `/ws/realtime` for all other views?
- Should private order/position subscriptions default to `instType: ANY`, or should the UI subscribe only to visible instrument families to reduce event volume?
- What stale threshold should the UI show for each data class: market, account, order, and automation?
