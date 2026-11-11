## Why

The app currently focuses on OKX SWAP market observation, manual trading, automation safety, positions, and account balances, but it does not show OKX On-chain Earn products, staking balances, or earn order states. Users need a conservative finance workspace that makes yield products, active orders, redemption timing, and ETH/SOL staking positions readable without turning yield discovery into automated investment action.

## What Changes

- Add an On-chain Earn dashboard for OKX financial products, starting with read-only product, balance, order, and APY visibility.
- Fetch and normalize OKX On-chain Earn product offers from `/api/v5/finance/staking-defi/offers`.
- Fetch and normalize active and historical On-chain Earn orders from `/api/v5/finance/staking-defi/orders-active` and `/api/v5/finance/staking-defi/orders-history`.
- Add dedicated read-only ETH staking and SOL staking panels for product info, balance, purchase/redeem history, and APY history.
- Add non-blocking loading, partial failure, stale cache, and unconfigured credential states so the rest of the dashboard remains usable.
- Add a clear navigation entry for Earn under the account/finance workflow.
- Keep purchase, redemption, cancellation, automatic subscription, and any LLM/radar-driven Earn action out of the first implementation.
- Define the future action boundary so later purchase/redeem work must use a separate explicit enable flag, confirmation, and local audit trail instead of reusing the manual trading authorization switch.

## Capabilities

### New Capabilities

- `on-chain-earn`: Defines how the system retrieves, normalizes, displays, and safely scopes OKX On-chain Earn products, orders, ETH staking, and SOL staking data.

### Modified Capabilities

- None.

## Impact

- Affected backend code: OKX client financial-product methods, normalized Earn API endpoints, cache/fallback helpers, credential handling, focused tests, and optional local snapshot storage if needed for stale fallback.
- Affected frontend code: navigation grouping, Earn page data loading, product/order/staking tables or panels, APY history rendering, loading/empty/error states, and focused static tests.
- External API: OKX V5 financial-product endpoints under `/api/v5/finance/staking-defi/...`.
- Dependencies: no new third-party dependency is expected; reuse existing FastAPI, React, lucide-react, and chart/formatting patterns where possible.
- Systems: finance observation workflow only. This change must not submit Earn purchase/redeem/cancel requests, alter SWAP manual trading, or feed Earn data into automated trading decisions.
