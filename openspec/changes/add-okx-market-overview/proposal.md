## Why

The market area currently focuses on individual perpetual contracts and a contract radar. Users need a concise overview of the OKX market activity available through documented APIs, with the scope of each number made explicit.

## What Changes

- Add a market overview page with OKX platform rolling 24-hour trading volume in USD.
- Reuse existing perpetual ticker snapshots for a small BTC, ETH, and SOL watch section, and the existing US events feed for upcoming events.
- Show source, timestamp, unit, loading, stale, and unavailable states for each independent data section.
- Do not present OKX platform volume as global cryptocurrency turnover or invent a global market-cap or historical series.

## Capabilities

### New Capabilities

- `okx-market-overview`: Read-only OKX platform activity and existing contract and event context in one market page.

### Modified Capabilities

None.

## Impact

- Adds a public OKX REST client method and a cached backend read endpoint.
- Adds one market navigation tab and overview UI under `frontend/`, following `docs/frontend-design-guidelines.md`.
- Reuses `/api/tickers` and `/api/market/us-events`; no private trading credentials or new external provider is required.
