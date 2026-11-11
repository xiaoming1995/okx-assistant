# Mantine UI migration inventory

This inventory records presentation replacement boundaries only. Existing route state, API calls, subscriptions, cache/refresh ownership, and safety behavior remain in their current domain components.

| Route family | Current state owner | Mantine replacement target | State and responsive constraints |
| --- | --- | --- | --- |
| Application shell and primary navigation | `App` | `AppShell`, `NavLink`, `Tabs`, `ActionIcon` | Preserve all existing hash destinations and active-route state; narrow navigation must retain all destinations. |
| Market contract workbench | `MarketContractWorkspace` | shared workbench layout, dense toolbar, `TextInput`, `SegmentedControl`, `Menu`, `ActionIcon`, `ScrollArea`, `Skeleton` | Preserve selected contract, watchlist, search, filters, sort, collapse state, chart period, subscriptions, and retained refresh. |
| Market chart, statistics, AI outlook | `MarketPage`, `MarketStatsPage`, `MarketAiOutlookPage` | shared page header, `Paper`, `Tabs`, `Badge`, `Alert`, `Skeleton`, status pattern | Keep `lightweight-charts`, manual AI trigger, per-period data, cache and error semantics. |
| Radar, announcements, US events | `ContractRadarPage`, `AnnouncementsPage`, `UsMarketTimelinePage` | shared page/header, form controls, data rows/table, alert/empty/loading patterns | Preserve date/filter/query behavior and event provenance/cache labels. |
| Trading | `TradingPage` | shared form, toolbar, table, confirmation/status patterns | Preserve validation, order submission behavior, configured/disabled states, and no additional trading capability. |
| Automation | `CleanAutomationPage`, `AutomationPage`, `StrategyListPage`, `SignalLogPage`, `SignalDetailPage` | shared page/header, data table, menus, dialogs, status/feedback patterns | Preserve strategy and signal actions, action permissions, and route/detail state. |
| Account and Earn | `PositionsPage`, `AccountPage`, `EarnPage` | shared metric, table, status/feedback, filter patterns | Preserve complete snapshot during refresh, PnL semantics, read-only Earn boundary, cache/unavailable copy. |
| AI settings and usage | `LlmSettingsPage`, `LlmUsagePage` | shared forms, tables, status and confirmation patterns | Preserve configuration validation, submit/disabled behavior and usage filters. |

The shared foundation is intentionally introduced before route migration. During a route migration, all common visible controls in that route must use the Mantine pattern rather than mixing a legacy equivalent beside it.

## Retained layout CSS boundary

After the Mantine migration, `styles.css` still owns the data-dense chart and contract-rail geometry, table column widths and horizontal scrolling, the US-event date strip, and responsive arrangement of trading, automation, account, and AI-report workspaces. These are domain-specific layouts or chart integrations, not alternate button, input, table, alert, or dialog implementations. Shared controls and feedback render through Mantine; route CSS may arrange their content and express domain-specific selection or semantic states using the documented design tokens. The unreferenced legacy control/card selector families were removed after their JSX consumers migrated.
