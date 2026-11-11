## Context

The market chart page currently loads SWAP instruments, ticker snapshots, and candle data. It renders price-focused chart context for the selected contract, but it does not expose contract-level trading statistics such as long/short account ratio, taker buy/sell pressure, or open interest history.

OKX exposes those metrics through the Trading Statistics REST API under `/api/v5/rubik/stat/...`. The relevant contract-level endpoints are unauthenticated public data endpoints, but they have lower per-instrument rate limits than the existing ticker snapshot endpoint. The frontend also supports `1m` candles, while OKX trading-statistics endpoints generally use `5m` or coarser periods.

## Goals / Non-Goals

**Goals:**

- Provide selected-contract trading statistics on the market chart page for OKX SWAP instruments.
- Normalize OKX array responses into named fields so the frontend does not depend on endpoint-specific array positions.
- Show a compact, readable trading-structure summary: long/short account ratio, active buy/sell balance, and open interest level/change.
- Keep statistics aligned with the selected contract and an explicit statistics period.
- Handle loading, partial data, stale data, and OKX errors without breaking candles or ticker display.

**Non-Goals:**

- Do not change instrument search/filter behavior, watchlist behavior, or the completed market instrument list UX scope.
- Do not add automatic trading rules or automation signals based on these statistics.
- Do not present long/short ratio or taker volume as direct buy/sell instructions.
- Do not add option-market statistics in the first implementation.
- Do not require private OKX account credentials for public trading-statistics data.

## Decisions

### Add a Backend Aggregation Endpoint

Add a backend endpoint such as `GET /api/market/stats?instId=BTC-USDT-SWAP&period=5m&limit=100` that fetches and normalizes the three first-version contract metrics:

- `/api/v5/rubik/stat/contracts/long-short-account-ratio-contract`
- `/api/v5/rubik/stat/taker-volume-contract`
- `/api/v5/rubik/stat/contracts/open-interest-history`

Rationale: the frontend should not know OKX response array positions, endpoint naming differences, rate-limit quirks, or fallback rules. A single normalized endpoint also lets the backend cache by `instId + period + limit`.

Alternative considered: call OKX directly from the frontend. This would duplicate parsing logic in UI code, complicate local/prod proxy behavior, and make rate limiting harder to control.

### Normalize Data Around Observation, Not Advice

The backend should return named series and derived summary values:

- latest long/short account ratio
- taker buy volume, taker sell volume, taker buy share, and buy/sell ratio
- latest open interest in contracts, coin, and USD when available
- open interest change over the returned series
- source, timestamp, cache age, and warnings

Rationale: users need plain evidence and directionality, while downstream UI copy must stay observational. This project already treats market radar and LLM explanations as observation support rather than direct trading advice.

Alternative considered: compute a single sentiment score. That would hide evidence behind another opaque score and could be mistaken for a trading signal.

### Use an Explicit Statistics Period

The first implementation should default trading statistics to `5m`, even when the chart is showing `1m`. If the selected chart interval is supported by the trading-statistics endpoints, the page can use the same period; otherwise it must show the effective statistics period.

Rationale: OKX trading statistics do not map perfectly to all candle intervals. Explicit period labeling avoids misleading users into thinking 1m candles and 5m statistics are sampled at the same cadence.

Alternative considered: force the chart to only use periods supported by trading statistics. This would reduce chart flexibility and change existing chart behavior unnecessarily.

### Display Summary First, Trends Second

The market page should add a compact trading-structure summary near the selected-contract hero or chart header, then render focused trend panels below the chart for users who want detail:

```text
Selected Contract
Price / 24h / metadata

Trading Structure
Long/Short Accounts | Taker Buy Share | Open Interest | OI Change

Candlestick Chart

Detail Panels
[Long/Short] [Taker Buy/Sell] [Open Interest]
```

Rationale: users first need to know what matters now, then inspect history. Putting multiple mini trends above the main K-line would crowd the primary chart.

Alternative considered: overlay all statistics on the candle chart. That would make scales hard to read and risks visual clutter.

### Treat Elite Trader Metrics as Later Scope

The OKX endpoints for top-trader long/short account and position ratios should remain out of the first implementation unless the user asks for an advanced panel.

Rationale: the first version should solve the core "what is happening in this contract" problem without adding several similar ratios that are easy to misread.

Alternative considered: include every related OKX metric immediately. That would increase implementation and QA surface while making the UI harder to scan.

## Risks / Trade-offs

- [Risk] OKX trading-statistics endpoints have lower rate limits than tickers. -> Mitigation: cache by instrument and period, refresh on selected-contract changes, and avoid polling faster than the endpoint data can update.
- [Risk] Some contracts or periods may return empty statistics. -> Mitigation: show partial data states per metric and keep existing price/K-line panels working.
- [Risk] Users may interpret ratios as trading instructions. -> Mitigation: use observational labels such as "偏多账户较多" and "主动买入占比", avoid "buy/sell" recommendations, and do not feed these values into automation by default.
- [Risk] 1m chart data can be paired with 5m statistics. -> Mitigation: expose and display `statsPeriod` clearly in the UI.
- [Risk] OKX array response shapes are easy to parse incorrectly. -> Mitigation: centralize parsing in `OkxClient` helpers and cover response normalization with backend tests.

## Migration Plan

This is an additive change. Deploy the backend endpoint first, then the frontend can render an unavailable or loading state until stats are returned. Rollback is straightforward: remove the market stats UI and endpoint without changing existing instruments, tickers, candles, trading, or automation data.

## Open Questions

- Should the first UI use the chart period when supported, or always use a separate statistics period selector?
- Should the backend persist recent stats snapshots to the database, or keep only an in-memory cache for the first version?
- Should top-trader metrics be exposed later as an "advanced" toggle on the market chart page or as a separate analysis panel?
