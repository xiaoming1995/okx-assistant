## Why

The AI market-reading page currently has only a small, request-time macro snapshot. Users cannot see the coming U.S. market events, distinguish an official scheduled release from an already published fact, or replay the event context that accompanied a K-line move. A durable, source-attributed U.S. market event timeline provides the verified context needed for later LLM market reading without treating unverified news as fact.

## What Changes

- Add a read-only `美国事件` market page with a date-oriented timeline, category and state filters, a Shanghai-time default, and retained U.S. Eastern source time.
- Ingest and persist a bounded first set of high-impact, official U.S. events: Federal Reserve monetary-policy events, BLS employment and inflation releases, BEA growth/consumption/trade releases, and Treasury auction schedule events where a stable official schedule is available.
- Model each event through its lifecycle: scheduled, released, revised, or cancelled; retain source URL, source/fetch times, importance, and actual/forecast/previous/revision values where supplied.
- Expose a read-only API for date-window timeline browsing and event detail, with cache/fallback metadata rather than silently inventing missing values.
- Make event records suitable for a later AI evidence window, but do not change the existing AI-outlook prompt, add general news ingestion, or create trading actions in this change.

## Capabilities

### New Capabilities

- `us-market-event-timeline`: A source-attributed, date-filterable U.S. market event timeline for scheduled and published high-impact events.
- `us-market-event-ingestion`: Official-source normalization, lifecycle persistence, refresh behavior, and read-only timeline API contracts.

### Modified Capabilities

- None.

## Impact

- Affected backend: event-source adapters, persistence abstraction and SQLite/Postgres schema initialization, event refresh/cache logic, and a new read-only market API.
- Affected frontend: market route/tab parsing, a responsive timeline page, event cards, source/freshness states, and focused tests.
- No order, account, automation, LLM-provider, or existing `/api/market/ai-outlook` contract changes are included.
