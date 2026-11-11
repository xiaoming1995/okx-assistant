## 1. Event Domain and Persistence

- [x] 1.1 Define normalized U.S. market event, event-version, category, importance, lifecycle-state, provenance, and date-window validation models.
- [x] 1.2 Add matching SQLite and Postgres tables, unique provider-event identity, scheduled-time/state indexes, and repository methods for upsert, version retention, date-window listing, and event detail.
- [x] 1.3 Implement lifecycle reconciliation so scheduled records become released, revised, or cancelled without losing earlier observed source versions.
- [x] 1.4 Add focused database/model tests for deduplication, revision retention, nullable figures, date-only events, and DST-safe UTC/source-timezone storage.

## 2. Official Source Adapters and Refresh Service

- [x] 2.1 Create a provider-adapter interface that returns normalized candidates, provider freshness, and isolated warnings, with bounded per-provider cache/retained-data behavior.
- [x] 2.2 Implement the Federal Reserve adapter for FOMC meeting, statement/decision, press conference, minutes, and available SEP context with official source links.
- [x] 2.3 Implement the selected BLS adapter for CPI, PPI, Employment Situation, JOLTS, and other approved high-impact calendar entries with official source links.
- [x] 2.4 Implement the selected BEA adapter for GDP, Personal Income and Outlays/PCE, and International Trade schedule entries with official source links.
- [x] 2.5 Validate a Treasury official-schedule adapter against captured fixtures and enable auction events only when announcement, auction, and settlement dates can be normalized without guessed values.
- [x] 2.6 Implement the date-window refresh service that persists candidates, uses shorter expiry near events, returns retained records after source failure, and produces deduplicated warnings.
- [x] 2.7 Add provider fixture tests for source normalization, partial/missing fields, changed source data, refresh failure, retained-data fallback, and absence of fabricated forecasts or release times.

## 3. Read-Only Event APIs

- [x] 3.1 Add `GET /api/market/us-events` with bounded `from`/`to` date validation, allow-listed category/state filters, scheduled-time ordering, and source/freshness/warning metadata.
- [x] 3.2 Add `GET /api/market/us-events/{eventId}` returning canonical event data, observed versions, and provenance without triggering trading/account mutations.
- [x] 3.3 Add API tests for valid date browsing, filters, invalid/excessive windows, ordered results, unknown detail IDs, partial provider availability, and retained-data warnings.

## 4. Market Timeline Interface

- [x] 4.1 Add the `#/market/us-timeline` route, `美国事件` market navigation tab, selected-date route query handling, and frontend API types/loaders.
- [x] 4.2 Implement the default Shanghai-time date header and adjacent-date rail while preserving each event's U.S. Eastern official time or explicit date-only/unknown-time state.
- [x] 4.3 Implement category and lifecycle filters, date-grouped loading/empty/error states, and source/freshness context without hiding usable retained events.
- [x] 4.4 Render distinct scheduled, released, revised, and cancelled event cards with title, importance, figures, period/unit context, direct official source link, and unavailable-value treatment.
- [x] 4.5 Add responsive styling that keeps the date rail, cards, values, timezone context, and source warnings readable at desktop and narrow/mobile widths.
- [x] 4.6 Add focused frontend coverage for route state, date/category/state filtering, timezone labels, structured figures, provider-warning rendering, empty states, and absence of order/automation controls.

## 5. Verification and Delivery Readiness

- [x] 5.1 Run focused backend database, source-adapter, lifecycle, and API tests.
- [x] 5.2 Run focused frontend tests and the production frontend build.
- [ ] 5.3 Run `openspec validate add-us-market-event-timeline --strict` and `git diff --check`.
- [x] 5.4 Verify the rendered route in a browser at desktop and narrow widths: date navigation, Shanghai/Eastern time display, filters, scheduled/released card states, official source links, partial-data warning, and read-only boundary.

## 6. P0/P1 Source Reliability and Timeline Clarity

- [x] 6.1 Normalize the official flag for SQLite/Postgres writes and prevent the Postgres boolean type mismatch that blocks all provider persistence.
- [x] 6.2 Replace the invalid Treasury XML address and make official-source HTTP reads bounded, retryable, and safe to report when interrupted or rejected.
- [x] 6.3 Return per-provider availability and retained-event counts; distinguish a usable retained fallback from a provider with no saved events.
- [x] 6.4 Replace raw source exception banners with a compact, readable official-source status panel while preserving the read-only timeline.
- [x] 6.5 Add regression coverage and re-verify the running API/UI against the PostgreSQL-backed service.

## 7. P0/P1 Timeline Browsing Experience

- [x] 7.1 Make the month the primary browse window while retaining a route-synchronized focused date and adjacent-day rail.
- [x] 7.2 Render month events as a continuous date-grouped timeline, with a next-event guide when the focused date has no matching event.
- [x] 7.3 Replace select-heavy filtering and the expanded provider block with compact category/state chips and an expandable source-status summary.
- [x] 7.4 Refine event-card density and responsive styles so available figures are prominent and absent figures do not create empty visual blocks.
- [x] 7.5 Add frontend coverage and verify the rebuilt desktop and narrow running page, including month navigation, date focus, filters, source detail, and read-only behavior.

## 8. P0/P1 Reference Timeline Reconciliation

- [x] 8.1 Replace the full-month browse emphasis with a bounded selected-date window and compact reference-style hierarchy.
- [x] 8.2 Render a monetary-policy decision as a primary card with persistent `公布` / `前值` / `预期` slots, and render related FOMC items as compact rows without invented data.
- [x] 8.3 Keep lifecycle filtering available while making category controls and degraded-source context visually secondary.
- [x] 8.4 Restrict BLS/BEA schedule matching to an explicit source entry and normalize the FOMC decision bundle without duplicate primary events.
- [x] 8.5 Add focused parser/UI coverage and re-verify the rebuilt API and responsive timeline route.

## 9. P0 Reference-Accurate Reading Canvas

- [x] 9.1 Constrain the timeline itself as a centered reading column at desktop widths instead of allowing its flex item to expand across the workbench.
- [x] 9.2 Give primary and related events an explicit neutral card surface, compact time gutter, and non-intrusive source affordance matching the reference hierarchy.
- [x] 9.3 Keep degraded-source detail secondary and add regression coverage for the fixed desktop canvas/card presentation.
- [x] 9.4 Make independent official-source refreshes concurrent so a slow provider cannot exceed the frontend proxy timeout, then rebuild and verify the actual route at wide and narrow viewports.

## 10. P0 Official Released Values

- [x] 10.1 Read the current BLS official data API alongside the schedule and normalize only explicitly published actual and previous values.
- [x] 10.2 Reconcile an official released observation with its scheduled timeline identity, retain the released version, and keep unsupported or absent values unavailable.
- [x] 10.3 Add focused fixtures for released BLS values and regression coverage that forecast values remain unavailable without an approved consensus source.
- [x] 10.4 Rebuild and verify the running API and timeline route show an official released figure when the source supplies one.

## 11. Cached Read and Background Refresh

- [x] 11.1 Return persisted timeline records immediately and trigger an expired official-source refresh in a guarded background worker.
- [x] 11.2 Expose background-refresh status and make the page re-read the cached timeline after a short bounded interval without blocking its first render.
- [x] 11.3 Add regression coverage for cached reads, one in-flight refresh, and the background-updated response contract.
- [x] 11.4 Rebuild and verify the running API responds from cache promptly while the timeline refreshes asynchronously.

## 12. Released-Value Retention Regression

- [x] 12.1 Prevent a later schedule-only refresh from downgrading a released or revised official event or clearing its sourced values.
- [x] 12.2 Add persistence regression coverage and verify the PostgreSQL-backed API and rendered timeline keep CPI/PPI values after a refresh.

## 13. Calendar Date-Title Reconciliation

- [x] 13.1 Correct flattened official-calendar parsing so each title is associated only with the date that precedes it.
- [x] 13.2 Remove the three confirmed stale CPI schedule records created by the old parser and verify the rebuilt timeline shows only the correct PPI/CPI dates.

## 14. Official Event Display Names

- [x] 14.1 Keep canonical official event titles unchanged while rendering consistent Chinese abbreviation-and-full-name labels for supported BLS and BEA events, including PPI.

## 15. Future Calendar Navigation and Integrity

- [x] 15.1 Add route-synchronized previous/next month controls, a calendar date picker, and a distinct today shortcut with an explicit background-sync empty state.
- [x] 15.2 Bind BLS dates and titles at the official table-cell/one-date-row level; safely reconcile only unmatched future scheduled BLS previews after a successful source read.
- [x] 15.3 Add future-calendar parser and reconciliation regressions, remove the confirmed malformed September–December BLS previews, and verify October/November browsing at runtime.

## 16. Historical Official Backfill and Clarity

- [x] 16.1 Load the prior/current official BLS calendars and align past supported releases with ordered, explicit BLS monthly observations without deriving release dates; use a source-attributed verified schedule cache when the BLS calendar is blocked.
- [x] 16.2 Reconcile malformed historical `scheduled` BLS previews only after a successful official calendar read or the verified calendar cache, retain released/revised records, retry transient BLS data reads, and add regression coverage.
- [x] 16.3 Render an explicit historical-value-verification state instead of an empty historical card, report verified-calendar-cache status, then rebuild and verify July/August runtime data.
