## Why

The market chart page now contains price context, K-line data, trading-structure summary, and multiple statistics detail panels, which makes the desktop layout exceed the visible workspace and clips lower content. Users need the chart to stay focused while still having a dedicated place to inspect complete per-contract trading statistics.

## What Changes

- Keep the market chart page focused on selected-contract price, K-line, and a compact trading-structure summary.
- Move the full trading-statistics detail panels into a dedicated contract trading data page.
- Add a clear entry from the market chart summary to the full trading data view for the currently selected contract.
- Preserve the existing normalized `GET /api/market/stats` API and selected-contract data semantics.
- Keep all trading-statistics language observational and avoid direct buy, sell, long, or short instructions.

## Capabilities

### New Capabilities
- `market-contract-trading-stats-detail-view`: Defines the dedicated contract trading data view and the chart-page summary entry behavior.

### Modified Capabilities
- None.

## Impact

- Affected frontend code: market chart layout, route/navigation handling, trading-statistics detail rendering, and focused frontend tests.
- Affected backend code: none expected; reuse the existing normalized market stats endpoint.
- APIs: no API contract changes expected.
- Systems: market observation workflow only; no changes to trading execution or automation decisions.
