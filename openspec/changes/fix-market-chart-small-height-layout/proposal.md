## Why

On shorter desktop browser heights, the market chart page clips the lower metric row because the page uses a fixed viewport shell with hidden overflow. Users cannot reliably see the bottom market statistics row after the chart.

## What Changes

- Add responsive handling for short desktop-height market chart layouts.
- Let the right market content area scroll vertically when its content exceeds the available viewport height.
- Compress the chart minimum height only on short desktop-height screens so the chart remains usable while the lower metrics stay reachable.
- Keep the existing desktop two-column market layout and mobile responsive behavior.
- Add focused frontend verification for the small-height layout.

## Capabilities

### New Capabilities
- `market-chart-small-height-layout`: The market chart page adapts to short viewport heights without hiding the bottom metrics.

### Modified Capabilities

## Impact

- Affected frontend code: market chart CSS layout rules and focused static layout tests.
- Runtime validation: browser viewport checks around the reported short-height desktop size.
- No backend, API, dependency, or data model changes.
