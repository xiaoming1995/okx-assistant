## Context

The manual AI market report already has a compact conclusion, chart evidence, freshness state, and secondary source details. The response model also exposes horizon entries (`15m`, `1h`, and `today`) with an AI bias, confidence, summary, watch items, and risk. Those entries are currently not rendered, leaving the report without a short-horizon outlook.

## Goals / Non-Goals

**Goals:**

- Restore short-horizon outlooks in a compact, reader-friendly form.
- Keep every forecast explicitly conditional on the captured chart state and provide a re-read trigger.
- Reuse the existing manual response; no additional AI request or backend contract is needed.

**Non-Goals:**

- Guaranteed direction, price targets, trade signals, entry/exit advice, or automated actions.
- Adding forecasting when the response did not provide a horizon.
- Making macro availability a prerequisite for a chart-based forecast.

## Decisions

- Render up to three known horizons in chronological order: 15 minutes, one hour, then today. This matches the response contract and gives a predictable scan order.
- Use a dedicated `条件推演` section after chart evidence. Each card includes timeframe, directional observation, confidence, a chart-grounded summary, and one re-read/invalidating condition. This keeps present facts separate from future interpretation.
- Translate stance and raw technical terms with existing reader-facing mappings, and remove macro/source failure wording from the forecast cards. Source degradation remains in the collapsed supplement.
- If a horizon is absent or has no usable chart text, omit it rather than manufacture a prediction. The section explains that a conclusion is based on the captured snapshot and must be manually refreshed when the chart changes.

## Risks / Trade-offs

- [AI language can appear overly certain] → Label the section as conditional, show confidence, use observation-oriented language, and retain the no-trading safety boundary.
- [A report becomes stale as prices move] → Pair the section with the existing report-versus-current-chart freshness state and manual refresh control.
- [Horizon text can contain raw or macro-only fields] → Reuse the readable-text filter and show a bounded fallback only when it contains chart-relevant content.
