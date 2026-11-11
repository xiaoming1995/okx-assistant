## Why

The automation module can already create strategies, generate signals, preview risk, and submit OKX simulated orders, but its safety contract is still implicit in code and transient UI state. Before adding more strategy types, radar-driven candidates, or any real-money automation discussion, the system needs explicit automation requirements, global controls, durable risk evidence, alerts, and audit trails.

## What Changes

- Add an `automation-trading` capability that defines automated strategy lifecycle, execution modes, risk controls, audit trails, alerts, and backtesting boundaries.
- Add global automation safety controls so users can pause all automated execution and recover manually from circuit-breaker states.
- Persist strategy risk check snapshots for executable signals so each allow/block decision can be reviewed later.
- Persist automation alerts for engine, strategy, risk, OKX, LLM, and order failures instead of relying only on transient status warnings.
- Extend signal detail data so users can inspect the risk snapshot and execution path for observed, blocked, skipped, failed, and submitted signals.
- Add strategy archive and restore behavior without deleting historical signals or audit records.
- Keep automatic execution limited to OKX simulated trading; live automatic trading remains out of scope.

## Capabilities

### New Capabilities

- `automation-trading`: Manages automated strategy configuration, signal generation, simulated execution, global risk controls, audit records, alerts, and strategy lifecycle boundaries.

### Modified Capabilities

- None.

## Impact

- Backend automation APIs need global safety state, alert, archive, risk snapshot, and richer signal detail behavior.
- Database storage needs durable automation safety, alert, risk snapshot, execution audit, and archive fields or tables.
- Frontend automation overview, strategy management, and signal detail views need controls and status surfaces for global pause, alerts, archives, and risk audit data.
- Existing `signal_only` and `simulated_auto` behavior must remain compatible, with no live automatic execution mode added.
- Tests should cover global pause, circuit breaker, archive exclusion from polling, risk snapshot persistence, alert generation, signal detail audit payloads, and unchanged simulated-only execution boundaries.
