## Context

Contract Radar currently uses ticker `volCcyQuote24h` to select a bounded set of liquid candidates, then fetches 15-minute candles and ranks final rows by `playable`, opportunity, liquidity score, and volatility. The visible ranking consequently is not a turnover ranking, while the frontend always requests `bar=15m`; the latter is a volatility-analysis period rather than an explicit one-hour turnover choice.

OKX candle rows already persist the quote-volume field needed to calculate a comparable short-window turnover. The product must remain a public-market, read-only decision-support surface: raw activity ranking must not convert into a buy/sell recommendation, bypass the existing minimum-volume filter, or let the optional AI analysis mutate the ranking.

## Goals / Non-Goals

**Goals:**

- Make one-hour quote turnover, descending, the default deterministic candidate-list order.
- Allow an explicit switch between one-hour and twenty-four-hour quote-turnover order.
- Derive and expose an auditable one-hour value from completed 15-minute candles, including availability and comparability metadata.
- Preserve the current filters, entry assessment, risk/tradability labels, manual AI flow, cache fallback behavior, and contract handoffs.
- Keep desktop and narrow layouts, loading, cached/error, keyboard-focus, selection, and disabled states consistent with the frontend design guidelines.

**Non-Goals:**

- Do not turn radar results into trading instructions, send orders, or change automation settings.
- Do not use private account, position, order-book, or LLM-generated data for ranking.
- Do not claim that a bounded-candidate scan is an all-market one-hour volume leaderboard.
- Do not add a historical radar database, a database migration, or background polling beyond the existing scan/candle refresh path.

## Decisions

### Default to a named turnover sort mode

Add a normalized radar request sort key with `turnover_1h` as its default and `turnover_24h` as the only alternative. The resolved key is returned with the scan filters and sort metadata, is included in the radar scan and manual AI-analysis cache identities, and is used by the frontend's selected state.

The result list is ordered by the chosen comparable turnover value descending. Records without a valid value for the selected window follow comparable records and retain a stable deterministic tiebreaker (24-hour comparable turnover, then contract ID). Existing opportunity, risk, tradability, and entry-assessment values remain visible explanatory data; they do not silently override the chosen turnover order.

Alternative considered: retain `playable > opportunity` as a prefix before turnover. This would preserve the old safety grouping but violate the visible promise of a descending turnover ranking, so it is rejected. Safety stays in the live-instrument filter, minimum-24-hour-turnover candidate screen, explicit labels, and warnings.

### Calculate one-hour turnover only from four completed 15-minute quote-volume candles

For each bounded candidate, derive `turnover1h` from the most recent four confirmed 15-minute candles. Sum `volumeQuote` only when all four rows are confirmed, positive, and use the same comparable quote denomination expected for that result. Persisted candle rows and fresh OKX rows use the same calculation.

The in-progress candle is excluded so a ranking does not change merely because a candle is partially formed. If fewer than four completed rows, a missing/non-positive quote volume, or an incomparable unit prevents calculation, return an unavailable turnover descriptor and a concise Chinese explanation rather than estimating it from contract count or base-coin volume.

Alternative considered: use the current unfinished 1-hour candle. It is cheaper to explain but changes continuously and is not comparable with a completed hour, so it is rejected. Alternative considered: infer one-hour turnover from `volCcyQuote24h / 24`; it invents a short-window value and is rejected.

### Retain the existing bounded 24-hour liquid candidate screen and disclose it

The scan continues to first apply settlement, live-state, and minimum 24-hour turnover filters and then restrict candle reads to `candidateLimit` contracts selected by 24-hour comparable turnover. One-hour order is therefore a ranking of the screened candidate pool, not a full-universe real-time ranking. The response summary and UI explain this scope using the current candidate and total counts.

Alternative considered: request 15-minute candles for every listed SWAP contract to make a global one-hour leaderboard. This increases public API work and failure/rate-limit exposure substantially, while the radar's current bounded high-liquidity candidate model is intentional; it is rejected for this change.

### Build both turnover rankings from each manual scan

Each manual scan prepares both `turnover_1h` and `turnover_24h` Top lists from the same screened candidate pool and K-line snapshot. The twenty-four-hour ordering remains based on current normalized ticker turnover; the one-hour ordering always uses four completed comparable 15-minute quote-turnover candles. This deliberately makes the one-hour data requirement part of every manual scan, so a later local window switch never substitutes a partial subset for a real ranking.

Necessary public K-line reads use a bounded primary worker pool. Items that exhaust the client's existing retry policy receive one lower-concurrency recovery attempt; only items that still fail fall back to local data and produce the compact aggregate warning. Server logs retain limited contract/error context for diagnosis, while the UI continues to show only the Chinese availability state.

Alternative considered: lazily request the other window only on its first switch. This still makes the control feel slow and returns to the competing-scan problem, so it is rejected. Alternative considered: locally sort only the visible active Top list. That can omit candidates that belong in the other window's Top list and is rejected. Hiding a warning once any cache exists and retrying every candidate indefinitely are also rejected for the existing data-credibility and bounded-work reasons.

### Separate structural risk from the current market condition

`riskLevel` is renamed in user-facing copy to `结构风险`, because it is a deterministic gate for liquidity comparability, live state, K-line sufficiency, and extreme range rather than a prediction that a trade is safe. The numeric risk penalty and filter continue to use that same narrow, auditable definition.

Each result also exposes a market-condition descriptor derived from completed recent candles: `横盘震荡` when the recent net price displacement is small relative to its traded range, `趋势运行` when the displacement occupies a material portion of that range, `高波动` for an expanded range, and `方向待确认` when evidence is insufficient or mixed. A range condition adds a concise direction-risk notice: avoid treating a low structural-risk label as confirmation to chase a breakout; wait for volume and candle-close confirmation.

The compact list remains scan-friendly, so the detailed workbench surfaces the explicit market-condition tag and the structure-risk wording, with the diagnostic sentence in the existing progressive-disclosure risk area. This preserves the simple-tool layout and does not add trade directions, automation, or a market-wide forecast.

Alternative considered: increase every sideways candidate's structural risk penalty. That would conflate an observable market condition with data, liquidity, or extreme-move risk, make the existing risk filter ambiguous, and hide the different reason an entry may be poor. It is rejected in favor of two independently readable labels.

### Make initial radar scans visibly active without blanking retained results

The first manual scan has no safe prior result to retain, so both the candidate list and selected-detail workspace use the shared accessible loading spinner and low-motion skeleton lines. The list skeleton follows compact table-row density; the detail skeleton follows the existing four-metric and assessment hierarchy. The toolbar reports `正在扫描合约` and its scan action remains disabled to prevent duplicate work.

When a complete payload exists, refresh behavior remains intentionally different: retain the current list and selected contract, and use the existing compact status wording rather than replacing content with skeletons. The no-scan state becomes a concise instruction panel rather than unexplained large whitespace. The implementation reuses shared loading primitives, current spacing tokens, and reduced-motion behavior.

### Keep row semantics and interaction explicit

The compact Radar controls gain a single named sort selector with `1小时成交额` and `24小时成交额`; `1小时成交额` is selected on first render. The candidate-table header, row metric, selected detail view, and scan status identify the active sort window and amount rather than presenting the old ambiguous “流动性” column. The control is keyboard operable, reports its selected state, has visible focus feedback, and is disabled only while a manual scan is active. When both rankings are present, a sort switch immediately selects the corresponding local Top list and never starts a request; no automatic AI analysis occurs.

The implementation reuses existing compact controls and semantic status styles. It does not introduce new visual tokens, card patterns, or animation language.

### Make the scanned workbench readable in one desktop viewport

At desktop widths, the sort selector must reserve sufficient horizontal space for both turnover labels so it never wraps itself into a second line. The warning and waiting-for-AI states remain visible but become single compact feedback rows. The selected-contract view continues to show the contract, opportunity score, four decision metrics, scope, entry assessment, tags, and handoff actions immediately; explanatory reasons and risk prose move into a native, keyboard-operable disclosure that starts collapsed. This preserves safety context without forcing users to scroll before they can compare the ranked list and act on the selected contract.

At intermediate widths the controls use deliberate tool rows rather than clipping or internally wrapping the turnover selector. At narrow widths they return to the existing natural single-column document flow, where no status or core action is hidden.

### Treat a turnover switch as local snapshot selection

Selecting a different turnover window must immediately replace the displayed rows with the matching Top list from the same complete scan snapshot; it must not request K lines, refetch Radar, or show a loading state. The active sort metadata, table header, row amounts, selected-contract metric, and selection all change together. Switching invalidates any manual AI conclusion displayed for the former leader set but never triggers new AI work automatically.

If the draft settlement, minimum turnover, volatility, or structural-risk controls differ from the scan snapshot, the toolbar explicitly says that those changes take effect only after “重新扫描”. Window selection still remains local to the last complete snapshot. Legacy or degraded payloads that do not contain both Top lists never fabricate a local ranking; they request one manual rescan to enable the control.

### Preserve one dual-ranking scan snapshot safely

Normalize legacy cached radar payloads that do not contain both turnover rankings so the UI shows a clear “重新扫描以启用双口径排行” state rather than inventing a default value. A current complete payload stays visible while a forced refresh is in progress. The scan-cache identity covers the material screening and candle parameters rather than display sort, while the manual-AI cache identity additionally includes the selected window and leaders. An upstream candle refresh failure may use available cached candles only when its four-row completed-window calculation is valid; otherwise the result is marked unavailable.

### Filter a completed snapshot locally without changing scan criteria

Keep the existing settlement, minimum 24-hour turnover, volatility, and structural-risk toolbar inputs as **next-scan conditions**. Add a compact `结果筛选` disclosure to the completed candidate-panel header for `波动` and `最小 24h 成交额`; it starts collapsed so the scan toolbar is not visually duplicated. These values are deliberately separate state so changing them never changes the request parameters or creates a scan.

The local volume threshold uses the normalized comparable 24-hour quote-turnover value already shown for each candidate. It only narrows the current selected turnover ranking and never attempts to recover rows outside the bounded candidate snapshot. The list header reports visible rows over the current snapshot total and adds `已筛选` while a local value is active; if no row matches, both panels explain that the local result filter is responsible and offer one clear `清除结果筛选` action. A turnover-window switch continues to choose the other locally held ranking first, then applies the same local result filter.

Alternative considered: reuse the existing scan-condition inputs for local filtering after a scan. That would make it unclear whether a user had changed the next scan or the current displayed result, and lowering a server-side candidate threshold cannot restore unscanned contracts. A permanently expanded second filtering row is also rejected because it repeats the same two concepts in the first viewport. The chosen disclosure keeps the two scopes distinct without making routine scans visually noisy.

## Risks / Trade-offs

- [One-hour activity can be noisy] → Keep entry assessment, volatility, risk, and tradability labels visible and explicitly describe ranking as activity, not a recommendation.
- [A candidate can lack four usable closed candles] → Place it after comparable results and show a Chinese data limitation instead of a fabricated amount.
- [The candidate pool is not the full market] → Preserve and surface bounded-pool counts and wording; do not call it a market-wide leaderboard.
- [Additional fields can invalidate cache expectations] → Version/normalize the response and include the resolved sort key in cache identity.
- [A narrow control bar can wrap poorly] → Use the existing compact responsive control patterns and verify 1201px+, 768–1200px, and <=767px layouts.
- [A local filter may be mistaken for a market-wide search] → State that it is a `本次扫描结果` filter, preserve the bounded-candidate scope, and provide visible/total counts.

## Migration Plan

1. Add request/result normalization and cache-key isolation while keeping old snapshot fallback readable.
2. Implement the deterministic 1-hour aggregation and requested turnover sort, with backend tests before UI wiring.
3. Update the Radar control and result labels, then validate loading, cache/error, focus, disabled, desktop, and narrow states against the live endpoint.
4. Deploy with the current short radar cache TTL. Roll back by restoring the previous default sort while leaving the new fields optional; existing snapshots and the manual AI endpoint remain usable.

## Open Questions

- None for the first change: the confirmed default is `1小时成交额`, and the sole alternative is `24小时成交额`.
