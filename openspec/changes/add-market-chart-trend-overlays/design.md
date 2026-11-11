## Context

The market page uses `lightweight-charts` v5.2.0 with one candlestick series and one synchronized volume histogram. The completed readability change validates candle batches and preserves 200 loaded candles, but places the initial camera on the newest 80 candles. It intentionally excluded technical indicators, so users still have no visual reference for short-, medium-, and longer-period direction.

The supplied reference uses a compact, familiar trading-chart vocabulary: MA5/MA10/MA20 overlays with a same-color legend, a dashed current-price anchor, high/low annotations, and a bounded number of visible candles. The desktop workbench already has the current-price label, volume pane, time scale, crosshair inspector, degradation notices, and manual-history protection; this change extends those surfaces rather than recreating a mobile trading terminal.

## Goals / Non-Goals

**Goals:**

- Make recent price direction and turns readable at a glance through default MA5, MA10, and MA20 overlays.
- Keep the price pane focused enough for candle bodies, wicks, and volume relationships to remain legible.
- Explain the active candle and visible price range without changing the chart into a trading-signal surface.
- Preserve current read-only data, realtime-navigation, attribution, and responsive-layout behavior.

**Non-Goals:**

- Do not add RSI, MACD, Bollinger bands, strategy signals, forecasts, buy/sell recommendations, or order-entry controls.
- Do not add a data-provider, API endpoint, database schema, persistent user preference, or third-party dependency.
- Do not discard the existing historical buffer or force a realtime jump while a user is inspecting history.

## Decisions

### 1. Use deterministic simple moving averages computed from the retained candle buffer

MA5, MA10, and MA20 will be calculated locally from each candle close after candle normalization. Each line begins only once its period has enough valid closing prices. The full retained history is used in the calculation before the camera chooses its visible subset, so the first visible MA value has the correct preceding context. The price-pane line series use yellow (`#e5a823`), rose (`#d34b78`), and cyan (`#32afbf`) respectively, with no separate price scale, price line, or last-value marker that could compete with the active price.

Alternative considered: request precomputed indicator values from the backend. That introduces a new contract and makes a purely derived, presentation-only value harder to audit. Alternative considered: expose a broad indicator catalogue. That adds choice overload and moves the observational chart toward signal interpretation.

### 2. Focus a new chart context on at most 48 newest candles

The initial/new-context camera will use `min(48, loaded candle count)` candles with a small right edge. The existing 200-row buffer remains in the chart and continues to support pan/zoom. The explicit `最新` control reuses this camera. Realtime updates maintain the existing behavior: they follow only when the user is already at the newest edge.

Alternative considered: retain the 80-candle focus. It is robust but still too dense for the 15-minute reference use case. Alternative considered: use a different count per bar. That is harder to explain and test while not materially improving first-release readability.

### 3. Put trend legend in the plot without replacing the existing inspector

A compact top-left chart legend displays the MA labels and their values in matching colors. When a crosshair identifies a historical candle, legend values correspond to that candle; otherwise they describe the newest candle. The existing inspector remains the authoritative OHLC/volume detail below the header, keeping exact values discoverable without overcrowding the plot.

Alternative considered: show moving-average values only in the inspector. This removes the immediate association between a colored line and its value. Alternative considered: make the legend a new fixed-height header row. This takes vertical space from the candle pane.

### 4. Add contextual range and active-candle anchors with bounded annotation count

The chart displays the existing latest-price line/label plus a local closing countdown only for an unconfirmed newest candle. The countdown is calculated from the selected bar duration and current client time, updates once per second, and is omitted for a confirmed candle or unavailable timestamp. The highest high and lowest low in the current visible logical range receive at most one label each; if the same candle is both extrema, labels are merged. Visible-range tracking recomputes these annotations after pan, zoom, period change, or data replacement.

Alternative considered: annotate every swing high/low. That creates visual noise and makes the chart less readable. Alternative considered: use server time for the countdown. The current candle timestamp and selected duration already make client-side display sufficient; it does not affect market data or execution.

## Risks / Trade-offs

- [Thin history does not have 20 valid closes] → Render the available candles and omit only the MA lines whose lookback is incomplete.
- [MA lines slightly reduce candle contrast] → Use distinct but restrained line colors, 2px width, no line markers, and a small in-plot legend.
- [Current price, extrema, and MA legend collide on narrow layouts] → Prioritize the price label, allow the legend to wrap or compact at the existing narrow breakpoint, and omit an extrema label when it cannot be placed safely.
- [A client timer causes unnecessary rerenders] → Limit it to an unconfirmed newest candle, update at one-second cadence, and clean up on context changes/unmount.
- [Visible-range calculations use logical indexes outside loaded data] → Clamp indexes to normalized candle boundaries and render no extrema annotation for an empty/non-overlapping range.

## Migration Plan

1. Add deterministic moving-average, visible-window, countdown, and extrema-selection tests before wiring chart series.
2. Add line-series overlays and in-plot presentation while preserving current candlestick, volume, crosshair, and navigation behavior.
3. Verify common desktop and compact workbench viewports, all supported periods, short histories, historical panning, realtime updates, and the `最新` return control.
4. Roll back by removing the frontend-only overlay, legend, and annotation code; candle API, persisted data, and existing chart behavior remain compatible.

## Open Questions

- None for the first release. MA5, MA10, and MA20 remain visible by default; exposing per-user indicator toggles is deferred until there is evidence that users need configurability.
