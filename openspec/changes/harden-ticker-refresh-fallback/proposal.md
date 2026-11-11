## Why

The public OKX bulk SWAP ticker response is occasionally truncated while streaming through the upstream delivery path.  The dashboard already preserves a complete prior snapshot, but it surfaces the raw `IncompleteRead` exception to users even while chart and WebSocket data remain usable.

## What Changes

- Treat a failed bulk ticker refresh as a background freshness event when a complete cached snapshot exists, rather than a page-level error.
- Add bounded retry scheduling with backoff after repeated incomplete upstream responses, so page visits do not repeatedly request the same large response.
- Return structured ticker freshness and degradation metadata from `/api/tickers`.
- Replace raw upstream exception text in the UI with a concise Chinese description of the retained snapshot, its age, and whether live selected-contract prices remain available.
- Preserve an explicit degraded state when no complete snapshot is available; never silently present incomplete ticker data as current.

## Capabilities

### New Capabilities

- `resilient-market-ticker-refresh`: Complete-snapshot caching, failure backoff, and user-readable degraded-state metadata for the bulk market ticker feed.

### Modified Capabilities

- None.

## Impact

- Backend ticker refresh and `/api/tickers` payload handling in `backend/app/main.py`.
- Shared market-workspace ticker loading and freshness messaging in `frontend/src/main.tsx` and `frontend/src/styles.css`.
- Backend and frontend regression tests for transient incomplete responses, retained snapshots, retry scheduling, and the no-raw-error UI boundary.
