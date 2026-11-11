## ADDED Requirements

### Requirement: Position snapshots survive transient upstream interruption
The system SHALL retain and return the last complete account-and-position snapshot for the active environment when an OKX account refresh is interrupted. It MUST NOT expose raw upstream transport exception text in an API warning, error detail, or rendered user interface.

#### Scenario: A complete memory snapshot exists when a refresh fails
- **WHEN** an account or positions refresh fails after a complete in-memory snapshot was saved
- **THEN** `GET /api/account` returns that snapshot with a display-safe Chinese freshness warning and a degraded refresh state

#### Scenario: Only a persisted snapshot exists when a refresh fails
- **WHEN** no complete in-memory snapshot exists but a complete snapshot has been persisted for the active environment
- **THEN** `GET /api/account` returns the persisted snapshot with its timestamp, a display-safe Chinese freshness warning, and no raw transport exception text

#### Scenario: No complete snapshot exists when a refresh fails
- **WHEN** an account refresh fails and no complete memory or persisted snapshot is available
- **THEN** the API reports an explicit unavailable state using a display-safe Chinese message and does not return partial account or position data

### Requirement: Account refresh retries are bounded and observable
The system SHALL permit at most one background account refresh per environment at a time and SHALL defer repeated failed refresh jobs using a capped retry deadline. Account responses SHALL include structured refresh state and cache-age metadata that the client can render without parsing error strings.

#### Scenario: A stale snapshot enters retry backoff
- **WHEN** a background refresh of a stale complete snapshot fails
- **THEN** subsequent account requests return the retained snapshot without starting another job before the retry deadline

#### Scenario: A later refresh succeeds
- **WHEN** a deferred account refresh succeeds
- **THEN** the response becomes current and its failure count and retry deadline are cleared

