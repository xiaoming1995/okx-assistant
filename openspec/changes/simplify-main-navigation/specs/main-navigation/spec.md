## ADDED Requirements

### Requirement: Top navigation is simplified to five primary sections

The frontend SHALL render exactly five primary top-level navigation entries: Market, Trade, Automation, Account, and Settings.

#### Scenario: User views primary navigation
- **WHEN** the application header is displayed
- **THEN** the top-level navigation shows Market, Trade, Automation, Account, and Settings as the primary entries
- **AND** Strategy Management, Signal Logs, Positions, AI Config, AI Usage, Account Management, Contract Radar, and Market Chart are not shown as separate top-level entries

### Requirement: Market section groups discovery and charting

The Market section SHALL provide secondary access to Contract Radar and Market Chart, with Contract Radar as the default Market view.

#### Scenario: User opens Market
- **WHEN** the user selects the Market primary navigation entry
- **THEN** the Contract Radar view is displayed by default
- **AND** the Market section shows secondary controls for Contract Radar and Market Chart

#### Scenario: User opens Market Chart
- **WHEN** the user selects Market Chart from the Market section secondary controls
- **THEN** the existing market chart view is displayed

### Requirement: Trade remains a dedicated primary section

The Trade section SHALL continue to open the existing manual trading view as a dedicated high-risk operation surface.

#### Scenario: User opens Trade
- **WHEN** the user selects the Trade primary navigation entry
- **THEN** the manual trading view is displayed

### Requirement: Automation section groups automation pages

The Automation section SHALL provide secondary access to Automation Overview, Strategy Management, and Signal Logs.

#### Scenario: User opens Automation
- **WHEN** the user selects the Automation primary navigation entry
- **THEN** the automation overview is displayed by default
- **AND** the Automation section shows secondary controls for Overview, Strategies, and Signals

#### Scenario: User opens Signal Detail
- **WHEN** the user opens a signal detail from Signal Logs
- **THEN** the detail view remains within the Automation section
- **AND** back navigation returns to Signal Logs

### Requirement: Account section groups account pages

The Account section SHALL provide secondary access to Positions and Account Management.

#### Scenario: User opens Account
- **WHEN** the user selects the Account primary navigation entry
- **THEN** the Positions view is displayed by default
- **AND** the Account section shows secondary controls for Positions and Account Management

### Requirement: Settings section groups AI operations

The Settings section SHALL provide secondary access to AI Configuration and AI Usage.

#### Scenario: User opens Settings
- **WHEN** the user selects the Settings primary navigation entry
- **THEN** the AI Configuration view is displayed by default
- **AND** the Settings section shows secondary controls for AI Configuration and AI Usage

### Requirement: Contract handoff remains intact

The navigation changes MUST preserve selected-contract handoff from Contract Radar into Market Chart, Trade, and Automation.

#### Scenario: User opens a radar contract in another workflow
- **WHEN** the user chooses to open a Contract Radar result in Market Chart, Trade, or Automation
- **THEN** the target view opens with that contract selected
- **AND** the corresponding primary section is active
