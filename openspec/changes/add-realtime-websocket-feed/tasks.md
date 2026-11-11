## 1. Backend Realtime Foundation

- [x] 1.1 Add live/demo private WebSocket URL settings and expose only non-secret realtime capability metadata through settings status.
- [x] 1.2 Define normalized realtime event types for status, error, stale, market ticker, market candles, account, position, order, automation status, alert, and signal events.
- [x] 1.3 Implement a backend realtime hub that accepts browser WebSocket connections, validates subscribe/unsubscribe messages, and fans out events by topic.
- [x] 1.4 Add heartbeat, disconnect cleanup, reconnect backoff, and stale-state notifications for browser feed sessions.
- [x] 1.5 Cover subscription validation, unsupported topic errors, and connection cleanup with backend tests.

## 2. Public Market Streams

- [x] 2.1 Reuse or refactor the existing OKX public WebSocket client so ticker and candle streams can feed the realtime hub.
- [x] 2.2 Keep REST/cache candle seeding before candle deltas and preserve the existing `/ws/candles` behavior during migration.
- [x] 2.3 Add ticker subscriptions for selected trade instruments and visible market instruments without requiring credentials.
- [x] 2.4 Add throttling or batching for high-frequency ticker events before broadcasting to React clients.
- [x] 2.5 Test public market event normalization, unsupported bar handling, and REST fallback when OKX WebSocket fails.

## 3. Private Account Streams

- [x] 3.1 Implement backend-only OKX private WebSocket login with correct environment-specific credentials and private endpoint selection.
- [x] 3.2 Subscribe to account, positions, and orders channels when credentials are configured.
- [x] 3.3 Send typed disabled-state events when private topics are requested without configured credentials.
- [x] 3.4 Persist or reconcile order updates before broadcasting order events to browser clients.
- [x] 3.5 Trigger REST snapshot refresh requirements after private WebSocket reconnect or sequence uncertainty.
- [x] 3.6 Test private login request construction, missing-credential behavior, order persistence before broadcast, and reconnect recovery events.

## 4. Internal Automation Streams

- [x] 4.1 Broadcast automation status events after global pause/resume, strategy enablement, archive/restore, or circuit-breaker state changes are persisted.
- [x] 4.2 Broadcast alert events after automation alerts are persisted.
- [x] 4.3 Broadcast signal events after signal creation or execution-path updates are persisted.
- [x] 4.4 Keep persisted automation status, alerts, signal detail, and signal log REST APIs as the review source of truth.
- [x] 4.5 Test automation broadcasts and verify no live automatic trading capability is introduced.

## 5. Frontend Integration

- [x] 5.1 Add a shared realtime client hook with subscribe/unsubscribe, reconnect backoff, heartbeat awareness, stale status, and REST snapshot callback hooks.
- [x] 5.2 Migrate market chart and market/ticker list consumers to the shared realtime client while preserving manual refresh.
- [x] 5.3 Migrate the trade page selected-instrument price, account summary, position summary, and order-status freshness to realtime updates with REST fallback.
- [x] 5.4 Migrate account and positions pages to realtime account/position updates while retaining manual refresh and filters.
- [x] 5.5 Migrate automation overview and signal-log freshness indicators to internal realtime events while keeping REST search and pagination.
- [x] 5.6 Keep leverage, announcements, Earn, settings, historical orders, and paged signal logs REST-first.
- [x] 5.7 Add or update frontend static tests for reconnect fallback, stale warnings, topic subscriptions, and unchanged paged/search behavior.

## 6. Verification

- [x] 6.1 Run backend tests covering realtime hub, OKX public/private adapters, persistence, and existing REST endpoints.
- [x] 6.2 Run frontend tests and production build.
- [x] 6.3 Run OpenSpec validation for the new change and all specs.
- [x] 6.4 Smoke test Docker or local services with REST health, existing `/ws/candles`, and new realtime feed connectivity.
- [x] 6.5 Inspect representative market, trade, account, positions, and automation pages for fallback labels and responsive behavior after realtime updates.
