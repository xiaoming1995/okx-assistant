## Context

The dashboard already centralizes OKX REST access in `backend/app/okx.py`, exposes normalized read-only market APIs from `backend/app/main.py`, and renders market subpages from `frontend/src/main.tsx`. OKX V5 exposes official announcements through two support endpoints:

- `GET /api/v5/support/announcements`
- `GET /api/v5/support/announcement-types`

Both endpoints can be used without API credentials. The announcement list endpoint treats a request containing `OK-ACCESS-KEY` as private and then requires authentication, so the dashboard must call it as a public endpoint. The announcement-type endpoint is limited to 1 request per 2 seconds by IP, and announcement lists are limited to 5 requests per 2 seconds.

## Goals / Non-Goals

**Goals:**

- Add a market announcement page for official OKX notices.
- Normalize OKX announcement responses into a stable backend payload for the frontend.
- Support filtering by OKX announcement type and paging through result pages.
- Show Chinese announcements by default through `Accept-Language: zh-CN`.
- Cache announcement types and announcement pages, with stale fallback when OKX returns rate-limit or network errors.

**Non-Goals:**

- No trading signal generation, ranking, strategy mutation, or automatic action from announcements.
- No private account-specific announcement access.
- No scraping announcement detail bodies; the first version links to the OKX-hosted article URL.
- No push notifications or scheduled polling in the first version.

## Decisions

1. Use public-only OKX client methods.

   Add `get_announcement_types()` and `get_announcements()` to `OkxClient` with `auth=False`. They should pass an `Accept-Language` header, but they must not attach API credentials. This keeps the feature independent from live/simulated trading settings and avoids changing the endpoint into private mode.

   Alternative considered: reusing authenticated settings for region-specific filtering. Rejected for the first version because it couples a read-only information page to credential presence and may fail when credentials are absent or scoped differently.

2. Add backend proxy endpoints instead of calling OKX directly from the browser.

   Expose `/api/announcements/types` and `/api/announcements`. The backend can normalize field names, validate `annType` and `page`, add cache metadata, and reuse the existing `OkxError` behavior for OKX business errors such as `50011`.

   Alternative considered: frontend direct fetch to OKX. Rejected because it duplicates OKX response parsing in the UI, makes cache handling weaker, and can run into browser/network policy differences.

3. Cache announcement types separately from announcement pages.

   Announcement types change rarely and have a stricter limit, so they should have a longer cache lifetime. Announcement pages should cache by `language`, `annType`, and `page`. A manual refresh may bypass fresh cache but should still fall back to stale cache if OKX rejects the request.

   Alternative considered: no cache. Rejected because live verification showed `50011 Too Many Requests` can happen quickly, especially on the type endpoint.

4. Put the UI under the market section.

   Announcements affect markets, listing status, delistings, trading rules, deposits/withdrawals, API behavior, and Earn products. The first version should add a `公告` tab under the existing `市场` section beside `合约雷达`, `行情图表`, and `交易数据`.

   Alternative considered: top-level navigation entry. Rejected because announcements are auxiliary market context rather than a primary trading workflow.

## Risks / Trade-offs

- OKX may return future-dated `businessPTime` values in documentation examples or live regional feeds -> Display both source-provided times without inferring market impact.
- OKX may return `50011` with HTTP 200 or 429 -> Continue parsing response `code` and use stale cache fallback for either form.
- Announcement type descriptions depend on `Accept-Language` -> Persist language in cache keys and default to `zh-CN`.
- A stale cache could hide a new urgent notice -> Show `source`, `cacheAgeMs`, and warning text when data is not fresh.
- Frontend file is already large -> Keep the page component scoped and reuse existing `Notice`, tab, button, and panel styles instead of introducing a new design system.
