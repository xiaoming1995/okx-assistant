## Context

Contract Radar already scans OKX SWAP instruments, filters by settlement and liquidity thresholds, fetches bounded candle data, and ranks contracts with deterministic scores. The LLM is currently suitable for explaining selected candidates, but it does not reason over the whole scan universe.

The requested improvement is to let the LLM analyze the market-wide data already collected by the radar so users can understand which areas of the market are active, volatile, risky, or worth watching. This must remain decision support: deterministic rules continue to own ranking, tradability status, and safety gates.

## Goals / Non-Goals

**Goals:**

- Add a manual AI market analysis flow in Contract Radar.
- Summarize all scanned market data into a compact structured payload before calling the LLM.
- Produce a simple market-level answer: regime, key drivers, watchlist, risks, and suggested filters.
- Keep scan/rank behavior deterministic and testable.
- Make LLM cost and latency explicit by triggering analysis only from a user action.
- Provide graceful fallback when LLM is unavailable.

**Non-Goals:**

- Do not automatically run AI analysis on page load.
- Do not send unbounded raw tickers or candle rows to the LLM.
- Do not let the LLM change opportunity scores, ranking order, liquidity gates, or risk labels.
- Do not place orders, create strategies, or emit buy/sell instructions from the analysis.
- Do not require private account, position, or order data.

## Decisions

### Decision: Use a two-stage radar analysis pipeline

The backend should first run the existing deterministic market scan, then build a compact market summary from that scan for the LLM.

Pipeline:

```text
OKX instruments/tickers/candles
  -> deterministic radar scan and scoring
  -> compact market summary
  -> LLM market analysis
  -> UI analysis panel
```

Rationale: deterministic scanning is cheaper, testable, and already aligned with the radar's contract-selection role. The LLM is best used to synthesize context and communicate trade-offs from the prepared evidence.

Alternative considered: send all contracts and candles directly to the LLM. This is slower, more expensive, harder to verify, and more likely to produce inconsistent output.

### Decision: Analyze a bounded market summary, not raw market rows

The summary should include aggregate fields and short top lists such as:

- scan universe count, returned candidate count, skipped count, and freshness timestamp
- market breadth: rising/falling/flat counts, median and percentile 24h change
- liquidity distribution: total comparable turnover, top turnover contracts, low-liquidity count
- volatility distribution: median range, high-volatility count, top volatility contracts
- volume and risk signals: volume spike candidates, abnormal move candidates, stale/missing data count
- deterministic radar leaders: top playable contracts with score, turnover basis, volatility, risk, and tags

Rationale: this keeps prompts bounded while still giving the LLM enough market-wide context to compare sectors, liquidity, and volatility.

Alternative considered: analyze only the visible top ranking rows. That would be cheaper but would miss broad market conditions and why certain contracts are excluded.

### Decision: Keep AI analysis as an explicit user action

The Contract Radar page should not call the LLM on initial load or during filter changes. Users first run a radar scan, then click an AI analysis action when they want the market synthesis.

Rationale: users asked for a cleaner interaction model. Separating scan from AI analysis makes latency, token cost, and data freshness easier to understand.

Alternative considered: automatically call the LLM after every scan. This is convenient but makes the page feel busy, can add unexpected delays, and can create unnecessary LLM usage.

### Decision: Return strict structured LLM output

The LLM response should be parsed as a fixed JSON shape:

- `marketRegime`: concise regime label such as `trend`, `range`, `mixed`, or `risk-off`
- `confidence`: bounded numeric or enum confidence value
- `summary`: one concise paragraph
- `highlights`: short list of market observations grounded in provided metrics
- `watchlist`: contracts worth inspecting, each with reason and risk note
- `riskWarnings`: short list of risks and excluded patterns
- `suggestedFilters`: optional radar filters or follow-up scan settings
- `generatedAt`, `source`, and `warnings`

Rationale: a strict shape makes UI rendering predictable and lets tests verify that fallback and parsing behavior are stable.

Alternative considered: return free-form markdown. This is faster to build, but it makes the UX less consistent and harder to validate.

### Decision: LLM cannot alter deterministic rank or trading state

The analysis output can reference deterministic radar candidates and can explain why a contract is worth watching, but it must not overwrite scores, rank order, tradability status, or risk labels. It also must not execute or prepare trades.

Rationale: ranking is a product contract that must be auditable from market data. LLM output is advisory context, not a control plane.

Alternative considered: let the LLM produce a final "best contracts" ranking. This would undermine reproducibility and make low-liquidity hallucinations harder to catch.

### Decision: Cache analysis separately from scan snapshots

AI analysis should be cached with the scan input hash, filter settings, generated timestamp, and stale/fresh status. A normal radar rescan should not necessarily force a fresh LLM call unless the user explicitly requests fresh analysis or the cache is stale.

Rationale: users may revisit the analysis panel while tuning filters. Separate caching controls LLM cost without hiding data freshness.

Alternative considered: never cache AI analysis. This is simpler but unnecessarily expensive and makes repeated UI checks slow.

## Risks / Trade-offs

- [Risk] The LLM may overstate certainty. -> Mitigation: bound output fields, show confidence, require metric-grounded reasons, and avoid buy/sell language.
- [Risk] Prompt payload can grow as the market universe grows. -> Mitigation: summarize aggregates and cap all top lists before calling the LLM.
- [Risk] Users may confuse AI analysis with deterministic scoring. -> Mitigation: separate UI sections and labels: radar ranking remains data score, AI panel is market interpretation.
- [Risk] LLM failures could block radar scanning. -> Mitigation: keep scan and analysis endpoints independent and return deterministic fallback analysis on failure.
- [Risk] Cached analysis can become stale during fast markets. -> Mitigation: display generated time, scan time, cache age, and provide explicit refresh.

## Migration Plan

1. Add market summary models and builder functions behind the existing radar scan data path.
2. Add the AI analysis API action with strict response parsing, fallback output, and separate cache metadata.
3. Add frontend controls and a compact analysis panel without changing default radar ranking behavior.
4. Add backend and frontend tests for manual trigger, summary payload limits, fallback behavior, and UI labels.
5. Rollback by hiding the AI analysis action and stopping calls to the analysis endpoint; deterministic radar remains unchanged.

## Open Questions

- What cache freshness window should be used for AI analysis: 1 minute, 3 minutes, or aligned with the radar snapshot TTL?
- Should the first implementation include optional funding/open-interest data if available later, or keep the prompt strictly to instruments, tickers, candles, and radar scores?
- Should suggested filters be clickable in the first version or displayed as read-only guidance?
