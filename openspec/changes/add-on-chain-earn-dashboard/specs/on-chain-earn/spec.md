## ADDED Requirements

### Requirement: Earn Navigation
The system SHALL provide a clear On-chain Earn entry within the account or finance workflow.

#### Scenario: Open Earn workspace
- **WHEN** the user selects the On-chain Earn entry
- **THEN** the system displays an Earn workspace without leaving the local dashboard
- **AND** existing Market, Trade, Automation, Account, and Settings workflows remain reachable.

#### Scenario: Preserve finance context
- **WHEN** the user views Earn data
- **THEN** the displayed page identifies the data as OKX financial-product and staking information
- **AND** the page does not present Earn products as SWAP contracts or automated trading strategies.

### Requirement: Earn Read Only Boundary
The system SHALL keep the first On-chain Earn implementation read-only.

#### Scenario: First version contains no purchase action
- **WHEN** the user views an On-chain Earn product that is purchasable
- **THEN** the system displays product availability and investment limits
- **AND** the system does not display or submit an Earn purchase form.

#### Scenario: First version contains no redeem action
- **WHEN** the user views an active earning or redeemable order
- **THEN** the system displays order state, amount, earnings, and relevant timing
- **AND** the system does not display or submit an Earn redeem or cancel form.

#### Scenario: Automation cannot trigger Earn actions
- **WHEN** automation strategies, radar analysis, or LLM analysis produce market observations
- **THEN** the system MUST NOT create, recommend as an executable command, or submit On-chain Earn purchase, redeem, or cancel requests.

### Requirement: Product Offers
The system SHALL retrieve and display OKX On-chain Earn product offers.

#### Scenario: Load product offers
- **WHEN** the user opens the Earn product list with configured OKX credentials
- **THEN** the backend requests OKX On-chain Earn offers
- **AND** the frontend displays product id, currency, protocol, protocol type, term, estimated APY, state, investment limits, earnings currencies, redeem period, and fast redemption limit when available.

#### Scenario: Filter product offers
- **WHEN** the user filters offers by currency, product id, or protocol type
- **THEN** the backend passes supported filters to the OKX offers request
- **AND** the displayed product list is scoped to those filters.

#### Scenario: Product state labels
- **WHEN** a product offer has state `purchasable`, `sold_out`, or `stop`
- **THEN** the UI displays a readable state label for available, sold out, or paused
- **AND** the raw state remains available in the normalized response for diagnostics.

### Requirement: Active Earn Orders
The system SHALL retrieve and display active OKX On-chain Earn orders.

#### Scenario: Load active orders
- **WHEN** the user opens active Earn orders with configured OKX credentials
- **THEN** the backend requests active On-chain Earn orders
- **AND** the frontend displays order id, currency, product id, protocol, term, APY, invested amounts, earnings data, purchase time, estimated settlement time, cancel-redemption deadline, tag, and fast-redemption data when available.

#### Scenario: Active order state labels
- **WHEN** an active order state is `8`, `13`, `9`, `1`, or `2`
- **THEN** the UI displays a readable state label for waiting, cancelling, on-chain processing, earning, or redeeming
- **AND** the raw state remains available in the normalized response.

#### Scenario: Empty active orders
- **WHEN** OKX returns no active On-chain Earn orders
- **THEN** the system displays an empty state for active Earn orders
- **AND** the rest of the Earn workspace remains visible.

### Requirement: Earn Order History
The system SHALL retrieve and display historical OKX On-chain Earn orders with pagination support.

#### Scenario: Load order history
- **WHEN** the user opens Earn order history
- **THEN** the backend requests historical On-chain Earn orders using supported filters and pagination parameters
- **AND** the frontend displays order id, currency, product id, protocol, term, APY, invested amounts, earnings data, purchase time, redemption time, realized earnings, and tag when available.

#### Scenario: Limit history page size
- **WHEN** the user requests historical orders
- **THEN** the backend enforces the OKX maximum page size of 100 records
- **AND** the response exposes whether more records can be requested through supported pagination fields.

#### Scenario: Completed history state
- **WHEN** a historical On-chain Earn order has state `3`
- **THEN** the UI displays the order as completed
- **AND** the raw state remains available in the normalized response.

### Requirement: ETH Staking Overview
The system SHALL provide a read-only ETH staking overview.

#### Scenario: Load ETH staking product info
- **WHEN** the user opens the ETH staking panel
- **THEN** the system displays BETH rate, redemption days, minimum amount, and fast redemption daily limit when available.

#### Scenario: Load BETH balance
- **WHEN** the user has configured OKX credentials
- **THEN** the system displays BETH amount, latest interest accrual, total interest accrual, and snapshot timestamp when available.

#### Scenario: Load ETH staking history
- **WHEN** the user opens ETH staking purchase and redemption history
- **THEN** the system displays request type, amount, redeeming amount, status, order id, request time, completed time, and estimated completed time when available.

### Requirement: SOL Staking Overview
The system SHALL provide a read-only SOL staking overview.

#### Scenario: Load SOL staking product info
- **WHEN** the user opens the SOL staking panel
- **THEN** the system displays OKSOL rate, redemption days, minimum amount, fast redemption daily limit, and currently available fast redemption amount when available.

#### Scenario: Load OKSOL balance
- **WHEN** the user has configured OKX credentials
- **THEN** the system displays OKSOL amount, latest interest accrual, and total interest accrual when available.

#### Scenario: Load SOL staking history
- **WHEN** the user opens SOL staking purchase and redemption history
- **THEN** the system displays request type, amount, redeeming amount, status, request time, completed time, and estimated completed time when available.

### Requirement: APY History
The system SHALL display ETH and SOL staking APY history from public OKX endpoints.

#### Scenario: Load ETH APY history
- **WHEN** the user views ETH staking APY history for a supported number of days
- **THEN** the system retrieves ETH staking APY points
- **AND** the UI displays APY values with their timestamps.

#### Scenario: Load SOL APY history
- **WHEN** the user views SOL staking APY history for a supported number of days
- **THEN** the system retrieves SOL staking APY points
- **AND** the UI displays APY values with their timestamps.

#### Scenario: Clamp APY history range
- **WHEN** the requested APY history day range is less than 1 or greater than 365
- **THEN** the backend rejects or normalizes the request to the supported range
- **AND** the UI does not imply that unsupported history was loaded.

### Requirement: Credential And Access States
The system SHALL handle missing credentials and OKX access errors without breaking the dashboard.

#### Scenario: Credentials not configured
- **WHEN** the user opens an authenticated Earn section without configured OKX credentials for the selected environment
- **THEN** the system displays an unconfigured state for that section
- **AND** public APY history sections remain available when possible.

#### Scenario: OKX financial product access unavailable
- **WHEN** OKX rejects an Earn request because the account, region, permission, or product access is unavailable
- **THEN** the system displays a non-blocking warning for the affected Earn section
- **AND** market, trading, automation, positions, and account pages remain usable.

### Requirement: Earn Cache And Partial Failures
The system SHALL isolate Earn refresh failures and stale cache behavior per Earn data source.

#### Scenario: Return stale Earn data
- **WHEN** a live Earn refresh fails and stale cached data exists for the same environment and query
- **THEN** the system returns the stale cached data with cache age and warning metadata
- **AND** the UI labels the affected section as stale or warning.

#### Scenario: Partial Earn source failure
- **WHEN** product offers load successfully but active orders, history, ETH staking, or SOL staking fail
- **THEN** the successful Earn sections remain visible
- **AND** each failed section displays its own unavailable or warning state.

#### Scenario: Earn failure does not affect account page
- **WHEN** an Earn API request fails
- **THEN** existing account balance, positions, market, trading, and automation endpoints continue to use their own cache and error handling.

### Requirement: Future Earn Action Safety
The system SHALL define a separate safety boundary for future On-chain Earn purchase, redeem, and cancel actions.

#### Scenario: Earn actions require separate enablement
- **WHEN** a future implementation adds Earn mutation endpoints
- **THEN** those endpoints MUST require a dedicated Earn action authorization separate from SWAP live trading enablement
- **AND** disabling SWAP live trading MUST NOT be the only protection for Earn actions.

#### Scenario: Earn actions require explicit confirmation
- **WHEN** a future Earn purchase, redeem, or cancel request is prepared
- **THEN** the system MUST require confirmation that names the environment, action, product or order id, asset, amount, and material timing or early-redemption option before submitting to OKX.

#### Scenario: Earn actions require audit records
- **WHEN** a future Earn mutation request is submitted to OKX
- **THEN** the system MUST persist a local audit record containing action type, environment, request summary, OKX response summary, timestamps, and raw metadata needed for review.
