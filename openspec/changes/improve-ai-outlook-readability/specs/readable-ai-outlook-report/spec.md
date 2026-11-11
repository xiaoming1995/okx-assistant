## ADDED Requirements

### Requirement: AI report uses a readable current-chart hierarchy
The AI outlook page SHALL present a current-chart conclusion, snapshot data status, no more than three traceable chart-evidence items, and observation/reassessment conditions before supplementary material. The primary report SHALL NOT render future-price prediction cards as its main hierarchy.

#### Scenario: Generated report is shown
- **WHEN** a user opens a generated AI report
- **THEN** the first report area shows the current-chart conclusion, data status, up to three evidence items, and observation conditions in Chinese

#### Scenario: Report has no analysis yet
- **WHEN** the current chart snapshot has not been analyzed
- **THEN** the page explains the manual analysis boundary and shows readable pending states without fabricating a conclusion

### Requirement: Technical evidence is translated for user reading
The page SHALL translate recognized technical evidence into Chinese labels and formatted values. It MUST NOT expose implementation field names or raw English status tokens as primary report copy.

#### Scenario: Report includes moving-average and volume evidence
- **WHEN** the report contains technical evidence for moving averages, range, or volume
- **THEN** the page renders the evidence as Chinese facts with formatted prices, percentages, or counts rather than raw property names

### Requirement: Data degradation is visible without overwhelming the report
The page SHALL distinguish chart-snapshot completeness from supplementary external-source degradation. External-source failure details MUST be visually secondary while snapshot incompleteness, staleness, or cache state remains visible beside the report conclusion.

#### Scenario: Supplementary macro data fails
- **WHEN** a report includes unavailable macro or source details while its chart snapshot is usable
- **THEN** the page shows a concise secondary warning and allows the user to inspect detail without replacing the chart conclusion

#### Scenario: Chart snapshot is incomplete
- **WHEN** the active report snapshot is incomplete, stale, or degraded
- **THEN** the page prominently identifies that state before its evidence and observation conditions

### Requirement: Report remains accessible across layouts
The report SHALL use content-sized cards and a responsive layout that avoids horizontal clipping or large unused card areas at desktop and narrow widths.

#### Scenario: Desktop report is rendered
- **WHEN** a generated report is displayed in a desktop market workbench
- **THEN** conclusion and evidence blocks use their content height and supplementary content does not create large empty primary cards

#### Scenario: Narrow report is rendered
- **WHEN** the viewport is narrow
- **THEN** report blocks flow in a single readable column with wrapping text and accessible source details
