## Context

The OKX workspace already has market chart pages, public ticker/candle retrieval, realtime WebSocket updates, contract radar analysis, and a reusable LLM configuration/completion/usage logging stack. The requested feature is narrower than automated trading and broader than the existing radar explanation: it should let the user ask for an AI-assisted market-reading report for the currently selected contract by combining recent K-line evidence with current US macro context. The report is for user reading reference and must not overlap with automated trading signal semantics.

The macro context is time-sensitive. The system must fetch it from explicit public sources, cache it, and report freshness instead of relying on model memory. The first useful scope is CPI and Federal Reserve policy context, with a source abstraction that can later add additional releases such as PCE, nonfarm payrolls, unemployment, DXY, Treasury yields, or CME FedWatch probabilities.

## Goals / Non-Goals

**Goals:**

- Add a manual AI outlook flow on the market chart page for one selected OKX perpetual contract.
- Combine bounded market data, recent K-line structure, and US macro event/data context in one structured backend request.
- Include separate reference views for the next 15 minutes, next 1 hour, and today's session.
- Use existing LLM configuration, completion parsing, timeout behavior, and usage logging.
- Return a deterministic fallback outlook when macro sources or the LLM are unavailable.
- Show source names, publish/schedule times, cache ages, and warnings so the user can judge freshness.
- Keep the feature read-only and decision-support oriented.

**Non-Goals:**

- Do not auto-run the LLM on page load, every tick, every candle, or every contract selection.
- Do not place orders, prepare order tickets, create strategies, or modify automation state.
- Do not present the report as an automation signal, trade trigger, entry condition, or execution recommendation.
- Do not use private account balances, positions, leverage, or pending orders in the first version.
- Do not let the model invent macro facts that were not supplied by the backend.
- Do not provide guaranteed-profit language, mandatory buy/sell language, or unbounded personalized financial advice.
- Do not require a paid macro-data provider for the first implementation.

## Decisions

### Decision: Create a dedicated market AI outlook endpoint

Add a new read-only backend route such as `POST /api/market/ai-outlook` with inputs for `instId`, `bar`, `limit`, and force-refresh flags. The route should build the full evidence payload server-side and return a structured result.

Rationale: the frontend should not orchestrate multiple macro sources or assemble LLM prompts. Keeping this in the backend allows consistent caching, source attribution, usage logging, fallback behavior, and tests.

Alternative considered: call the LLM directly from the frontend with chart state. This would expose more prompt logic in the UI, make API key handling unsafe, and make macro freshness harder to verify.

### Decision: Fetch macro evidence before calling the LLM

The backend should gather macro facts through a small provider layer:

- CPI: latest/scheduled release context and values from BLS public data/news-release endpoints where available.
- Federal Reserve: upcoming/recent FOMC meeting context, policy-rate target range, and recent policy statement metadata from Federal Reserve public pages or feeds.
- Optional expectation source: market-implied rate expectation such as CME FedWatch only if the source can be fetched reliably and clearly labeled as market expectation, not official policy.

Every macro item should include `source`, `title`, `publishedAt` or `scheduledAt`, `value`, `previousValue` if available, `summary`, `url`, `cacheAgeMs`, and warnings.

Rationale: macro data changes over time and can materially alter interpretation. The model must see explicit evidence instead of relying on stale training data.

Alternative considered: ask the LLM to know the latest CPI/Fed events. This is not acceptable because the model can be stale or wrong about release timing and values.

### Decision: Keep macro source failures isolated

Macro collection should return partial results and warnings instead of failing the whole outlook. A fresh source is preferred, stale cache is acceptable with a visible warning, and total macro-source failure should still allow a technical-only fallback.

Rationale: a transient BLS/Fed/network failure should not break the chart page. The user still benefits from K-line interpretation if macro facts are marked unavailable.

Alternative considered: fail the request whenever a macro source fails. This is simpler but brittle and creates a poor user experience during high-interest events.

### Decision: Use bounded market and K-line summaries

The AI payload should include:

- selected contract identity and instrument metadata
- current ticker snapshot and 24h change/volume fields
- recent candle summary across the selected bar
- a capped list of recent candle details, for example the last 30 candles
- derived technical fields such as trend slope, recent range, volume change, last candle body/wick, volatility, and recent highs/lows
- realtime/source/freshness fields from the existing chart data path
- multi-period summaries for report horizons: next 15 minutes from 1m/5m candles, next 1 hour from 5m/15m candles, and today from 15m/1H/4H candles plus 24h ticker context

Rationale: this gives the LLM enough evidence to explain the current structure without sending unbounded raw data.

Alternative considered: send every loaded candle and all ticker fields. This increases cost and latency without improving reliability.

### Decision: Return strict structured output

The LLM must return JSON with a fixed shape:

- `stance`: `bullish`, `bearish`, `neutral`, or `wait`
- `confidence`: 0-100
- `summary`: concise conclusion
- `overall`: user-readable market view, reference confidence, and summary
- `horizons`: exactly `15m`, `1h`, and `today`, each with bias, confidence, summary, watch items, and risk note
- `report`: key factors, focus items, reassessment conditions, and risk notes
- `macro`: macro bias, key events, and uncertainty
- `technical`: trend, key levels, volume read, and pattern notes
- `suggestion`: legacy-compatible observation action, user focus item, reassessment note, risk notes
- `sources`: compact source references and freshness
- `warnings`: user-visible caveats

The parser should normalize aliases, clamp confidence, drop unsupported fields, and fall back on deterministic analysis when JSON parsing fails.

Rationale: the frontend needs stable rendering and tests need a predictable contract.

Alternative considered: render free-form markdown. That is faster but harder to validate and easier to overstate.

### Decision: Keep output report-oriented and non-executing

The feature can say things like "未来15分钟震荡观察", "未来1小时偏多参考", "今天走势受 CPI/FOMC 影响需要重评", or "用户可关注 2468 附近压力". It must not submit orders, pre-fill trading tickets, or use language like "信号触发", "开仓", "入场", "必须买入", "必须做空", or "保证收益".

Rationale: the user's intent is self-read market context. Execution belongs to the trading/automation modules, which already have separate safety gates.

Alternative considered: wire the result into trading or automation. That increases risk and is out of scope for this chart-page feature.

### Decision: Cache macro data and analysis separately

Use separate cache keys for macro snapshots and AI outlook results:

- Macro cache keyed by provider/source and normalized request.
- AI outlook cache keyed by `instId`, `bar`, latest candle timestamp, ticker timestamp, macro snapshot hash, and prompt schema version.

Normal refresh can reuse fresh cached macro data. Explicit "刷新AI" can bypass analysis cache but should still respect provider-specific macro cache limits unless `forceMacro` is requested.

Rationale: macro data and chart data refresh at different frequencies. Separate caching reduces LLM cost while keeping freshness visible.

Alternative considered: one shared cache blob. That makes invalidation unclear and can show stale macro context with fresh candles.

## Risks / Trade-offs

- [Risk] Macro data sources are unavailable or change format. -> Mitigation: isolate each provider, keep partial results, show warnings, and preserve stale cache.
- [Risk] LLM output overstates certainty. -> Mitigation: require confidence, invalidation, risk notes, source references, and forbid guaranteed or mandatory trading language.
- [Risk] Users confuse AI outlook with automated trading. -> Mitigation: label the panel as analysis only and avoid controls that directly create orders or strategies.
- [Risk] Prompt payload grows and raises latency/cost. -> Mitigation: cap candle detail count, summarize technical features, and run only on manual click.
- [Risk] Current macro context may be stale around release minutes. -> Mitigation: expose publish/schedule time and cache age; allow explicit refresh.
- [Risk] Official macro sources may not expose all fields needed for "加不加息" probabilities. -> Mitigation: distinguish official Fed events from market-implied expectations and make expectation sources optional.

## Migration Plan

1. Add backend macro snapshot models and provider functions with source-level cache/fallback behavior.
2. Add selected-contract market summary builders that reuse existing ticker/candle APIs and database cache.
3. Add `POST /api/market/ai-outlook` with strict request validation, prompt building, LLM invocation, structured parsing, usage logging, and deterministic fallback.
4. Add frontend chart-page action and result panel without changing existing chart, radar, trade, or automation flows.
5. Add tests for provider normalization, fallback behavior, prompt caps, LLM parsing, usage logging, and frontend rendering.
6. Roll back by hiding the frontend action and disabling the endpoint; existing market chart and radar flows continue unchanged.

## Open Questions

- Should the first version include market-implied rate probabilities, or only official BLS/Fed facts?
- What macro cache TTL should be used around scheduled release windows: normal 30-60 minutes, but shorter near release time?
- Should "AI看行情" live only on the chart page, or also appear on the contract radar detail panel after the first version proves stable?
- Should the UI call the output "投资建议" or the safer "行情观点 / 观察建议"? The latter better matches the read-only boundary.
