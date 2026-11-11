## Context

`/api/tickers` loads the OKX bulk SWAP ticker response, which is large and delivered with chunked transfer encoding.  A complete ticker snapshot is already persisted and the browser maintains WebSocket subscriptions for selected and visible contracts.  Today, a failed REST refresh stores the raw exception as `warning`, and every page that consumes the shared workspace renders that message as a prominent notice.

## Goals / Non-Goals

**Goals:**

- Keep a validated complete snapshot available while transient bulk-refresh failures recover in the background.
- Bound retries across page polling with a shared backoff schedule rather than asking each page visit to synchronously retry a large upstream request.
- Give the UI structured freshness state and a plain-language, non-technical status message.
- Preserve explicit unavailable behavior when no complete snapshot exists.

**Non-Goals:**

- Guarantee availability of the upstream OKX or Cloudflare transport.
- Change order execution, market-analysis decisions, or the public WebSocket protocol.
- Treat a partial JSON body as a current complete market snapshot.

## Decisions

### Refresh from a complete snapshot is asynchronous and backoff-aware

When a complete cached or persisted snapshot exists, `/api/tickers` SHALL return it immediately.  Once it becomes stale, at most one background refresh starts and only when the shared retry deadline has elapsed.  A failed refresh increments a bounded failure count and sets the next retry deadline with capped exponential backoff.  This avoids forcing every consumer to wait on the same unreliable bulk request.

The existing client-level three attempts remain as an individual request attempt.  Backoff is applied between bulk-refresh jobs, not by multiplying the number of client-level attempts.

### Ticker metadata is structured and safe for display

The response adds a `refresh` object containing the state, cache age, retry time, and a safe status label.  Raw transport error text remains available only in backend logs; it is not sent as a user-facing `warning`.  The legacy `warning` field is retained for compatibility and is populated only when no complete snapshot is available.

### The UI distinguishes stale list data from live selected-contract updates

The shared workspace derives a compact status line from `refresh`.  It says that the contract list is using a prior complete snapshot, includes its update time, and notes whether the selected contract's WebSocket price feed is connected.  A stale list snapshot is a warning-level data-freshness state, not a page-blocking error banner.  The no-snapshot state remains visually prominent.

### Alternatives considered

- Switching HTTP libraries alone was rejected because repeated reads from inside the running container reproduce truncation at varying byte counts; a library swap cannot guarantee an upstream chunked response completes.
- Fetching an individual REST ticker for every contract was rejected as a replacement for the full list because it increases request volume and rate-limit exposure.  WebSocket updates already cover selected and visible rows.
- Hiding the error entirely was rejected because stale data must remain transparent to users.

## Risks / Trade-offs

- [A long upstream outage leaves the full list stale] → expose age and unavailable state, keep selected-contract WebSocket state separate, and retry on a capped schedule.
- [The first visit has no persisted snapshot] → retain an explicit unavailable response and a concise user-facing explanation.
- [API consumers use the legacy warning field] → preserve it while adding the `refresh` contract.
- [Tests rely on clock timing] → inject timestamps through the existing `now_ms()` function and assert state transitions deterministically.

## Migration Plan

1. Add structured refresh metadata and retry scheduling while preserving existing `data`, `source`, `ts`, `cacheAgeMs`, and `warning` fields.
2. Update the shared frontend workspace to use the new metadata when present and retain a fallback for older backend payloads.
3. Rebuild services and verify both a successful snapshot and a forced incomplete refresh retain usable data without exposing raw `IncompleteRead` text.
4. Roll back by reverting the metadata-aware UI and cache scheduling changes; persisted complete snapshots remain compatible.

## Open Questions

- None for this local read-only dashboard scope.
