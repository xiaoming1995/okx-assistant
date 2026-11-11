## Context

The completed market-chart workbench separates the market summary, operational status, contextual candle inspector, candlestick pane, and volume pane. `MarketPage` nevertheless renders an additional gray `status` paragraph under its title. That state is reassigned for routine ticker, candle, connection, and list-refresh events, so it changes far more frequently than a user needs to be notified.

The public candle sender currently emits the latest local cache immediately, then a 200-row REST seed, and later cached rows updated from the WebSocket. Consumers draw each received array directly. The storage query returns ordered rows, but neither the sender nor the client asserts valid timestamps, duplicate removal, interval continuity, or freshness before treating a seed as a complete trend. An interrupted or old cache can therefore briefly become the chart's full viewport.

The existing chart retains 200 candles and calls `fitContent()` only for initial or changed chart context. This preserves manual historical navigation, but a full-range fit can make ordinary movement unreadable when a distant move dominates the scale.

## Goals / Non-Goals

**Goals:**

- Remove the routine-changing gray subtitle without concealing source, fallback, freshness, or warning information.
- Make the initial chart data deterministic, ordered, unique, appropriately fresh, and visibly degraded when a trustworthy current snapshot is unavailable.
- Focus the initial camera on a recent bounded candle window while retaining the loaded history for pan and zoom.
- Give users an explicit, predictable way to return to the newest focused window.
- Keep candle inspection readable at supported desktop dimensions.

**Non-Goals:**

- Do not add technical indicators, forecasts, trading recommendations, order entry, or a new market-data provider.
- Do not remove the existing 200-candle historical buffer, supported bar periods, volume pane, manual-history preservation rule, or TradingView attribution link.
- Do not change the public REST response contract or introduce persistent user chart preferences in this iteration.

## Decisions

### 1. Remove routine status copy; preserve actionable status where it belongs

The market-chart header will no longer render the generic `status` paragraph. The existing source/freshness pills remain the compact operational indication, while warnings and degraded-data explanations use the notice surface. This separates normal expected realtime events from user-actionable exceptions.

Alternative considered: throttle or animate the subtitle. This still leaves redundant moving copy in the visual hierarchy and cannot make a normal status meaningful.

### 2. Use one candle-batch normalization and suitability check at the realtime boundary

The backend will normalize every cache, REST, and WebSocket-derived batch before persistence or fan-out: retain finite positive timestamps, sort ascending, de-duplicate by timestamp, and use the known bar duration to evaluate internal gaps and recency. A cache batch is suitable as a fast initial seed only if it is continuous within a bounded bar tolerance and recent enough for the selected interval.

An unsuitable cache will not be announced as a normal complete seed. The sender will attempt the REST seed; if no current seed can be obtained, it will expose the normalized persisted data only with an explicit degraded source and warning. The frontend repeats lightweight ordering/de-duplication defensively before assigning chart state, so a malformed transport payload cannot distort the time scale.

Alternative considered: delete all cache-first delivery. That avoids bad first paint but gives up fast offline/fallback behavior and makes a temporary provider failure unnecessarily empty.

### 3. Keep all retained history but focus the camera on the latest 80 candles

After data is loaded for a new contract or period, the chart will retain its complete normalized buffer but set a logical visible range around the newest 80 candles, with a small right-edge margin. The bounded count is deliberately period-independent: it produces a legible recent segment for each supported resolution without needing extra API requests. The user can pan or zoom into the rest of the retained history.

A visible `最新` action will reuse the same camera calculation. It only changes the time-scale viewport; it does not fetch data, reset the selected contract or bar, or alter the inspector semantics.

Alternative considered: replace the candle buffer with only the latest 80 rows. This would make the chart readable but would regress historical inspection and the existing user-controlled navigation behavior.

### 4. Make the inspector primary values compact, with secondary values available on demand

The inspector will continue to follow the crosshair-selected candle or newest candle. Its primary reading line will prioritize timestamp, OHLC, signed candle movement, and volume. Amplitude and quote turnover remain available through a compact secondary disclosure or contextual detail instead of competing for fixed horizontal space.

Alternative considered: remove candle detail entirely. That would create more plot room but make exact readings dependent on a visually harder-to-use axis and crosshair alone.

### 5. Preserve established chart and attribution behavior

The volume pane remains synchronized below the dominant price pane. Existing historical-view protection remains intact: updates auto-follow only at the newest edge, and a historical view remains in place until the user uses `最新` or returns to that edge. The header TradingView link remains present and the plot attribution logo stays disabled.

## Risks / Trade-offs

- [A newly listed or thinly traded instrument has fewer candles] → Permit a short but ordered batch; do not label a small history as a gap merely because it lacks 80 rows.
- [Exchange candle timestamps can be delayed around a connection loss] → Use a documented interval-specific freshness tolerance and show degraded source/warning rather than silently replacing good history with a partial set.
- [Recent focus can surprise users expecting a full timeline] → Keep all 200 rows pannable and provide a clear `最新` action rather than a hidden camera mode.
- [A compact inspector can hide useful figures] → Preserve the existing values in contextual secondary detail and test both latest and historical crosshair states.
- [Data normalization differs between REST and WebSocket] → Share backend normalization before both persistence and send, then keep the frontend guard limited to transport safety.

## Migration Plan

1. Add focused unit tests for normalized rows, duplicates, gap/freshness classification, cache-seed selection, and degraded fallback payloads.
2. Update realtime candle sender and frontend chart state/camera controls without changing external API routes or database schema.
3. Add focused frontend static coverage, run backend and frontend tests/build, and verify fresh load, cache degradation, period change, manual history, and `最新` behavior in a browser.
4. Roll back by reverting the frontend and realtime sender changes; cache data remains compatible and no migration is required.

## Open Questions

- None. The initial implementation will use the proposed 80-candle recent window and make bar-duration freshness tolerances explicit in tests.
