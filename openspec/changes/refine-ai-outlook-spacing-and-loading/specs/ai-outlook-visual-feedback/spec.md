## ADDED Requirements

### Requirement: AI report uses a consistent visual rhythm
The AI outlook report SHALL use one consistent hierarchy for labels, compact content, card content, and independent modules. Sibling report modules MUST be separated by their container rather than by stacked external margins, and the multi-timeframe cards MUST retain aligned internal sections at supported desktop widths.

#### Scenario: Viewing a completed AI report
- **WHEN** a user opens a generated AI outlook report
- **THEN** the direction, multi-timeframe, and optional detail sections have uniform module separation and the three timeframe cards have aligned content structure

#### Scenario: Viewing the report on a narrow viewport
- **WHEN** the report layout changes to its single-column responsive form
- **THEN** the same content hierarchy and non-overlapping spacing remain available without horizontal overflow

### Requirement: First manual analysis has clear loading feedback
When a user starts AI analysis and no previous report exists, the interface SHALL display a stable structural loading state that represents the direction and multi-timeframe report areas. The primary action MUST communicate that analysis is in progress and prevent a duplicate request.

#### Scenario: Starting the first analysis
- **WHEN** a user activates the manual AI analysis action without an existing report
- **THEN** the report area displays a labelled in-progress state and a non-content skeleton instead of an empty result area

#### Scenario: Completing the first analysis
- **WHEN** the AI analysis request succeeds
- **THEN** the loading state is replaced by the generated report without leaving a stale in-progress indicator

### Requirement: Refresh preserves the readable report and explains freshness
When a user refreshes an existing AI outlook report, the interface SHALL keep the previous report visible and SHALL show a concise updating status that explains it is displaying the previous snapshot while the new one is requested. The refresh action MUST be disabled until the request completes.

#### Scenario: Refreshing a generated report
- **WHEN** a user refreshes while a report is already displayed
- **THEN** the previous report remains readable, the action shows a busy state, and an updating message is visible

#### Scenario: Refresh request fails
- **WHEN** a refresh request fails after a report has been displayed
- **THEN** the previous report remains visible, the updating state is removed, and the existing error feedback describes the failure

### Requirement: Loading feedback is accessible and motion-respectful
AI outlook loading feedback SHALL expose a polite status message to assistive technology. Its visual motion MUST be disabled when the user requests reduced motion, and it MUST NOT claim a fabricated percentage or analysis phase.

#### Scenario: Reading loading feedback with assistive technology
- **WHEN** analysis enters either initial or refresh loading state
- **THEN** assistive technology receives one concise polite status message describing the current request

#### Scenario: User prefers reduced motion
- **WHEN** the operating system requests reduced motion
- **THEN** the loading spinner and skeleton animation are not animated while the status remains readable
