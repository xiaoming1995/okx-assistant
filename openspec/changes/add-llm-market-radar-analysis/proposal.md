## Why

Contract Radar currently ranks contracts with deterministic market metrics and can ask the LLM to explain selected candidates. Users now need the LLM to analyze the broader market context from collected market data, so contract selection can consider market regime, liquidity concentration, volatility clusters, and risk breadth instead of only per-contract rows.

## What Changes

- Add a manually triggered AI market analysis capability for Contract Radar.
- Build a compact, deterministic market summary from SWAP instruments, ticker snapshots, candle-derived metrics, and radar candidates before calling the LLM.
- Send bounded structured summary data to the LLM instead of raw rows for every contract or every candle.
- Return a concise analysis containing market regime, confidence, key observations, watchlist contracts, risk warnings, and suggested radar filters.
- Keep deterministic radar scoring and ranking authoritative; the LLM cannot change numeric scores, ranking order, tradability status, or execute trades.
- Add graceful fallback output when LLM configuration is missing, the LLM call fails, or the response cannot be parsed.
- Expose freshness, source, and warning metadata so the UI can clearly distinguish cached analysis from fresh analysis.

## Capabilities

### New Capabilities

- `llm-market-radar-analysis`: Manual LLM analysis over summarized market-wide radar data, producing market regime, insights, watchlist, risks, and filter suggestions without controlling ranking or trading.

### Modified Capabilities

- None.

## Impact

- Backend market radar code: summary builder, bounded LLM prompt, strict response parsing, cache/freshness metadata, and fallback analysis.
- Backend API surface: add an analysis endpoint or extend radar scan responses with an explicit analysis action.
- Frontend Contract Radar UI: add a separate AI market analysis action and compact analysis panel.
- Tests: backend unit tests for summary construction, LLM/fallback behavior, and cache semantics; frontend static tests for manual-trigger UX and clear labels.
- No new exchange integration or private account dependency is required.
