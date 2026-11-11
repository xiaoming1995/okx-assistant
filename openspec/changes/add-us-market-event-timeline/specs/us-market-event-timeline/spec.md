## ADDED Requirements

### Requirement: U.S. Market Event Timeline Route
The system SHALL provide a read-only `美国事件` page in the market section at `#/market/us-timeline`, with an optional `date` query parameter in `YYYY-MM-DD` form.

#### Scenario: User opens the default timeline route
- **WHEN** the user opens `#/market/us-timeline` without a valid date
- **THEN** the market navigation SHALL identify `美国事件` as the active page
- **AND** the page SHALL select the current calendar date in `Asia/Shanghai`
- **AND** the page SHALL not create an order, strategy, alert, or AI analysis request

#### Scenario: User opens a dated timeline link
- **WHEN** the user opens `#/market/us-timeline?date=2026-09-17`
- **THEN** the page SHALL select September 17, 2026 in the timeline
- **AND** the selected date SHALL be reflected in the route when the user changes it

### Requirement: Date-Oriented Event Browsing
The timeline SHALL expose a selected date and adjacent dates, group events by their displayed calendar date, and support category and lifecycle-state filtering.

#### Scenario: User selects an adjacent date
- **WHEN** the user selects an adjacent date from the date rail
- **THEN** the page SHALL load events for that date window
- **AND** it SHALL show an explicit empty state when no matching events exist

#### Scenario: User filters event categories or states
- **WHEN** the user filters by one or more supported categories or states
- **THEN** the page SHALL show only events that satisfy every selected filter
- **AND** it SHALL preserve the selected date

### Requirement: Direct Month and Date Navigation
The timeline SHALL let users move to the previous or next month and select an explicit calendar date while keeping the route-synchronized selected date.

#### Scenario: User browses a future month
- **WHEN** the user selects the next-month control or chooses a future date from the calendar picker
- **THEN** the timeline SHALL request the bounded window around that selected date
- **AND** it SHALL distinguish an empty persisted window from a window still being refreshed in the background

### Requirement: Time Zone Transparency
The timeline SHALL use `Asia/Shanghai` as its default display zone while retaining each event's original official time context.

#### Scenario: Event has an official U.S. release time
- **WHEN** an event has a scheduled time sourced in `America/New_York`
- **THEN** the card SHALL display the converted Shanghai time
- **AND** it SHALL expose the original U.S. Eastern time and source timezone

#### Scenario: Event source has no exact release time
- **WHEN** an official source only identifies an event date and does not provide a stable exact time
- **THEN** the card SHALL display the date-only/unknown-time state
- **AND** it SHALL not invent a release time

### Requirement: Structured Event Cards
The timeline SHALL render scheduled, released, revised, and cancelled events as clearly distinguished, source-attributed cards.

#### Scenario: Scheduled event is displayed
- **WHEN** an event is scheduled but has not been released
- **THEN** its card SHALL show its title, category, importance, scheduled time, state, source link, and available previous or forecast fields
- **AND** unavailable fields SHALL be shown as unavailable rather than generated values

#### Scenario: Released or revised event is displayed
- **WHEN** an event has an official actual value or a published revision
- **THEN** its card SHALL show the available actual, previous, forecast, revision, unit, and period-label context
- **AND** it SHALL identify whether the record is released or revised

#### Scenario: Historic official values are not yet verifiable
- **WHEN** a past dated calendar event has no sourced actual or previous value
- **THEN** the card SHALL identify it as awaiting historical-value verification
- **AND** it SHALL retain the official schedule/source link without presenting an empty value block or fabricated figure

### Requirement: Focused Compact Timeline Presentation
The timeline SHALL use the selected date as the center of a bounded nearby-date browse window and present events in a compact, date-grouped hierarchy suitable for scanning a scheduled policy-event bundle. On a desktop viewport, the timeline canvas SHALL remain a centered, bounded reading column instead of stretching event rows across the workbench.

#### Scenario: User views a scheduled monetary-policy decision
- **WHEN** a scheduled Federal Reserve monetary-policy decision is present in the selected browse window
- **THEN** the primary decision card SHALL retain visible `公布`, `前值`, and `预期` slots
- **AND** every unavailable source value SHALL use an explicit unavailable label rather than a fabricated value

#### Scenario: A related FOMC calendar item is present
- **WHEN** the official calendar identifies a related projection or press-conference item on the same date
- **THEN** the timeline SHALL render it as a compact related event row
- **AND** it SHALL retain its official source link and exact-time availability state

#### Scenario: User opens the timeline on a wide desktop viewport
- **WHEN** the market workbench is wider than the reference reading column
- **THEN** the date rail and event rows SHALL retain the same bounded column width and card hierarchy
- **AND** scheduled related events SHALL remain visibly card-shaped rather than becoming unbounded text rows

### Requirement: Source and Freshness Context
The timeline SHALL make provider/source status visible without hiding usable persisted events.

#### Scenario: A provider refresh uses retained data
- **WHEN** a provider refresh fails and previously persisted events are returned
- **THEN** the page SHALL continue to show those events
- **AND** it SHALL display a source/freshness warning with the retained-data context

#### Scenario: Timeline has partial provider availability
- **WHEN** one official provider is unavailable while another provider returns events
- **THEN** the page SHALL show the available events
- **AND** it SHALL identify the unavailable provider without presenting its missing data as complete

#### Scenario: All displayed providers are healthy
- **WHEN** each provider that contributes to the current window is fresh
- **THEN** the default timeline view SHALL prioritize the event list over provider-status detail
- **AND** a degraded provider SHALL remain visible through a compact warning without obscuring usable events

### Requirement: Observational Safety Boundary
The timeline SHALL remain an informational context surface and SHALL not present event data as a trade execution instruction or verified causal price explanation.

#### Scenario: User views event details
- **WHEN** the user views an event card or its source details
- **THEN** the UI SHALL not expose order, leverage, automation, or signal-creation controls
- **AND** it SHALL not label a price change as caused by the event without separately verifiable evidence
