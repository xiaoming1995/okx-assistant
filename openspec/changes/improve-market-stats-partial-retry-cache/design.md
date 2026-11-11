## Context

The trading data page loads three OKX statistics series for the selected SWAP contract: long/short account ratio, taker buy/sell volume, and open interest history. These metrics are independent public endpoints. A transient `IncompleteRead(0 bytes read)` on one endpoint currently produces a partial payload with empty data for that metric while the successful metrics remain visible.

## Goals / Non-Goals

**Goals:**
- Preserve successful metrics when a sibling metric request fails.
- Prefer the last successful metric data for the same contract, period, and limit instead of showing an empty metric.
- Make partial data status explicit enough that users understand what is current and what is cached.
- Let users retry the stats request directly from the panel.

**Non-Goals:**
- Do not change OKX API credentials, endpoint selection, or add third-party data sources.
- Do not turn trading-stat observations into direct trading advice.
- Do not introduce persistent storage for trading statistics.

## Decisions

1. Add an in-memory per-metric cache keyed by `instId`, effective `period`, `limit`, and metric key.
   - Rationale: metric failures are independent, and the user experience should not lose good prior data for only one failing endpoint.
   - Alternative considered: cache only the whole combined payload. This already exists but cannot help when the current refresh partially succeeds with one metric missing.

2. Keep `force=true` as a network refresh while still allowing stale per-metric fallback on failures.
   - Rationale: users expect retry to hit OKX again, but a transient repeat failure should still avoid a blank metric if useful prior data exists.
   - Alternative considered: make force bypass every cache. That gives a stricter diagnostic result but makes the UI less usable during public endpoint instability.

3. Return metric-specific warning text instead of a generic unavailable message.
   - Rationale: the UI can show exactly which statistic failed and whether cached data is being displayed.
   - Alternative considered: hide warnings when cached fallback exists. That would make the panel look current when one metric is stale.

4. Increase only the short retry backoff for incomplete or disconnected responses.
   - Rationale: the failure observed was an empty incomplete response after quick retries; a slightly longer backoff improves recovery without making the page feel stuck.

## Risks / Trade-offs

- Stale metric data can be mistaken for fresh data -> warning text explicitly says the metric is showing the last cached data.
- In-memory cache is lost on backend restart -> acceptable because this is a runtime resilience feature, not historical storage.
- Longer retry backoff can add latency on repeated failures -> bounded to three attempts and only affects failed OKX requests.
