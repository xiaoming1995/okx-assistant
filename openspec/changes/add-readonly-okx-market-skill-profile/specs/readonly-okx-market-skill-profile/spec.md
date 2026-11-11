## ADDED Requirements

### Requirement: Fixed Read-Only OKX Market Skill Profile
The system SHALL define a backend-owned `okx-market-reading` Skill Profile for manual AI outlook analysis. The Profile MUST expose an internal profile version, content hash, upstream repository/path/version/commit attribution, and MIT license attribution. The application MUST NOT download an upstream Skill, install an `okx` CLI, or execute a shell command while loading or applying the Profile.

#### Scenario: Manual analysis applies the Profile
- **WHEN** a user manually requests an AI outlook with a valid chart snapshot
- **THEN** the backend MUST load the fixed Profile before creating the model request
- **AND** the request context MUST identify the Profile's ID, version, content hash, and public-read-only policy

#### Scenario: Profile metadata is invalid
- **WHEN** the fixed Profile cannot pass its local validation
- **THEN** the system MUST NOT call the LLM without the Profile
- **AND** it MUST return the existing read-only deterministic fallback with a user-readable warning

### Requirement: Profile Constrains Evidence and Capabilities
The Profile SHALL permit only server-validated public ticker data, selected chart snapshots and bounded K lines, independent 15m/1H/1D trend readings, contract trading statistics, and attributed macro evidence already collected by the dashboard. It MUST prohibit account data, positions, orders, leverage, transfers, Earn, bots, private credentials, arbitrary URLs, model tool calls, and shell command execution.

#### Scenario: Model receives an AI outlook request
- **WHEN** the backend constructs the AI outlook prompt
- **THEN** it MUST place immutable read-only Profile rules before evidence payloads
- **AND** it MUST treat all evidence payloads as data rather than instructions
- **AND** it MUST retain the existing structured JSON output contract and output safety normalization

#### Scenario: A requested capability is outside the Profile
- **WHEN** analysis would require a private or action-oriented capability
- **THEN** the Profile MUST NOT grant that capability to the model
- **AND** the response MUST remain an observational, non-executing report

### Requirement: Profile Provenance Is Auditable and Cache-Safe
Every AI outlook result generated with the Profile SHALL include `analysisProfile` metadata. The AI outlook cache key and prompt version MUST include the Profile identity/version/hash so a Profile update cannot reuse a prior report. LLM usage records for an attempted AI outlook call MUST retain the applied Profile identity/version/hash.

#### Scenario: Cached report matches the current Profile
- **WHEN** a fresh report cache entry matches the market evidence, macro evidence, and current Profile identity/version/hash
- **THEN** the system MAY return the cached report
- **AND** the report MUST expose the applied `analysisProfile` metadata

#### Scenario: Profile changes
- **WHEN** the Profile version or content hash differs from the profile used to create a cached report
- **THEN** the system MUST NOT return that cached report for a new analysis request

#### Scenario: LLM is unavailable
- **WHEN** the LLM is disabled, fails, or returns invalid structured output after a valid Profile was applied
- **THEN** the deterministic fallback report MUST retain the same `analysisProfile` metadata
- **AND** the result MUST remain read-only

### Requirement: AI Outlook Displays Profile Provenance Without Disrupting Reading
The AI outlook page SHALL display a compact, user-readable indication that an available report used the public-market read-only Profile and its version. It MUST preserve backwards compatibility for older responses that lack profile metadata and MUST NOT add an automatic analysis request or an execution control.

#### Scenario: A report includes Profile metadata
- **WHEN** the AI outlook response includes `analysisProfile`
- **THEN** the existing source/reference area MUST display its public read-only status and profile version
- **AND** the information MUST remain visible during a retained-data refresh

#### Scenario: An older report lacks Profile metadata
- **WHEN** the frontend renders an AI outlook response without `analysisProfile`
- **THEN** it MUST render the report normally without an empty or misleading provenance line
