## Context

The current market AI flow builds a small in-memory macro snapshot at analysis time. It currently reads BLS CPI evidence and a Federal Reserve FOMC calendar, then combines those facts with selected-contract ticker and multi-period candles. The dedicated AI page is explicitly manual and read-only. The frontend already has hash-based market subroutes, but there is no durable event history, calendar page, event lifecycle, or source-normalized API.

The requested timeline is intended to become evidence for future LLM reading of news and K-lines. That requires distinguishing an official future release from a released value, keeping the original source and time zone, and preserving revisions. It must not turn incomplete official calendars into a claim that the system knows every U.S. event or every market consensus forecast.

## Goals / Non-Goals

**Goals:**

- Provide a read-only, source-attributed timeline of high-impact U.S. market events under the market section.
- Start with an official, bounded source set: Fed monetary-policy calendar; selected BLS inflation/employment releases; selected BEA growth, consumption, and trade releases; and Treasury auction events only when the official schedule can be normalized reliably.
- Persist scheduled and released records, including revisions and the provenance needed to replay later event context.
- Render a date-first mobile-friendly timeline that defaults to Asia/Shanghai while always retaining the original `America/New_York` time context.
- Establish a normalized event contract usable by later AI evidence assembly without changing the current AI-outlook request or prompt.

**Non-Goals:**

- Do not claim to aggregate all U.S. affairs, social-media posts, media headlines, political rumors, or global news.
- Do not add a paid/general real-time news provider, consensus/forecast provider, alert delivery, scheduled background worker, or automatic LLM execution.
- Do not infer causal market impact, submit orders, pre-fill order tickets, alter automation, or present trading signals.
- Do not change the existing `/api/market/ai-outlook` payload in this change.

## Decisions

### 1. Treat the timeline as an independent market context page

Add a market secondary route such as `#/market/us-timeline?date=YYYY-MM-DD`. It has its own full-width timeline rather than the selected-contract rail: an economic event is market-wide, and a permanently mounted contract list would crowd the date/card workflow shown in the reference. The selected contract continues to belong to the chart, AI-outlook, and statistics workbench.

The timeline defaults its display date and clock to `Asia/Shanghai`, labels the rendered time accordingly, and retains each event's official `America/New_York` source time in the card/detail. This removes ambiguity during U.S. daylight-saving changes.

Alternative considered: make the timeline another pane in the AI page. That hides scheduled events until the user starts an analysis and makes date browsing too constrained.

### 2. Persist a canonical event record plus immutable observed versions

Add a `market_events` record keyed by `(provider, provider_event_key)` and a `market_event_versions` record for each observed source state. The canonical record contains:

- identity and classification: provider, provider key, title, category (`monetary`, `inflation`, `employment`, `growth`, `consumption`, `trade`, `treasury`), importance, and state;
- time: `scheduled_at` in UTC, `source_timezone`, `published_at` when known, and `fetched_at`;
- figures: `actual`, `forecast`, `previous`, `revision`, `unit`, and `period_label` as nullable strings;
- provenance: official/source flag, source URL, compact source summary, and payload hash.

The version table stores the normalized fields and observed time whenever a provider changes a record. A released official value updates the canonical event but does not erase the scheduled version; a changed published value becomes `revised`. SQLite and Postgres implementations receive the same unique key and date/state indexes.

Alternative considered: keep only the current in-memory macro cache. It cannot support date navigation, restart survival, corrections, or later historical K-line comparison.

### 3. Use adapters for official schedules, and never fabricate unavailable figures

Each provider adapter returns normalized candidate events plus refresh warnings. The initial adapters are intentionally narrow:

- Federal Reserve: FOMC meeting, decision/statement, press conference, minutes, and SEP context where the official calendar identifies it.
- BLS: CPI, PPI, Employment Situation, JOLTS, and other explicitly selected high-impact release-calendar entries.
- BEA: GDP, Personal Income and Outlays/PCE, and International Trade release entries.
- Treasury: announced/auction/settlement events only when a stable official schedule parse provides all required dates.

Official sources do not generally provide a market-consensus forecast. `forecast` therefore stays null until an explicitly approved forecast provider is introduced; the UI says `暂无已验证预期` rather than displaying a calculated or LLM-generated number. Similarly, failed parsing must leave an event partial with a warning, not invent an exact release time or actual value.

Alternative considered: ask the LLM to fill event fields from general knowledge. That would make the later AI evidence chain unverifiable and time-sensitive facts unreliable.

### 4. Refresh lazily with bounded caching and clear fallback state

The read API obtains a normalized event window from persistence and refreshes a provider only when its provider cache is expired or when no usable record exists. Refreshes have provider-specific TTLs; a short TTL is used near a scheduled release, while historical records are retained. If a provider request fails, the response returns the latest persisted records with source/freshness warning metadata. If no record exists, it returns an empty partial result for that provider rather than failing the whole timeline.

No public write/refresh endpoint is required for the first page. The application remains usable without a daemon; a page/API request is a valid refresh opportunity. A future worker can call the same service layer without changing the data contract.

Alternative considered: refresh every provider for every page visit. That creates avoidable provider load and makes the UI fragile during outages.

### 5. Provide a bounded, read-only browse API

Add:

- `GET /api/market/us-events?from=YYYY-MM-DD&to=YYYY-MM-DD&categories=...&states=...`
- `GET /api/market/us-events/{eventId}`

Date ranges are validated and bounded (for example, a maximum 31-day window), categories/states use an allow-list, results are ordered by scheduled time, and responses include `source`, `generatedAt`, `cacheAgeMs`, and deduplicated warnings. Event detail includes the current canonical values and chronological versions/provenance.

Alternative considered: expose provider-shaped payloads directly. It would force the UI and a future LLM to understand different calendars and makes later provider substitution risky.

### 6. Design cards around facts, status, and later replay rather than predictions

The page renders a date header and consecutive date rail, category filters (`全部`, `货币政策`, `通胀`, `就业`, `增长`, `消费`, `贸易`, `美债`), and date-grouped event cards. A scheduled card shows event time, source, importance, prior/forecast fields when available, and state. A released/revised card adds actual and revision values. Each card exposes a source link and freshness/error context.

The timeline does not calculate or display a causal market conclusion. The persisted event identity and UTC timestamp are sufficient for a future event-evidence service to retrieve a fixed before/after candle window, which will be labeled as price facts rather than event causation.

Alternative considered: put an AI direction or buy/sell tag on every card. That conflates calendar data with trading advice and violates the current read-only boundary.

## Risks / Trade-offs

- [Official calendars change HTML/PDF structure or release times] → Isolate provider parsers, retain source URLs and old persisted records, show parser/freshness warnings, and test captured source fixtures.
- [A single scheduled release produces several artifacts] → Model related entries with stable provider keys and distinguish meeting, statement, press conference, and minutes instead of collapsing them into one ambiguous event.
- [Forecasts are absent from official data] → Keep the field explicitly unavailable until a separately approved, attributed forecast source exists.
- [Time-zone conversion is wrong around DST] → Store UTC as the canonical time, retain the original source zone, and test known EDT/EST boundary dates.
- [A source outage leaves no current records] → Return partial provider state and never substitute stale facts without a visible age/warning.
- [Users read price movement as proof of causality] → Use factual labels for any later candle window and retain the existing observation-only wording.

## Migration Plan

1. Add database tables, indexes, and repository methods without touching existing market or AI records.
2. Implement adapters and normalization with fixtures, then backfill a bounded date window on the first browse request.
3. Add the read API and its cache/fallback metadata.
4. Add the route/tab, desktop and narrow timeline layouts, card states, and source links.
5. Validate lifecycle transitions, time zones, API input bounds, source failures, and read-only UI behavior.
6. Roll back by removing the market tab/route and event API. The new tables may remain unused; existing chart, AI, trading, and automation flows remain unaffected.

## Open Questions

- Which market-consensus provider, license, and latency requirement should govern the future `forecast` field?
- Should Treasury auctions be included in the initial release only after a stable structured source is confirmed, or be deferred entirely?
- What event importance rubric should be used beyond the initial source-curated high-impact set?
- When a later real-time news provider is chosen, what source-rating and retention policy will decide whether an item enters the LLM evidence set?
