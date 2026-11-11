## ADDED Requirements

### Requirement: Realtime Feed Endpoint
The system SHALL expose a backend-managed WebSocket feed for browser clients to subscribe to realtime market, account, position, order, and automation events.

#### Scenario: Subscribe to realtime feed
- **WHEN** a browser client connects to the realtime feed and sends a valid subscription request
- **THEN** the backend accepts the subscription
- **AND** the backend sends a status event identifying the subscribed topics and active data source

#### Scenario: Reject unsupported topic
- **WHEN** a browser client subscribes to an unsupported realtime topic
- **THEN** the backend sends a typed error event for the unsupported topic
- **AND** the connection remains usable for supported topics

#### Scenario: Keep connection alive
- **WHEN** the realtime feed has no data events to send before the OKX idle timeout window
- **THEN** the backend keeps the upstream and browser connections alive with heartbeat behavior
- **AND** stale connections are closed or reconnected without crashing the service

### Requirement: Public Market Feed
The system SHALL stream public market updates through the backend without requiring OKX account credentials.

#### Scenario: Stream selected instrument ticker
- **WHEN** a page subscribes to ticker updates for a selected instrument
- **THEN** the backend subscribes to OKX public ticker data for that instrument
- **AND** the frontend receives normalized ticker events with instrument, source, and timestamp metadata

#### Scenario: Stream selected instrument candles
- **WHEN** a page subscribes to candle updates for a selected instrument and supported bar
- **THEN** the backend seeds candles from cache or REST before applying WebSocket updates
- **AND** the frontend receives normalized candle events suitable for the chart

#### Scenario: Unsupported candle interval
- **WHEN** a page requests a candle interval unsupported by the realtime feed
- **THEN** the backend sends a typed error event
- **AND** the subscription does not create an upstream OKX candle subscription

### Requirement: Private Account Feed
The system SHALL stream private account, position, and order updates through backend-owned OKX private WebSocket connections when credentials are configured.

#### Scenario: Subscribe with configured credentials
- **WHEN** the selected trading environment has valid OKX credentials and a browser subscribes to private account topics
- **THEN** the backend logs in to the matching OKX private WebSocket endpoint
- **AND** the backend subscribes to account, position, and order channels without exposing credentials to the browser

#### Scenario: Missing credentials
- **WHEN** a browser subscribes to private account topics and the selected trading environment lacks credentials
- **THEN** the backend sends a typed disabled-state event
- **AND** the frontend continues to rely on REST snapshots and manual refresh behavior

#### Scenario: Order event persistence
- **WHEN** an OKX private order update is received
- **THEN** the backend persists or reconciles the matching order record before broadcasting the normalized order event
- **AND** the order history API remains the source for paged and searched order records

#### Scenario: Reconnect private feed
- **WHEN** the private OKX WebSocket disconnects after a successful subscription
- **THEN** the backend reconnects with backoff
- **AND** subscribed browser clients are told to refresh their REST snapshots before applying new deltas

### Requirement: Internal Automation Feed
The system SHALL broadcast automation status, alert, signal, and execution-path changes as internal realtime events after backend state is persisted.

#### Scenario: Automation status changes
- **WHEN** global automation state, strategy enabled state, or circuit-breaker state changes
- **THEN** the backend broadcasts an automation status event after the state change is saved
- **AND** subscribed pages update visible status without waiting for the next polling interval

#### Scenario: Alert created
- **WHEN** a backend workflow creates an automation alert
- **THEN** the backend broadcasts an alert event with alert identity, severity, scope, source, and timestamp metadata
- **AND** the persisted alerts API remains available for review and acknowledgment

#### Scenario: Signal created
- **WHEN** an automation signal is created or its execution path changes
- **THEN** the backend broadcasts a signal event after the signal record is saved
- **AND** signal log search and pagination continue to use REST APIs

### Requirement: Snapshot And Fallback
The system SHALL retain REST snapshot APIs for initial load, query workflows, reconnect recovery, and manual refresh.

#### Scenario: Initial page load
- **WHEN** a realtime-enabled page opens
- **THEN** the page loads its current snapshot through existing REST APIs before applying WebSocket deltas
- **AND** the page displays source and freshness metadata for the visible data

#### Scenario: WebSocket unavailable
- **WHEN** the realtime feed is unavailable or returns an upstream error
- **THEN** the frontend displays a visible realtime warning
- **AND** the page continues to load data through REST snapshots or existing polling fallback

#### Scenario: Reconnect recovery
- **WHEN** a WebSocket reconnect completes after a disconnect
- **THEN** the frontend refreshes the relevant REST snapshot
- **AND** subsequent deltas are applied only after the snapshot refresh has completed

### Requirement: Query-Oriented Resources Remain REST
The system SHALL keep query-oriented and low-frequency resources on REST APIs as their primary data path.

#### Scenario: Historical order records
- **WHEN** the user searches, filters, or pages through local order records
- **THEN** the frontend requests the records through the existing paged REST API
- **AND** realtime order events do not replace REST search or pagination semantics

#### Scenario: Leverage configuration
- **WHEN** the user views or changes leverage for a contract, margin mode, and position side
- **THEN** the frontend uses REST APIs to load or submit the leverage setting
- **AND** realtime feeds do not imply that leverage is a streaming value

#### Scenario: Announcements and Earn data
- **WHEN** the user views OKX announcements or Earn data
- **THEN** the frontend uses REST/cached APIs for those resources
- **AND** the realtime feed is not required for announcement or Earn correctness
