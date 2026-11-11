## Context

`MarketPage` renders a fixed desktop market workbench: a contract rail on the left and a flex column on the right. The right column currently contains a workspace header, a three-column contract hero, a chart header, twelve permanently visible K-line metric tiles, and a `lightweight-charts` candlestick chart.

The current chart uses `lightweight-charts` v5.2.0 with a candlestick series and a crosshair callback. The existing candle payload already contains `open`, `high`, `low`, `close`, `volume`, and optional quote-volume fields. However, conversion currently drops volume when passing candle data to the chart. In addition, every candle-state update calls `timeScale().fitContent()`, which resets a user's chart navigation.

The prior short-height change intentionally made the right panel scrollable below a desktop height threshold. It prevents clipped content, but it does not establish hierarchy or reserve enough space for reading the trend. This change supersedes that scroll-first outcome for the supported desktop baselines while retaining safe overflow behavior outside them.

## Goals / Non-Goals

**Goals:**

- Make latest price, signed daily movement, and 24-hour context scannable before secondary metadata.
- Give price movement most of the available workbench height and display synchronized volume activity beneath it.
- Keep complete selected-candle data available without permanently dominating the chart workspace.
- Respect a user's manual time-scale position during realtime updates.
- Keep the right workbench's core chart content visible without vertical scrolling at 1280x720 and 1440x900 desktop viewports.
- Preserve current read-only data sources, supported bar intervals, contract rail behavior, and the external TradingView attribution link.

**Non-Goals:**

- Do not add order entry, automated trading controls, financial recommendations, or new market-data APIs.
- Do not add an indicator library, technical-analysis strategy signals, drawing tools, or multi-chart comparison in this change.
- Do not require the complete contract rail list to fit within a single viewport.
- Do not redesign the existing narrow/mobile single-column layout beyond preventing clipping or regression.

## Decisions

### 1. Use a three-level information hierarchy

The top of the right workbench will have three distinct levels:

1. **Persistent market summary**: contract identity, latest price, signed 24-hour change, and a compact 24-hour high/low/turnover summary.
2. **Operational state**: price and K-line transport source, freshness, and warnings shown as compact labels separate from market values.
3. **Contextual candle inspection**: timestamp, OHLC, candle change, amplitude, and volume shown in a single compact inspector for the crosshair-selected candle; it falls back to the newest candle when no candle is selected.

This replaces the always-visible twelve-tile K-line grid. It retains all existing detail data while preventing operational metadata and lower-priority figures from competing with the price trend.

Alternative considered: only reduce font sizes and tile padding. This would retain the same information hierarchy problem and still consume a fixed two-row area on short viewports.

### 2. Render a synchronized volume pane below the candlestick pane

The existing v5 chart library supports adding a series to a separate pane. A volume histogram will use the existing candle `volume` field, share the candlestick time scale, and use the candle direction color convention. The lower pane will have a bounded share of chart height so the price pane remains dominant.

If quote-volume is present, it remains available in the contextual inspector; the histogram label will not claim a quote currency where the source only provides contract/base volume.

Alternative considered: overlay volume columns on the price pane. It saves vertical space but obscures candle bodies and makes price-scale reading less clear.

### 3. Treat realtime follow as an explicit chart-navigation state

Initial data loading and a contract or bar-period change will fit the supplied candle range. After that, updates will preserve the current visible logical range. The chart will follow the newest candle only when the user is already viewing the newest edge, defined as the visible range ending within two bars of the newest bar. A user who pans or zooms away from that edge remains in control until they return to it.

The contextual inspector will continue to reflect the crosshair-selected candle while it is selected, rather than silently replacing it with the latest update.

Alternative considered: call `fitContent()` for each realtime snapshot. It guarantees the latest candle is visible, but makes historical inspection and chart zoom unusable on an active realtime feed.

### 4. Make the chart shell own the remaining desktop height

At supported desktop dimensions, non-chart content will have compact, bounded heights and the chart panel will fill the remaining right-workbench height. Inside the panel, the header and contextual inspector are fixed-size chrome, while the price and volume panes divide the remaining height. The price pane retains the larger share.

At desktop heights below the supported baseline, compact presentation is preferred before scrolling: secondary copy and nonessential spacing shrink or collapse while core values, period controls, the price pane, and volume pane remain visible. If the viewport cannot meet the baseline, the right workbench must permit reachability through scoped scrolling rather than clip content. Existing mobile/single-column rules remain the fallback at narrow widths.

Alternative considered: use a larger fixed minimum chart height. That improves the plot in isolation but recreates the prior clipping and nested-scroll problem.

### 5. Retain compliant external attribution outside the plot

The existing header link to TradingView remains visible and the library's in-plot attribution logo remains disabled. The redesign does not move attribution back into the plot or remove the external link.

Alternative considered: remove all attribution while simplifying the header. That would violate the established library-configuration constraint.

## Risks / Trade-offs

- [Volume semantics differ by instrument/source] → Label the histogram as volume, retain the source's raw unit semantics, and show quote volume only when supplied.
- [Following logic can feel surprising] → Make the rule deterministic, test both newest-edge and historical-view states, and retain a visible latest-price marker so users can orient themselves while inspecting history.
- [A compact desktop mode could become unreadable] → Prioritize removal/collapse of secondary chrome over reducing numeric font sizes below the existing readable scale.
- [Pane layout changes can expose library sizing edge cases] → Use the installed v5 pane API with `autoSize`, validate resized desktop viewports, and verify cleanup when the chart component unmounts.
- [A CSS-only response would appear complete but not fix navigation] → Include runtime coverage for manual pan/zoom persistence during a realtime candle update.

## Migration Plan

1. Implement the layout and chart-series changes only in the frontend, retaining existing API payloads and routes.
2. Run focused static tests, the frontend test suite and production build, then visually verify the desktop baselines and narrow fallback.
3. Verify the realtime follow rule using a controlled candle update after a manual historical pan.
4. Roll back by reverting the frontend change; no data migration, API rollout, or persisted user setting is introduced.

## Open Questions

- None for the V1 scope. Technical indicators, drawing tools, and user-configurable chart layouts remain deliberately deferred.
