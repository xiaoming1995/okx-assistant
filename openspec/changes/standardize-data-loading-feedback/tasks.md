## 1. Shared loading primitives

- [x] 1.1 Add reduced-motion-safe, accessible compact status and neutral skeleton primitives using the existing spacing and surface tokens.
- [x] 1.2 Add static coverage for the reusable loading feedback contract.

## 2. Shared market workspace

- [x] 2.1 Track independent initial and refresh states for instruments, tickers, and K-line snapshots in `MarketContractWorkspace` context.
- [x] 2.2 Render a loading-aware contract rail and prevent duplicate list refresh actions.
- [x] 2.3 Render loading-aware market summaries and a labelled chart loading layer without hiding valid data during refresh.

## 3. Market details

- [x] 3.1 Disable AI analysis until a usable chart snapshot is ready and render an explanatory snapshot-preparation state.
- [x] 3.2 Preserve existing trading statistics during refresh and render shaped initial metric placeholders.

## 4. List and account pages

- [x] 4.1 Add first-load and retained-refresh feedback to American events and announcements.
- [x] 4.2 Add consistent first-load and refresh feedback to Earn, positions, and account data pages.
- [x] 4.3 Add first-load feedback to automation, signal, and LLM data pages where a title-only status currently masks empty content.

## 5. Verification

- [x] 5.1 Extend static tests for market workspace, AI-outlook, trading-statistics, list, and account loading states.
- [x] 5.2 Run targeted tests and the production frontend build.
- [x] 5.3 Verify desktop and narrow layouts for initial loading, refresh, error/empty, focus, and disabled states.
