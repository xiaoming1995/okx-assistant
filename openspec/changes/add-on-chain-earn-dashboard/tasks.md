## 1. Backend OKX Client

- [x] 1.1 Add read-only generic On-chain Earn client methods for offers, active orders, and historical orders.
- [x] 1.2 Add read-only ETH staking client methods for product info, balance, purchase/redeem history, and APY history.
- [x] 1.3 Add read-only SOL staking client methods for product info, balance, purchase/redeem history, and APY history.
- [x] 1.4 Ensure all authenticated Earn methods reuse existing environment credential handling and OKX request signing.

## 2. Backend Normalization And APIs

- [x] 2.1 Add normalized response builders for Earn product offers, active orders, and historical orders.
- [x] 2.2 Add normalized response builders for ETH staking overview, history, and APY points.
- [x] 2.3 Add normalized response builders for SOL staking overview, history, and APY points.
- [x] 2.4 Add read-only backend endpoints for Earn offers, active orders, order history, ETH staking, and SOL staking.
- [x] 2.5 Validate and clamp query parameters such as currency filters, product id, state/status, pagination fields, limit, and APY history days.
- [x] 2.6 Return section-scoped unconfigured credential responses for authenticated Earn endpoints.

## 3. Cache And Failure Handling

- [x] 3.1 Add cache keys that separate Earn source family, selected environment, filters, pagination, and APY days.
- [x] 3.2 Return stale cached Earn data with warning and cache-age metadata when live refresh fails.
- [x] 3.3 Keep partial failures isolated so one failed Earn source does not hide successful Earn sections.
- [x] 3.4 Verify Earn request failures do not affect existing account, position, market, trading, or automation endpoint behavior.

## 4. Frontend Navigation And Data Model

- [x] 4.1 Add an Earn tab or entry under the account/finance workflow while preserving existing primary workflows.
- [x] 4.2 Add TypeScript types for normalized Earn products, orders, staking cards, staking histories, APY points, and section warnings.
- [x] 4.3 Add frontend fetch helpers or page-local loaders for all read-only Earn endpoints.
- [x] 4.4 Preserve current selected section/tab behavior when users move between Earn, Account, and Positions.

## 5. Frontend Earn Workspace

- [x] 5.1 Render an Earn overview with connection state, timestamps, stale warnings, active order summary, and ETH/SOL staking summary.
- [x] 5.2 Render a product-offer table or panel with currency, protocol, term, APY, state, min/max amount, redeem period, and fast redemption limit.
- [x] 5.3 Render active Earn orders with readable state labels, invested amounts, earnings, timing fields, tag, and raw-state preservation.
- [x] 5.4 Render historical Earn orders with pagination controls and completed-order labels.
- [x] 5.5 Render ETH staking product info, BETH balance, ETH staking history, and ETH APY history.
- [x] 5.6 Render SOL staking product info, OKSOL balance, SOL staking history, and SOL APY history.
- [x] 5.7 Add loading, empty, warning, stale, and unconfigured states per Earn section.

## 6. Read-Only Safety Boundary

- [x] 6.1 Ensure the first-version UI contains no Earn purchase, redeem, cancel, or staking action submission controls.
- [x] 6.2 Ensure backend routes added in this change are GET/read-only and do not call OKX mutation endpoints.
- [x] 6.3 Add explicit tests or static assertions that Earn data is not wired into automation, radar executable actions, or LLM-triggered actions.
- [x] 6.4 Document the future Earn mutation boundary with separate enablement, confirmation, and audit requirements.

## 7. Tests And Validation

- [x] 7.1 Add backend tests for OKX Earn normalization, state labels, query validation, unconfigured credentials, cache fallback, and partial failures.
- [x] 7.2 Add frontend static tests for navigation, Earn page sections, state labels, read-only controls, and no direct investment wording.
- [x] 7.3 Run focused backend tests for Earn and existing account/market safety-adjacent behavior.
- [x] 7.4 Run frontend static tests and production build.
- [x] 7.5 Run `git diff --check` and a final keyword search for forbidden first-version mutation wiring.
