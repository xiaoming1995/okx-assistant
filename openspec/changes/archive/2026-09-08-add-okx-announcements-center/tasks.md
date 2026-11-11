## 1. Backend OKX Integration

- [x] 1.1 Add public OKX client methods for announcement types and paged announcement lists with language headers.
- [x] 1.2 Add backend normalization helpers for announcement types, announcement rows, language, type, and page inputs.
- [x] 1.3 Add cache and stale-fallback behavior for announcement types and announcement pages.
- [x] 1.4 Expose read-only `/api/announcements/types` and `/api/announcements` routes.

## 2. Frontend Announcement Page

- [x] 2.1 Add announcement response types, source labels, date formatting helpers, and fetch logic.
- [x] 2.2 Add a `公告` market tab, hash routing, and page rendering.
- [x] 2.3 Build the announcement page UI with type filters, paging, refresh, source metadata, links, loading, empty, and warning states.

## 3. Verification

- [x] 3.1 Add backend tests for OKX client requests, public-only headers, normalization, cache hits, and stale fallback.
- [x] 3.2 Add frontend static tests for the announcement tab and API integration.
- [x] 3.3 Run focused backend tests, frontend static tests, frontend build, and strict OpenSpec validation.
