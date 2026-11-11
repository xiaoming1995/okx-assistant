## Why

OKX trading-statistics endpoints can intermittently return incomplete bodies, especially the contract taker-volume endpoint. The current page correctly keeps successful metrics, but users only see a generic partial state and have to wait or refresh the whole page to recover.

## What Changes

- Keep each contract trading-stat metric independently resilient when one OKX statistics request fails.
- Reuse the last successful value for a failed metric when a matching stale metric cache exists.
- Show clearer partial-data warnings that identify the failed metric and whether cached metric data is being displayed.
- Add a manual retry action on the trading statistics panel that refreshes the selected contract and period without reloading the whole page.
- Extend focused backend and frontend tests for partial metric cache fallback and retry wiring.

## Capabilities

### New Capabilities
- `market-stats-partial-recovery`: Contract trading statistics can recover gracefully from single-metric OKX failures and expose a user-triggered retry path.

### Modified Capabilities

## Impact

- Affected backend code: normalized market stats endpoint, per-metric cache state, OKX retry timing, focused backend tests.
- Affected frontend code: market stats hook, summary panel warning/retry controls, static frontend tests.
- No new external dependencies or database migrations.
