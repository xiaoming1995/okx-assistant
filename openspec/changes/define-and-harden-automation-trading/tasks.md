## 1. OpenSpec and Scope Confirmation

- [x] 1.1 Validate the new `automation-trading` capability spec for execution modes, global controls, risk snapshots, alerts, audit trail, archives, radar handoff, and backtesting boundaries.
- [x] 1.2 Confirm the implementation keeps automatic execution limited to `simulated_auto` and does not add live automatic trading.
- [x] 1.3 Confirm legacy strategy and signal records remain readable without structured audit data.

## 2. Backend Storage

- [x] 2.1 Add durable storage for global automation pause and circuit-breaker state.
- [x] 2.2 Add archive fields to automation strategies with backwards-compatible defaults.
- [x] 2.3 Add storage for automation risk snapshots linked to strategy and signal ids.
- [x] 2.4 Add storage for automation execution steps linked to strategy, signal, and order event ids where available.
- [x] 2.5 Add storage for automation alerts with severity, source, message, related ids, acknowledgement state, and raw metadata.
- [x] 2.6 Add database tests covering new storage, default values, and legacy read compatibility.

## 3. Backend Global Safety

- [x] 3.1 Extend automation status payload with global pause, circuit-breaker, and active alert counts.
- [x] 3.2 Add pause-all and resume APIs for global automation safety state.
- [x] 3.3 Enforce global pause before automatic order submission from background runs and manual strategy runs.
- [x] 3.4 Add circuit-breaker state handling that blocks automated execution until manually resumed.
- [x] 3.5 Generate audit records and alerts when global safety controls block execution.

## 4. Backend Strategy Lifecycle

- [x] 4.1 Add strategy archive and restore APIs.
- [x] 4.2 Exclude archived strategies from automation polling and active strategy lists by default.
- [x] 4.3 Restore archived strategies in paused state.
- [x] 4.4 Preserve archived strategy signals and signal detail lookup.
- [x] 4.5 Add backend tests for archive, restore, polling exclusion, and preserved history.

## 5. Backend Risk and Execution Audit

- [x] 5.1 Persist risk check snapshots for long and short signals before execution decisions are finalized.
- [x] 5.2 Include risk snapshot data in signal detail responses.
- [x] 5.3 Persist execution steps for open, reverse, close-opposite, skip-same-direction, take-profit, stop-loss, and failed order flows.
- [x] 5.4 Include execution steps in signal detail responses.
- [x] 5.5 Render legacy signal detail payloads without failing when risk snapshots or execution steps are missing.
- [x] 5.6 Add backend tests for allowed, blocked, skipped, failed, reverse, take-profit, and stop-loss audit paths.

## 6. Backend Alerts

- [x] 6.1 Create alerts for engine loop errors, LLM failures, OKX failures, order failures, risk blocks, global pause, and circuit-breaker triggers.
- [x] 6.2 Deduplicate repeated active alerts by source, strategy, signal, and recent time window where appropriate.
- [x] 6.3 Add alert list API with active, acknowledged, severity, and source filters.
- [x] 6.4 Add alert acknowledgement API that preserves history but removes the alert from active counts.
- [x] 6.5 Add backend tests for alert creation, filtering, acknowledgement, and status counts.

## 7. Frontend Automation Overview

- [x] 7.1 Show global automation state, pause reason, circuit-breaker reason, and active alert counts in Automation Overview.
- [x] 7.2 Add pause-all and resume controls with clear disabled/loading/error states.
- [x] 7.3 Show recent active alerts in Automation Overview.
- [x] 7.4 Keep the overview compact and preserve the current status plus key metrics layout.

## 8. Frontend Strategy Management

- [x] 8.1 Add strategy archive and restore actions.
- [x] 8.2 Add active, paused, and archived filters without mixing archived strategies into the default active list.
- [x] 8.3 Show restored strategies as paused and require a separate start action.
- [x] 8.4 Preserve existing create, edit, toggle, run-once, and pagination behavior.

## 9. Frontend Signal Detail and Alerts

- [x] 9.1 Show risk snapshot checks in Signal Detail, including pass, warning, and block states.
- [x] 9.2 Show execution steps in Signal Detail for submitted, skipped, failed, reverse, take-profit, and stop-loss paths.
- [x] 9.3 Show a legacy fallback state when structured audit data is unavailable.
- [x] 9.4 Add alert list and acknowledgement UI if it fits the implemented alert API scope.

## 10. Validation

- [x] 10.1 Run OpenSpec strict validation for `define-and-harden-automation-trading`.
- [x] 10.2 Run backend automation, database, OKX, and radar tests.
- [x] 10.3 Run frontend static tests.
- [x] 10.4 Run frontend production build.
- [x] 10.5 Manually verify global pause, archive/restore, risk snapshot display, alert display, and signal audit detail in the local app.
- [x] 10.6 Confirm no live automatic trading mode or live automatic order path was added.
