## Why

The top navigation currently exposes too many operational pages at the same level, which makes the product feel busy and makes common workflows harder to scan. The app now has market discovery, trading, automation, account, and AI operations, so navigation should group related pages into clearer primary areas.

This change simplifies the main navigation into five top-level sections and moves secondary pages into contextual tabs or actions within their parent areas.

## What Changes

- Replace the current many-item top navigation with five primary entries: Market, Trade, Automation, Account, and Settings.
- Group Contract Radar and Market Chart under Market, with Contract Radar as the default market view.
- Keep Manual Trade as a dedicated Trade entry because it is a high-risk action surface.
- Group Automation Overview, Strategy Management, and Signal Logs under Automation.
- Group Positions and Account Management under Account.
- Group AI Configuration and AI Usage under Settings.
- Preserve existing deep workflow behavior, including opening a selected radar contract in market, trade, or automation.
- Ensure active navigation state reflects both primary section and secondary tab.

## Capabilities

### New Capabilities

- `main-navigation`: Defines the simplified top-level navigation model and contextual secondary navigation behavior.

### Modified Capabilities

- None.

## Impact

- Frontend page state and routing logic in `frontend/src/main.tsx`.
- Header navigation rendering and active-state logic.
- Existing page components may need lightweight wrappers or secondary tab controls.
- CSS for top navigation, secondary tabs, and responsive behavior.
- Frontend smoke tests must be updated to assert the simplified navigation and retained access to merged pages.
