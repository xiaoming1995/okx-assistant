## Context

The manual `POST /api/market/ai-outlook` flow already builds a server-validated evidence package: selected chart snapshot, ticker, bounded K lines, contract trading statistics, macro context, and independent 15m/1H/1D readings. It calls an OpenAI-compatible chat-completions endpoint with system and user messages, then normalizes structured JSON and falls back to deterministic analysis. The request path currently does not support model tool calls, and the shared LLM configuration is also used by automated strategies.

The upstream `okx-cex-market` Skill is an MIT-licensed instruction document for coding agents to invoke an `okx` CLI. Its public-market scope is useful, but executing its CLI in the dashboard would duplicate existing data access, introduce an uncontrolled subprocess and runtime dependency, and blur the dashboard's read-only analysis boundary.

## Goals / Non-Goals

**Goals:**

- Version a compact, application-owned profile derived from the upstream public-market scope.
- Supply the profile before existing server-validated evidence in every manual AI outlook request.
- Make the profile identity visible in responses, LLM usage audit records, and the report cache identity.
- Keep existing cache/fallback behavior, independent multi-timeframe reading, and manual-only invocation intact.
- Present a compact, accessible provenance line on the existing AI outlook panel.

**Non-Goals:**

- Do not install, invoke, or download the `okx` CLI in application containers.
- Do not provide model tool calling, shell execution, arbitrary URL requests, account data, order actions, bots, Earn actions, leverage, or position sizing.
- Do not add new market-source categories such as order books, funding rates, or arbitrary technical indicators in this change.
- Do not let a profile alter deterministic trends, cache freshness metadata, or the pre-existing read-only report contract.

## Decisions

### Store a small, fixed application profile rather than the upstream full Skill document

Add a backend-owned `okx-market-reading` profile containing upstream repository/path/version/commit/license attribution, an internal profile version, allowed evidence categories, prohibited capabilities, and conservative reporting rules. Its canonical serialized content receives a SHA-256-derived content hash.

The upstream version and commit are constants checked by tests. Runtime requests never reach GitHub and never download a Skill. `NOTICE.md` records MIT attribution and the profile's derivation.

Alternative considered: concatenate the upstream `SKILL.md` into every model prompt. This wastes tokens, contains CLI-oriented instructions that the application cannot execute, and gives no dependable application-level contract.

### Compile the profile into structured prompt context, not a new LLM authority

Create a profile compiler that returns immutable metadata and a bounded list of instruction strings. `market_ai_outlook_prompt` includes that context before `macro_evidence` and `market_evidence`; all evidence remains untrusted data and the existing JSON schema remains authoritative. The hard-coded AI outlook system message stays independent from the editable direct-signal system prompt.

Alternative considered: use the shared configurable `systemPrompt` for profile content. That would couple a read-only report to an automation-oriented configuration and allow an unrelated setting to remove the market-report safety boundary.

### Reuse only existing, server-validated public evidence in phase one

The Profile permits the already-produced ticker, selected chart snapshot/K lines, fixed 15m/1H/1D readings, contract trading statistics, and attributed macro evidence. It explicitly excludes any action or private-data category. The model receives no credentials, command strings, or capability tokens.

Alternative considered: install the upstream CLI so the model can query its full command index. That duplicates clients/cache behavior, makes output depend on subprocess state, and cannot be safely executed by the current chat-completions integration.

### Treat profile identity as part of report provenance and cache identity

All new, cached, and fallback report responses receive `analysisProfile`. The AI cache key includes profile ID, profile version, and content hash, and the prompt version changes. Usage-log context persists profile metadata with a schema migration, so historical LLM calls can be grouped by profile. Older response payloads remain renderable when the frontend field is absent.

Alternative considered: display the version only in the UI. It would not prevent a profile change from reusing an old report and would leave no reliable call-level audit trail.

### Reuse existing low-emphasis source presentation on the AI outlook panel

Add a short source/provenance line inside the existing report source area, using existing type scale, neutral status styling, and no new card or visual language. It says the rule is public-market, read-only, and shows its profile version. The new data is optional in the TypeScript type and hidden if absent.

## Risks / Trade-offs

- [The model may treat evidence text as instructions] → Mark all evidence as data, place immutable rules before it, cap data fields as today, and retain output normalization/filtering.
- [Profile changes make results difficult to compare] → Return and audit version/hash, and invalidate cached reports through the cache key.
- [Upstream document changes] → Pin a reviewed version and commit; update only through a code change with tests and attribution review.
- [The small profile appears to promise unavailable upstream commands] → List only evidence already collected by the dashboard and test its allow-list.
- [UI provenance distracts from the report] → Use one compact line in the existing source/reference section, not a new control or panel.

## Migration Plan

1. Add the profile module, attribution document, tests, and the database migration for usage-log metadata.
2. Thread profile metadata through prompt construction, cache identity, LLM usage context, normal/fallback/cached responses, and API response types.
3. Render the optional provenance line and validate desktop/narrow, loading, refresh-retained, fallback, disabled, and focus states.
4. Deploy with the profile active by default. No user action or existing report URL changes are required.
5. Roll back by removing the profile injection and response field; the existing deterministic fallback and prior UI contract continue to work. Database metadata columns may remain harmlessly after rollback.

## Open Questions

- None for the phase-one read-only profile. Model-directed tool calls remain a separate future change.
