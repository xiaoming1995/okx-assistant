## Why

The market chart currently shows price, candles, ticker status, and 24h totals, but it does not explain the trading structure behind a selected contract. Users need to see per-contract long/short participation, taker buy/sell pressure, and open interest changes in one place so the chart feels actionable as an observation workspace instead of only a price viewer.

## What Changes

- Add a selected-contract trading statistics capability to the market chart page.
- Fetch and normalize OKX Trading Statistics data for each selected SWAP contract:
  - contract long/short account ratio by `instId`
  - contract taker buy/sell volume by `instId`
  - contract open interest history by `instId`
- Present a compact trading-structure summary near the chart so users can quickly see whether participation, active buying/selling, and open interest are changing.
- Add focused trend panels for long/short ratio, taker volume, and open interest without converting the feature into trading advice.
- Keep existing market instrument list search, watchlist, ticker polling, candle WebSocket behavior, trade submission, and automation behavior unchanged.

## Capabilities

### New Capabilities

- `market-contract-trading-stats`: Defines how the market chart retrieves, normalizes, and displays selected-contract trading statistics.

### Modified Capabilities

- None.

## Impact

- Affected backend code: OKX client trading-statistics methods, a normalized market stats API endpoint, caching/fallback logic as needed, and focused backend tests.
- Affected frontend code: market chart data loading, metric formatting, trading-structure summary UI, trend panels, loading/empty/error states, and focused frontend tests.
- External API: OKX Trading Statistics REST API under `/api/v5/rubik/stat/...`.
- Dependencies: no new third-party dependency is expected; existing chart/UI libraries should be reused.
- Systems: market chart observation workflow only. This change must not alter automated trading decisions or present the statistics as direct buy/sell instructions.
