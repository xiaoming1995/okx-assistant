## Context

The current automation module has a working first loop: strategies can be created, edited, toggled, manually run, evaluated on a background interval, and either recorded as signals or submitted to OKX simulated trading. It supports `ma_cross` and `llm_direct`, with automatic execution limited to `simulated_auto`.

The current safety model is useful but mostly local to each strategy evaluation. Risk checks are computed at runtime, signals persist a compact result plus raw JSON, and the automation status exposes a single transient warning. This makes the module usable for experimentation, but weak for longer-running unattended operation because users cannot reliably review the exact risk checks, execution steps, alerts, or global safety state that existed when a signal was evaluated.

## Goals / Non-Goals

**Goals:**

- Define an explicit `automation-trading` capability covering lifecycle, execution modes, risk controls, audit trails, alerts, and simulated-only execution.
- Add durable global safety controls: pause-all and circuit-breaker state.
- Persist risk check snapshots for every executable automation signal.
- Persist automation alerts so important failures and blocks remain visible after refresh.
- Extend signal detail responses and UI with audit evidence.
- Support archiving strategies without deleting historical signals.
- Preserve the existing simulated-only automatic execution boundary.

**Non-Goals:**

- Do not add live automatic trading.
- Do not let LLM output bypass deterministic risk checks.
- Do not automatically create, enable, or run strategies from Contract Radar results.
- Do not add many new strategy templates in this change.
- Do not make external notifications mandatory.
- Do not delete historical signals, order events, or audit records when a strategy is archived.

## Decisions

### Decision: Store global automation safety state separately from transient loop status

Add durable state for global pause and circuit breaker information, including active flags, reason, trigger time, resume time, and update time. This can use `app_settings` for the first implementation or a small dedicated table if the migration remains simple.

Rationale: `automation_state` is process-local and represents the running loop. Pause and circuit breaker state are product state and must survive process restarts.

Alternative considered: reuse `automation_state["warning"]`. That is insufficient because it is transient, single-valued, and cannot represent manual recovery requirements.

### Decision: Check global controls before strategy execution

The automation loop should exclude archived strategies and evaluate global pause or circuit breaker state before attempting automatic execution. If a strategy produces a signal while global execution is blocked, the system should record the blocked decision and risk evidence without submitting an order.

Rationale: global controls must have higher priority than individual strategy `enabled` state.

Alternative considered: only disable strategy toggles in the UI. That does not protect API-triggered runs, background polling, or stale browser state.

### Decision: Persist risk snapshots as first-class audit data

Each long or short signal that reaches risk evaluation should persist the risk preview data used for the final decision: allowed, severity, message, checks, current position, projected position, cooldown, LLM confidence, and account source.

Rationale: users need to inspect why a signal was allowed, blocked, skipped, or failed after the fact. Raw JSON alone is hard to query and hard to render consistently.

Alternative considered: keep risk checks embedded only in signal `raw_json`. This preserves data but makes the audit trail implicit and difficult to evolve.

### Decision: Add durable automation alerts

Create alert records for engine errors, LLM failures, OKX failures, risk blocks, order failures, circuit breaker triggers, and important safety state changes. Alerts should have severity, source, message, related ids, created time, acknowledged time, and raw metadata.

Rationale: automation users should not have to keep the page open to know that the engine blocked or failed. A persistent alert list gives the UI and future notification channels a common source.

Alternative considered: display only current status warning. That loses history and cannot distinguish active alerts from acknowledged historical events.

### Decision: Archive strategies instead of deleting them

Add archive and restore behavior for strategies. Archived strategies do not participate in polling and are hidden from active lists by default, but remain available for historical signal detail and audit review. Restored strategies return paused.

Rationale: trading strategy history is operational evidence. Removing it would make old signals harder to explain.

Alternative considered: implement hard delete. This is simpler but creates audit and support problems.

### Decision: Keep simulated execution boundaries unchanged

`signal_only` continues to record signals without orders. `simulated_auto` remains the only automatic order submission mode. Real-money trading remains manual-only in this change.

Rationale: hardening safety and audit should precede any real-money automation discussion.

Alternative considered: introduce `live_auto` with stronger controls in the same change. That combines too much risk and would blur validation scope.

## Risks / Trade-offs

- [Risk] The change adds several persistence concepts at once. -> Mitigation: ship the MVP in ordered slices: global pause, archive, risk snapshots, signal detail; then alerts and execution steps.
- [Risk] Existing signals lack risk snapshots. -> Mitigation: render legacy signals with a clear "audit snapshot unavailable" state and preserve existing raw JSON display paths.
- [Risk] Circuit breaker rules may be too aggressive or too weak initially. -> Mitigation: start with explicit state and manual recovery, then add automatic trigger thresholds with focused tests.
- [Risk] Alert volume may become noisy. -> Mitigation: deduplicate repeated engine and provider failures by source, strategy, and time window before creating new active alerts.
- [Risk] Users may expect archive to delete records. -> Mitigation: label archive as hiding from active automation while preserving history.

## Migration Plan

1. Add storage for global automation state, archived strategy flags, risk snapshots, execution steps, and alerts with backwards-compatible defaults.
2. Update backend automation queries to ignore archived strategies during polling.
3. Add global pause and resume APIs, then enforce those checks in background and manual strategy runs.
4. Persist risk snapshots during signal evaluation and include them in signal detail responses.
5. Add alert creation and acknowledgement APIs.
6. Update automation overview, strategy management, and signal detail UI.
7. Validate with backend tests, frontend static tests, production build, and manual local checks.

Rollback should hide new UI controls and stop writing new audit tables while keeping existing signal, strategy, and order behavior intact. New audit records can remain unused if the feature is disabled.

## Open Questions

- Should the first circuit breaker trigger automatically on failed order count, failed LLM count, daily loss, or only manual activation?
- Should risk snapshots be stored in one JSON column initially, or normalized into check rows immediately?
- Should archived strategies remain searchable from the main strategy page by default filter, or only through an archived filter?
- Should alert acknowledgement be per alert only, or should the UI support acknowledge-all for low-severity alerts?
