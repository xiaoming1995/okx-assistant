## Context

The application already has OKX SWAP instrument discovery, ticker snapshots, candle caching, market charts, manual trade entry, and automation strategies. Contract selection is still mostly manual: users can sort instruments by 24h change or volume, then inspect one chart at a time.

The contract radar agent sits between the market page and automation setup. It scans many contracts, ranks them with deterministic market metrics, and gives users a concise explanation of which contracts are worth watching, suitable for short-term volatility, or too risky to touch.

## Goals / Non-Goals

**Goals:**

- Rank all available OKX SWAP contracts using a transparent scoring model.
- Separate "tradable enough" from "volatile enough" so users can understand why a contract appears in the ranking.
- Reuse current instrument, ticker, candle, cache, and LLM infrastructure where practical.
- Keep the first UI simple: ranked list, score strip, key metrics, tags, warnings, and actions to open existing flows.
- Limit expensive calls by scoring deterministically first and asking the LLM to explain only the top candidates.

**Non-Goals:**

- Do not automatically place orders from radar results.
- Do not promise profitable trades or generate a mandatory long/short signal.
- Do not require authenticated account data for radar scanning.
- Do not block the first version on optional derivatives metrics such as open interest, funding rate, or long/short ratio.
- Do not replace existing market, manual trade, or automation pages.

## Decisions

### Decision: Add a dedicated radar API

Create a backend endpoint such as `GET /api/market/radar` that returns normalized scan results instead of making the frontend assemble ranking logic from raw instruments, tickers, and candles.

Rationale: scoring must be consistent, testable, cacheable, and reusable from other pages. Keeping it in the backend also avoids issuing many candle requests from the browser.

Alternative considered: compute ranking entirely in the frontend from `/api/instruments`, `/api/tickers`, and `/api/candles`. This is simpler initially but would duplicate scoring logic, increase browser-side request fan-out, and make LLM explanation orchestration harder to control.

### Decision: Score deterministically before using the LLM

The radar scan computes numeric scores from market data first:

- Tradability score: instrument is live, quote/contract volume, data completeness, and later spread/slippage proxies.
- Volatility score: 24h high-low range, recent candle range percentage, recent return variability, and volume spike.
- Risk penalty: low volume, stale data, abnormal single-candle moves, missing candles, non-live instruments.
- Opportunity score: weighted combination of tradability and volatility after risk penalties.

The LLM may summarize reasons and warnings for top results only.

Rationale: deterministic ranking is cheaper, faster, auditable, and easier to test. LLM output is better used for explanation and grouping, not for raw market ranking.

Alternative considered: ask the LLM to analyze all contracts directly. This would be slow, costly, nondeterministic, and hard to verify.

### Decision: Use staged data collection

The scan should first load all SWAP instruments and ticker rows, filter out clearly unsuitable contracts, then fetch candles only for the remaining candidate set.

Default candidate strategy:

1. Include live SWAP instruments.
2. Prefer USDT-settled contracts unless the user includes coin-margined contracts.
3. Rank by 24h quote/contract volume and keep a bounded candidate count.
4. Fetch recent candles for candidates using one or more configured bars.
5. Compute scores and return top results.

Rationale: fetching candles for every contract on every scan can hit API limits and slow the UI. Ticker data is already cached and cheap enough to use as the first filter.

Alternative considered: fetch candles for every SWAP contract. This gives more complete scoring but creates unnecessary latency and load for the first version.

### Decision: Cache radar snapshots

Radar results should be cached for a short freshness window and stored as a scan snapshot. The response should include source, timestamp, cache age, and warning fields consistent with existing ticker/account patterns.

Rationale: users will refresh and filter the page often. A cached snapshot avoids repeating OKX and LLM calls while keeping the UI responsive.

Alternative considered: live scan on every page load. This makes freshness straightforward but increases latency, cost, and failure exposure.

### Decision: Keep radar actions contextual

Each ranked contract should provide actions to:

- Open the market chart for that contract.
- Open manual trade with that contract selected.
- Start creating or editing an automation strategy for that contract.

The radar itself should not execute trades.

Rationale: radar is a decision-support layer. Execution should remain in existing trade and automation flows where risk controls already exist.

## Risks / Trade-offs

- [Risk] Users may treat high opportunity score as a guaranteed profitable recommendation. -> Mitigation: label scores as market suitability, show risk warnings, and avoid direct buy/sell language in radar.
- [Risk] Scanning too many contracts may hit OKX rate limits. -> Mitigation: use ticker-first filtering, bounded candle candidates, cache snapshots, and expose stale-cache warnings.
- [Risk] Low-liquidity coins can look attractive because of extreme volatility. -> Mitigation: apply tradability thresholds and risk penalties before ranking by volatility.
- [Risk] LLM explanations may overstate confidence. -> Mitigation: require explanations to cite provided metrics only and keep numeric ranking outside the LLM.
- [Risk] Optional metrics may not be available in the current OKX client. -> Mitigation: ship first version with instruments, tickers, and candles; add open interest, funding, and order book metrics as later enhancements.
- [Risk] The UI can become visually noisy if too many metrics are shown. -> Mitigation: default to compact score, tag, reason, and warning columns; move detailed metrics into a side panel or expanded row.

## Migration Plan

1. Add radar scan models and scoring helpers without changing existing market or automation behavior.
2. Add radar API and cache/persistence support.
3. Add frontend API client and radar page.
4. Add navigation entry and contextual actions into existing market, trade, and automation flows.
5. Validate with backend unit tests, frontend rendering tests, and a production build.

Rollback is straightforward because radar is additive. Remove the navigation entry and stop calling the radar endpoint; existing market, trade, and automation flows remain intact.

## Open Questions

- Should the first default universe include only USDT-settled SWAP contracts, or all SWAP contracts?
- What default K-line window should represent "recent volatility": 1m, 5m, 15m, or 1h?
- Should radar scans run only on demand, or also refresh periodically in the background?
- Should LLM explanations be optional behind a toggle to avoid token cost?
