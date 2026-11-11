## Context

`frontend/src/main.tsx` holds the shared market-workspace requests and most data pages. The AI report has a local loading implementation, but the shared workspace does not distinguish initial requests from refreshes. Other pages often expose only a title string such as “加载中”, while their content areas render default empty values.

The existing frontend design guideline requires a corresponding loading state on first load, retained complete data during refresh, Chinese recoverable errors, reduced-motion support, and accessible important state changes.

## Goals / Non-Goals

**Goals:**

- Use one small, reusable visual pattern for compact list, metric and chart loading states.
- Expose explicit initial and refreshing state from the shared market workspace.
- Keep valid data visible during polling or user-triggered refreshes.
- Make unavailable actions visibly disabled with an explanatory label.
- Apply the pattern first to high-frequency market flows, then to list and account data pages without changing their APIs.

**Non-Goals:**

- Do not add artificial percentages, delays, global blocking overlays, or new polling schedules.
- Do not alter market calculations, account permissions, trading behavior, or API response formats.
- Do not replace valid empty states with loading states after a request has completed.

## Decisions

### 1. Model initial and refresh states separately

Each request surface derives `initialLoading` from an in-flight request with no complete data and `refreshing` from an in-flight request with existing data. Initial loading uses a shaped placeholder; refreshing retains content and adds a compact status indicator. This follows the existing AI-report behavior and avoids confusing a refreshed empty payload with a request still in progress.

An overlay across the whole application was rejected because it blocks unrelated controls and causes excessive motion.

### 2. Put market request state in the shared workspace

The contract list, ticker snapshot and K-line snapshot are shared by the chart, AI-outlook and statistics pages. Their request state belongs in `MarketContractWorkspace` context, so all consumers receive the same truth and no page invents a separate timing heuristic.

Duplicating booleans in each consumer was rejected because route switches and background refreshes would then disagree.

### 3. Reuse low-distraction loading primitives

The implementation adds a compact spinner/status row and structural skeleton variants using the existing neutral surfaces, 4px spacing grid, and reduced-motion rule. They carry `role="status"` only for meaningful state text; decorative skeleton bars remain hidden from assistive technology.

New page-specific animations were rejected to keep the interface visually consistent and to avoid animation noise in a data-dense tool.

### 4. Preserve the last complete snapshot on refresh

Market statistics and account/list requests retain their last successful result while refreshing. A failure leaves that result visible when available and presents the existing warning/error treatment. First-load failures use the normal Chinese error state instead of a perpetual skeleton.

## Risks / Trade-offs

- [More state fields in the workspace] → Keep them request-scoped and expose them only through the existing context snapshot.
- [Skeleton dimensions may drift from content] → Use the same rail rows, hero tiles and chart panel dimensions as their rendered counterparts.
- [Frequent polling may over-announce] → Announce only initial loading and user-visible refresh operations; passive refresh badges are not assertive.

## Migration Plan

1. Add shared loading primitives and workspace request state.
2. Apply and test the market chart, AI-outlook and statistics surfaces.
3. Apply compact initial/refresh feedback to list and account data surfaces.
4. Build and inspect desktop and narrow layouts with initial, refreshing, error, empty and disabled states.

The change is front-end only. Rollback consists of reverting the affected frontend and OpenSpec change files; APIs and stored data remain unchanged.

## Open Questions

None. The UI reports known request states only and does not claim unobservable backend progress.
