## Context

The manual AI outlook report already stores the selected chart snapshot and exposes its recent 20-candle high/low, moving averages, volume context, and report-scoped trading-structure evidence. Its decision-reference module can say `暂不形成方向`, but the user must infer the price boundaries from separate chart-evidence text. The application must keep this public-data reading surface separate from execution, automation, and personal account data.

## Goals / Non-Goals

**Goals:**

- Provide compact, report-scoped upper, lower, and neutral observation levels for a no-direction or observation decision.
- Derive all displayed prices from the current report snapshot, not LLM-generated prose or an independently refreshed frontend data request.
- Associate an upper or lower level with clear close, volume, and available trading-structure confirmation cues, and explain that a move back into the range restores observation status.
- Mark a level set as needing refresh when the selected chart has advanced beyond its report snapshot.

**Non-Goals:**

- No target prices, stop losses, entry prices, position sizing, leverage, profit expectation, order drafting, alerts, or automatic execution.
- No new external market source, no private account or position inputs, and no automatic AI analysis on page load or price movement.
- No promise that a boundary will produce a price move; the levels are conditional reading cues only.

## Decisions

### Decision: Derive levels deterministically from the report snapshot

The backend will derive a `observationLevels` object from `technical.recent20Low` and `technical.recent20High` in the same market evidence that feeds the report. The lower value defines the bearish-observation boundary, the higher value defines the bullish-observation boundary, and both define the neutral range. The response includes instrument, K-line period, snapshot identity/time, availability, and a machine-readable status.

Rationale: these values are already traceable to the selected chart and remain stable for the life of the report. LLM `keyLevels` remain explanatory evidence but cannot choose the visible price levels.

Alternative considered: parse price levels from LLM key-level prose. This would be less auditable and risks presenting invented or stale numbers.

### Decision: Use conditional observation language, not execution language

An upper boundary becomes `上方偏多观察线` only after a completed selected-period candle closes above the range and the snapshot's volume and available structure evidence do not contradict the direction. A lower boundary uses the symmetrical `下方偏空观察线` rule. The UI calls each a `观察线`, never an entry, opening, target, or order instruction. Returning into the neutral range is rendered as `回到区间，恢复观望`.

Rationale: a wick through a recent high or low alone is not a reliable reading change, and the product has no user-specific risk inputs.

Alternative considered: show only “break above/below” price labels. This is shorter but invites users to mistake a touch for confirmation.

### Decision: Treat volume and open interest as confirmation quality, not a directional price source

The report uses its existing volume context plus available taker-volume and open-interest states to describe confirmation. Active buy/sell direction can support the corresponding boundary; open-interest growth represents participation only and must not determine long versus short by itself. Missing or partial structure data remains visible and prevents a level from being called fully confirmed.

Rationale: the fields have different market meanings; reducing them to a hidden score would obscure a conflict such as selling pressure with falling participation.

### Decision: Render a fixed four-row panel in the decision reference

The UI will display, in a stable order: neutral range, upper observation level, lower observation level, and return-to-range condition. Each value uses the existing market price formatting, while explanatory text wraps without truncation. The panel displays its K-line period and report-snapshot freshness; it signals that a manual refresh is needed when newer chart data exists.

Rationale: this exposes all three price states together and prevents long explanation text from pushing one direction out of view.

## Risks / Trade-offs

- [A report becomes older than its chart] → Bind levels to the report snapshot and visibly request a manual refresh once newer candles arrive.
- [K-line high/low is missing or invalid] → Omit the level panel and retain the existing generic observation condition.
- [Partial trade statistics create a false sense of confirmation] → Label partial data and state that it does not produce full confirmation.
- [Readers interpret a level as an instruction] → Use observation-only wording, retain the no-order boundary, and exclude personal trading parameters.
- [The range is very tight on a low timeframe] → Require completed-candle confirmation and show the selected period rather than treating a touch as a change of view.

## Migration Plan

1. Add deterministic report-level derivation and response mapping without changing report triggering or caching semantics beyond the snapshot-derived payload.
2. Render the panel only when valid snapshot levels exist, leaving all current reports readable if the field is absent.
3. Add focused backend/frontend and browser checks for available, partial, stale, and invalid-range states.
4. Roll back by hiding the optional frontend panel and omitting the additive backend field; existing decision and report fields remain compatible.

## Open Questions

- A future release could offer non-actionable price alerts for a level touch, but that requires separate notification permissions and is excluded here.
