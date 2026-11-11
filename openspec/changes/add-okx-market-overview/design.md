## Context

The app has a market tab router, a cached SWAP ticker endpoint, and a US event timeline feed. OKX documents `GET /api/v5/market/platform-24-volume` with `volUsd`, `volCny`, and `ts`, but the project does not call it. This API describes OKX order-book platform trading volume over a rolling 24-hour window, not all-crypto turnover.

## Goals / Non-Goals

**Goals:**
- Add a read-only overview reachable from market navigation.
- Display independently sourced platform volume, representative SWAP ticker data, and upcoming US events with clear units and source states.
- Preserve last known complete platform volume during a brief upstream failure and identify it as cached.

**Non-Goals:**
- Global crypto market cap, market-wide turnover, ETF flows, or historical aggregate charts.
- New private credentials, trading actions, or changes to the existing radar and event-detail workflows.

## Decisions

- Add a small public `OkxClient` method for the platform-volume endpoint and a backend `/api/market/overview/volume` read endpoint. Validate a positive `volUsd` and plausible source timestamp before exposing a numeric value. Cache for 60 seconds to stay well below the OKX rate limit. On a refresh failure, retain a validated snapshot for at most 15 minutes and return `cached`; otherwise return `unavailable` without a fabricated zero. An in-memory cache is sufficient for this read-only, quickly expiring value.
- Keep ticker and event requests independent in the new page. Use the existing `/api/tickers` snapshot for BTC, ETH, and SOL USDT perpetual contracts, and `/api/market/us-events` for nearby US events. A failed or empty section must not blank other sections. Preserve prior complete content while refreshing.
- Add `/market/overview` to the existing market-tab router. Use current `Paper`, status, and compact data patterns plus the existing design tokens. Keep the page naturally scrolling on desktop and narrow screens.
- Show a source and Shanghai-time update label for each data group. Label platform volume as `OKX 平台 24 小时成交额（USD）`; label SWAP ticker volume by the actual unit, without treating it as market-wide volume.

## Risks / Trade-offs

- [OKX endpoint is unreachable or returns incomplete fields] → Show an unavailable message for platform volume, retain other sections, and allow retry through the next poll or reload.
- [Snapshot becomes old during an outage] → Mark it cached with its update time; suppress values older than 15 minutes.
- [Events are sparse on a given day] → Show an explicit empty state and a link to the full event timeline.

## Migration Plan

Deploy the backend and frontend together. The new route is additive; reverting the two source changes restores the previous navigation without migrating data.

## Open Questions

None for this first version. Historical global measures need a separately selected data provider.
