## Why

Several pages need near-real-time market, account, position, order, automation, and alert visibility, but they currently rely on fixed REST polling intervals. Polling is simple but creates delayed UI updates, repeated API load, and inconsistent freshness labels when data is event-driven.

## What Changes

- Add a unified realtime feed capability for browser clients to subscribe to normalized backend events.
- Extend realtime data beyond the existing candle WebSocket path to support public market updates, private account/position/order updates, and application-originated automation events.
- Keep REST snapshot APIs as the source for initial page load, search, filters, pagination, manual refresh, and reconnect recovery.
- Route OKX private WebSocket usage through the backend only, so browser clients never handle API secrets or OKX signing.
- Preserve persisted order, signal, alert, and audit records as the source of truth; WebSocket delivery only updates visible state and notifies the UI about new records.
- Keep low-frequency resources such as announcements, Earn data, settings, and leverage configuration on REST/cached APIs.

## Capabilities

### New Capabilities

- `realtime-websocket-feed`: Provides a backend-managed realtime feed with public market data, optional private account/order/position updates, internal automation events, REST snapshot fallback, and reconnect recovery behavior.

### Modified Capabilities

- None.

## Impact

- Backend WebSocket code needs a reusable connection manager, subscription handling, heartbeat/reconnect behavior, normalized event contracts, public OKX feed reuse, and private OKX feed support.
- Backend configuration needs private WebSocket endpoint support for live and demo environments without exposing credentials to the frontend.
- Frontend market, trade, account, positions, and automation pages need a shared realtime client hook with throttling, fallback, reconnect, and stale-state display.
- Existing REST APIs for account, orders, signals, announcements, leverage, settings, and historical/paged data remain available and continue to be tested.
- Tests should cover event normalization, subscription authorization/boundaries, reconnect fallback, private-feed disabled states, and unchanged REST pagination/search behavior.
