## Why

The market instrument list is the first place users choose a contract, but the current list makes similar symbols look duplicated and forces users to infer important settlement and contract-value differences. Searching for `BTC` can show both `BTC-USD-SWAP` and `BTC-USDT-SWAP` without enough explanation, which makes the market page feel unstable and harder to use.

## What Changes

- Improve the market instrument list so search results clearly distinguish USDT-settled and coin-settled swap contracts.
- Prefer the ordinary USDT-settled browsing path by default while still allowing users to view all contracts and coin-settled contracts.
- Stabilize market-page search by filtering the loaded instrument set in the client instead of reloading the instrument list on every keystroke.
- Align the market page list semantics with the trade and automation contract pickers so users see consistent contract metadata across entry points.
- Preserve all existing OKX instruments, watchlist actions, chart loading, ticker polling, and downstream trade or automation behavior.

## Capabilities

### New Capabilities

- `market-instrument-list`: Defines the user-facing behavior for browsing, searching, filtering, sorting, and selecting market instruments.

### Modified Capabilities

- None.

## Impact

- Affected frontend code: `frontend/src/main.tsx`, `frontend/src/styles.css`, and focused frontend static tests.
- Affected backend code: no endpoint contract changes are required; `/api/instruments` remains available for initial load and manual refresh.
- Dependencies: none.
- Systems: market chart contract selection UI, plus any shared helper behavior reused by trade and automation contract pickers.
