## Why

OKX API and product announcements can affect market data behavior, supported instruments, and operational risk, but the dashboard currently has no in-app place to review those updates. Adding a read-only announcement center gives users a fast way to track official OKX notices without mixing them into trading execution or account actions.

## What Changes

- Add a market-section announcement page that lists official OKX announcements with type filters, paging, publish times, and source links.
- Add backend read-only API endpoints that proxy and normalize OKX announcement types and announcement list responses.
- Default requests to Chinese announcements via `Accept-Language: zh-CN`, while keeping the response shape stable for frontend rendering.
- Cache announcement types and announcement pages so OKX rate limits or transient network errors can fall back to stale data with a clear warning.
- Keep announcement fetching public-only: do not attach OKX API credentials and do not treat announcements as trading signals.

## Capabilities

### New Capabilities

- `okx-announcements-center`: Read-only display and filtering of official OKX announcements from the V5 support announcement APIs.

### Modified Capabilities

- None.

## Impact

- Backend OKX client: add public announcement and announcement-type fetch methods.
- Backend API: add normalized read-only `/api/announcements` endpoints with validation, cache metadata, and stale fallback.
- Frontend market navigation: add an announcement tab and page using the existing dashboard styles and notice patterns.
- Tests: add OKX client URL/header coverage, backend cache/error coverage, and frontend static coverage for the new market tab and API calls.
