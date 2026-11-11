## 1. Radar request and turnover data contract

- [x] 1.1 Add and validate the normalized `turnover_1h` and `turnover_24h` radar sort keys, with `turnover_1h` as the API default and cache-key input.
- [x] 1.2 Define result and snapshot metadata for active sort mode, readable sort label, one-hour turnover availability, value, unit, candle count, and limitation warning while retaining legacy-payload fallback.
- [x] 1.3 Implement deterministic completed-one-hour quote-turnover aggregation from the latest four confirmed 15-minute candles, rejecting incomplete or incomparable data without estimation.
- [x] 1.4 Apply the requested comparable-turnover descending order with deterministic tie breaking, preserve existing filters/assessment fields, and disclose the bounded 24-hour-screened candidate scope.
- [x] 1.5 Keep manual AI analysis bound to the selected scan context and verify it cannot alter turnover ordering or trading state.

## 2. Backend validation

- [x] 2.1 Add focused radar tests for the default one-hour aggregation, exclusion of an unfinished candle, incomplete/non-comparable short-window data, and stable tie breaking.
- [x] 2.2 Add focused radar tests for explicit twenty-four-hour ordering, separate sort-mode cache snapshots, legacy cache normalization, and bounded-candidate scope metadata.
- [x] 2.3 Run the radar backend test suite and confirm existing entry-assessment, risk/tradability, and AI non-mutation behavior remain intact.

## 3. Contract Radar interaction

- [x] 3.1 Add the compact `1小时成交额` / `24小时成交额` selector, default selected state, request wiring, disabled scan state, keyboard operation, and visible focus feedback using existing frontend design tokens.
- [x] 3.2 Update the candidate-list header, row amount, selected-contract metrics, and status/scope wording to identify the active turnover window and bounded candidate pool without hiding risk, tradability, or entry-assessment labels.
- [x] 3.3 Render unavailable or legacy short-window data as a clear Chinese rescan/data-limitation state while preserving last complete scan data during refresh.
- [x] 3.4 Add or update frontend static/unit coverage for the two sort modes, semantic labels, accessible selected/disabled states, and the continued manual-only AI analysis flow.

## 4. End-to-end verification

- [x] 4.1 Run the relevant frontend test suite and production build, documenting unrelated pre-existing failures separately if any occur.
- [x] 4.2 Verify the live API default and explicit twenty-four-hour responses: amount order, result sort metadata, candidate-pool scope, cached response, and forced-refresh fallback.
- [x] 4.3 Verify Contract Radar at desktop, 768–1200px, and <=767px widths, including initial loading, retained-data refresh, empty/error or cache state, mouse/keyboard focus, and disabled sort control state.
- [x] 4.4 Verify the manual-AI request context for each sort mode through deterministic analysis-cache and non-mutation tests, confirming ranking and selected-contract handoff state remain unchanged without making an unrequested live model call.

## 5. Radar first-viewport density

- [x] 5.1 Keep the desktop ranking selector on one tool row, compact warning/AI-waiting feedback, and intentionally reflow controls at intermediate widths without creating a new visual language.
- [x] 5.2 Keep selected-contract key metrics, entry assessment, tags, and handoff actions in the compact detail view; progressively disclose secondary reasons and risks with a keyboard-operable native details control.
- [x] 5.3 Add static coverage and verify the scanned workbench at desktop and narrow widths, including the expanded and collapsed explanation state.

## 6. Turnover switch refresh behavior

- [x] 6.1 Trigger a radar request with the newly selected sort key on turnover-window selection; preserve prior complete data while the request is active and restore the resolved prior selection after a switch failure.
- [x] 6.2 Add static coverage for immediate sort-switch request wiring and explicit retained-result updating text.
- [x] 6.3 Verify a completed one-hour scan can switch to a completed twenty-four-hour scan, updating selected control, status, candidate ordering/header, and selected-contract metric.

## 7. K-line refresh resilience

- [x] 7.1 Reuse sufficient persisted K-line history for twenty-four-hour turnover scans when only the unselected one-hour quote-turnover field is unavailable; preserve the explicit unavailable state rather than estimating it.
- [x] 7.2 Bound primary K-line refresh concurrency, run one lower-concurrency recovery pass only for failed candidates, and retain compact user-facing fallback wording with server-side diagnostic context.
- [x] 7.3 Add focused tests and verify a live forced twenty-four-hour scan no longer creates avoidable K-line refresh warnings while a transient retry recovery does not surface a warning.

## 8. Structure risk and market condition

- [x] 8.1 Add deterministic recent-candle market-condition metadata that identifies sideways range, trend, high-volatility, or mixed/insufficient evidence without changing structure-risk penalties or ranking.
- [x] 8.2 Rename the user-facing risk filter, labels, and selected-contract metric to `结构风险`; show the independent market-condition label and its sideways direction-risk note in the compact detail flow.
- [x] 8.3 Add backend and frontend coverage, then verify the rendered desktop and narrow Contract Radar states, including the `横盘震荡` explanatory state and existing risk filter behavior.

## 9. Radar loading feedback and empty-workspace polish

- [x] 9.1 Add compact, accessible initial-scan skeletons for the candidate list and selected-detail workspace using the shared loading primitives and reduced-motion behavior.
- [x] 9.2 Keep retained scan results visible during refresh, show a local Chinese updating state, and replace the pre-scan blank detail area with a concise instruction state.
- [x] 9.3 Add frontend coverage and verify desktop plus narrow loading, retained refresh, disabled scan action, and no-scan empty states.

## 10. Dual-ranking local turnover switch

- [x] 10.1 Return accurate one-hour and twenty-four-hour bounded Top lists from every manual Radar scan, share the scan snapshot across display modes, and keep manual AI cache identity tied to the selected leader context.
- [x] 10.2 Replace turnover-switch request wiring with local snapshot selection; keep active sort, selection, metric labels, and concise status synchronized, invalidate stale manual AI text, and flag draft filters that still require a manual rescan.
- [x] 10.3 Add backend and frontend coverage for dual rankings, shared cache behavior, no-fetch local switching, legacy fallback, keyboard/focus/disabled states, and verify desktop plus narrow browser interactions.

## 11. Completed-snapshot result filters

- [x] 11.1 Add separate local result-filter state for volatility and minimum comparable 24-hour turnover; apply it to the active locally held ranking and selection without changing Radar request parameters.
- [x] 11.2 Render the compact `结果筛选` controls, visible/total scope, clear action, and concise no-match list/detail states using existing simple-tool tokens and responsive layouts.
- [x] 11.3 Add static coverage and verify desktop plus narrow browser interactions for local filtering, clear/focus/empty feedback, and the absence of an additional scan request.

## 12. Result-filter visual de-duplication

- [x] 12.1 Replace the permanently visible candidate-panel result-filter row with a compact, keyboard-operable panel-header disclosure while keeping local-filter semantics unchanged.
- [x] 12.2 Show active filtering through concise count/status feedback, clarify the next-scan toolbar label, and retain the empty-state clear action without reintroducing duplicate controls.
- [x] 12.3 Add static coverage and verify the default, expanded, active, empty, keyboard-focus, desktop, and narrow states.
