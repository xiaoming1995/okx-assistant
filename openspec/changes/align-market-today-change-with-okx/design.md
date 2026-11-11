## Context

The frontend currently uses one generic ticker-change helper for list cards, summary cards, sorting, and contract-selection controls.  Its baseline is `open24h`, which is a rolling 24-hour price.  The OKX app's market screen instead presents a calendar-day change for the China-market experience, producing materially different (and occasionally opposite) results for the same last price.

The raw ticker payload already carries all relevant bases: `sodUtc8`, `sodUtc0`, and `open24h`.  Backend Radar and AI report assembly deliberately use `open24h` and label the result as a 24-hour change.  They are analytics, not the market page's daily-display calculation.

## Goals / Non-Goals

**Goals:**

- Make every market-facing daily percentage use the same UTC+8 day-open baseline as the OKX app when that value is available.
- Keep a single frontend utility as the source of truth for daily change, including its sort key.
- Preserve an explicit rolling-24-hour calculation for analytics that are labelled as 24-hour data.
- Keep the UI usable when an upstream ticker omits a preferred day-open field.

**Non-Goals:**

- Changing the backend ticker endpoint, cache timing, K-line data, 24-hour high/low, volume, or market subscription source.
- Altering users' watchlists, contract selection, trading behavior, or the meaning of an explicit \"24h 涨跌\" label.
- Attempting to reconcile a screenshot captured at a different timestamp beyond aligning the calculation baseline.

## Decisions

### Model daily display and rolling 24-hour change as separate concepts

The frontend will expose a named daily-change utility whose primary base is `sodUtc8`; the existing rolling-24-hour calculation remains an explicit concept based on `open24h` for analytics.  This makes the label, calculation, and business intent reviewable instead of relying on one ambiguous `tickerChange` helper.

The alternative—changing all `open24h` consumers globally—was rejected because Radar and AI evidence would silently stop describing a rolling 24-hour movement.

### Use deterministic, valid-value fallback order

The daily utility will use the first valid non-zero base in this order: `sodUtc8`, `sodUtc0`, then `open24h`.  It will return no computed change when neither the last price nor a valid base is available.

This preserves a visible percentage for partial upstream ticker snapshots while favoring the requested OKX daily convention.  Omitting the percentage whenever `sodUtc8` is absent was rejected because it would make temporarily incomplete market rows unusable.

### Route display and sorting through the same daily utility

Contract list badges, market summary price movement, picker rows, and any sort named or presented as a daily change will all consume the daily utility.  The sort uses the same numeric percentage the user sees, preventing a list order that contradicts the displayed movement.

Creating separate calculations in individual components was rejected because future styling changes could reintroduce inconsistent values.

### Preserve backend 24-hour analytics without payload changes

Radar and AI report paths will continue to derive their explicitly labelled `change24h` values from `open24h`.  No field is removed or transformed in `/api/tickers`; the frontend selects the appropriate ticker field for its daily-display concern.

Adding a second backend endpoint was rejected because it would duplicate data already present in the ticker response and create unnecessary cache/API compatibility risk.

## Risks / Trade-offs

- [An upstream ticker does not include `sodUtc8`] → Use the documented fallback order and cover every branch with deterministic tests.
- [A later UI reuses the wrong helper] → Use names that state the period, centralize calculation, and add consumer/sort regression tests.
- [Users interpret a fallback as an exact UTC+8 day change] → Prefer the intended value whenever available; retain existing data-source status messaging and do not claim a different baseline in the UI.
- [A broad refactor changes true-24-hour analytics] → Add focused regression coverage confirming Radar and AI retain `open24h` semantics.

## Migration Plan

1. Introduce and test the separate calculation utilities.
2. Switch market-facing daily-display and daily-sort consumers to the UTC+8 utility.
3. Verify explicit 24-hour analytics still use `open24h`.
4. Build the frontend and compare known contracts against the OKX market view at the same observation time.

The change is frontend-compatible and requires no migration.  If a production discrepancy is observed, rollback consists of restoring the previous daily utility wiring; raw tickers and backend analytics remain unchanged.

## Open Questions

- None for the initial change.  A future product decision can add an explicit visual indication when fallback data is being used, but it is not required to align the normal OKX ticker path.
