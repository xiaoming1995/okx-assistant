## Context

The current app is a local OKX dashboard for SWAP market discovery, charts, manual trading, automation safety, positions, and account assets. It already has a single `OkxClient` request/signing boundary, environment-specific credentials, backend cache/fallback patterns, a compact React workspace UI, and an explicit safety posture that keeps automated execution limited and auditable.

OKX On-chain Earn is part of the V5 financial-product API under `/api/v5/finance/staking-defi/...`. The generic On-chain Earn endpoints expose product offers, active orders, historical orders, purchase, redeem, and cancel. ETH staking and SOL staking use separate product, balance, history, and APY endpoints. Only funding-account assets support On-chain Earn purchase or specialized ETH/SOL staking, so the first implementation should be a finance observation workspace rather than a trading extension.

## Goals / Non-Goals

**Goals:**

- Add a read-only On-chain Earn capability that displays product offers, active orders, historical orders, ETH staking data, and SOL staking data.
- Normalize OKX financial-product response fields so the frontend renders named values instead of endpoint-specific raw JSON shapes.
- Keep Earn loading, partial failure, and stale cache states isolated from market, trading, automation, and account pages.
- Reuse the existing OKX credential/environment handling and backend API style.
- Make future purchase/redeem work explicitly gated by separate Earn action controls and audit requirements.

**Non-Goals:**

- Do not implement Earn purchase, redemption, cancellation, or ETH/SOL staking actions in the first version.
- Do not create automatic Earn subscription, redemption, allocation, or rebalancing logic.
- Do not feed Contract Radar, LLM analysis, or automation strategies into Earn actions.
- Do not change SWAP manual trading permissions or reuse `OKX_ENABLE_LIVE_TRADING` as an Earn action authorization flag.
- Do not add Web3 wallet DeFi APIs or self-custody transaction calldata flows in this change.

## Decisions

### Decision: Treat Earn as a finance/account workflow, not a market signal workflow

Add the frontend entry under the account/finance area, with room to promote the top-level section from `Account` to `Finance` if the navigation needs to hold account assets, positions, and Earn together.

Rationale: Earn products are tied to funding-account assets, yield positions, and redemption timing. They are not SWAP contracts and should not be presented like market candidates or strategy signals.

Alternative considered: add Earn under Market. This would make APY look like a market opportunity score and blur the existing observation-versus-action boundary.

### Decision: Ship read-only data first

The first implementation should only call GET endpoints and render product, balance, APY, active order, and history data. Mutation endpoints should appear only in design notes and specs as explicitly out of scope.

Rationale: On-chain Earn actions move real funding-account assets and may have lockup, early-redemption, and settlement consequences. The app already separates manual/automated trading safety; Earn needs the same care before any action is added.

Alternative considered: include purchase/redeem forms immediately. This would expand the first implementation into a financial action workflow before users can verify that the displayed data and order states are correct.

### Decision: Use one backend aggregation layer with three source families

Extend `OkxClient` with financial-product methods and expose backend endpoints around normalized payloads:

- Generic On-chain Earn: offers, active orders, and order history.
- ETH staking: product info, BETH balance, purchase/redeem history, and APY history.
- SOL staking: product info, OKSOL balance, purchase/redeem history, and APY history.

Rationale: OKX returns similar concepts with different endpoint paths and response shapes. The frontend should consume stable app-level structures such as `products`, `orders`, `stakingCards`, `apyPoints`, `source`, `ts`, `cacheAgeMs`, and `warnings`.

Alternative considered: call OKX directly from the frontend. That would duplicate signing concerns, leak API shape into UI code, and make fallback behavior inconsistent with the rest of the backend.

### Decision: Cache by endpoint family and query parameters

Use backend cache keys that include environment, source family, filters, pagination, and APY days. Product and APY data can tolerate longer freshness windows than active orders and balances. Failed refreshes should return stale cache when available with a warning.

Rationale: OKX financial endpoints have user/IP rate limits, and users may switch filters frequently. Existing market-stat and account patterns already favor non-blocking stale fallback when live data is temporarily unavailable.

Alternative considered: always fetch live data. This would be simpler but more fragile and more likely to hit rate limits or make the page noisy during OKX/API instability.

### Decision: Normalize state labels conservatively

Map generic active order states into readable labels:

- `8`: waiting to subscribe / reserved
- `13`: cancelling
- `9`: on-chain processing
- `1`: earning
- `2`: redeeming

Map history state `3` as completed, while preserving raw state and raw payload for inspection. ETH/SOL history statuses should remain `pending`, `success`, `failed`, and `cancelled` where returned.

Rationale: Users need readable state, but OKX raw states are still necessary for support and future action logic.

Alternative considered: render only raw numeric state. That is technically accurate but weak for ordinary operational review.

### Decision: Keep future Earn actions behind separate authorization and audit

If purchase/redeem/cancel is added later, require a separate flag such as `OKX_ENABLE_EARN_ACTIONS=1`, an explicit confirmation that names the environment, asset, amount, product/order id, early-redemption choice, and expected settlement/redeem period, plus durable local audit records.

Rationale: `OKX_ENABLE_LIVE_TRADING` is scoped to SWAP order actions. Earn actions affect funding-account assets and should have a separate mental model and operational evidence.

Alternative considered: reuse live trading enablement. That would surprise users because enabling contract trading would also enable yield product asset movement.

## Risks / Trade-offs

- [Risk] Product APY may be mistaken for a recommendation. -> Mitigation: use labels such as "预估年化", "当前状态", and "赎回周期"; avoid "推荐申购" or automatic ranking language.
- [Risk] Active orders, balances, and product offers refresh at different useful cadences. -> Mitigation: cache per source family and show per-section timestamps.
- [Risk] Some users may not have OKX financial-product access or funding-account balances. -> Mitigation: show credential/access/unavailable states without breaking the rest of the app.
- [Risk] ETH and SOL staking return different product-info shapes. -> Mitigation: normalize into specialized card models and preserve raw fields for future diagnostics.
- [Risk] Adding another account-adjacent page can crowd navigation. -> Mitigation: keep Earn as a secondary tab under account/finance for the first version.

## Migration Plan

1. Add OKX client methods for On-chain Earn offers, active orders, history, ETH staking, and SOL staking read endpoints.
2. Add normalized backend API endpoints and cache/fallback helpers.
3. Add frontend route/tab state for Earn under the account/finance workflow.
4. Render overview, product list, active/history orders, and ETH/SOL staking panels with section-scoped loading and warnings.
5. Add backend tests for normalization, cache fallback, unconfigured credentials, and endpoint parameter validation.
6. Add frontend static tests for navigation, read-only action boundaries, state labels, and no direct investment wording.
7. Validate with focused backend tests, frontend static tests, build, and a manual local check against configured/unconfigured states.

Rollback can remove the Earn navigation entry and backend endpoints without changing existing market, manual trading, automation, positions, or account data. Any optional cache snapshots can remain unused.

## Open Questions

- Should the top-level navigation rename `Account` to `Finance`, or should Earn start as an `Account` secondary tab?
- Should product offers default to all supported currencies or a small watchlist such as USDT, ETH, SOL, BTC?
- Should APY history default to 30 days or 90 days?
- Should stale fallback persist to the database immediately, or is in-memory cache enough for the first implementation?
- Should future Earn action audit records reuse a generic local order-event table or get a dedicated `earn_action_events` table?
