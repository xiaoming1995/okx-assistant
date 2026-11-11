## Why

The market chart currently shows live price and candle structure, but it does not connect those signals with high-impact US macro events such as CPI releases, FOMC decisions, policy-rate context, or market-implied rate expectations. Users need a manual AI-assisted view that combines fresh macro context with the selected perpetual contract's current K-line structure, while keeping the output clearly bounded as decision support rather than an automated trading instruction.

## What Changes

- Add a manually triggered "AI看行情" capability to the market chart page for the currently selected contract and K-line period.
- Collect a bounded market snapshot containing ticker data, recent candles, derived K-line metrics, and freshness metadata before asking the LLM to analyze.
- Add a macro-data layer that retrieves and caches latest/scheduled US economic and policy context from configured public sources, starting with CPI and FOMC/policy-rate information.
- Generate a structured AI outlook with macro backdrop, technical read, direction bias, confidence, key levels, invalidation conditions, risk notes, and source freshness.
- Keep the feature observational and user-triggered: no automatic page-load LLM calls, no order placement, no strategy creation, and no mutation of ranking, trading state, leverage, or account data.
- Provide graceful fallback when macro data, OKX market data, or LLM calls fail, including stale-cache metadata and clear warnings.
- Record LLM usage with the existing usage logging pipeline under a new request type.

## Capabilities

### New Capabilities

- `market-ai-outlook`: Manual AI outlook for a selected OKX perpetual contract that combines fresh macro context with current ticker and K-line evidence, returning structured decision-support output with safety boundaries and source freshness.

### Modified Capabilities

- None.

## Impact

- Backend API: add a read-only market AI outlook endpoint and supporting request/response models.
- Backend data collection: add macro source clients, cache handling, K-line summary builders, and deterministic fallback analysis.
- Backend LLM integration: reuse existing LLM configuration, completion, JSON parsing, timeout, and usage logging utilities.
- Frontend market chart UI: add an "AI看行情" action and a compact analysis panel with loading, cache, fallback, warning, and result states.
- Tests: add backend tests for macro normalization, prompt payload bounds, strict response parsing, fallback behavior, and usage logging; add frontend static tests for manual trigger and clear risk/source labels.
- Operations: may require optional environment variables for macro source API keys if a chosen source needs one; first implementation should work with no private OKX account access beyond existing public market data.
