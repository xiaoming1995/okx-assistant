## ADDED Requirements

### Requirement: Primary reading modules share a desktop alignment boundary
The AI outlook page SHALL render the current conclusion and chart-evidence modules with a shared top edge and matched outer height whenever the reading area uses its desktop multi-column layout.

#### Scenario: Uneven module content on desktop
- **WHEN** current conclusion and chart evidence contain different amounts of text or badges in a desktop multi-column reading area
- **THEN** both module outer cards begin on the same vertical coordinate and end on the same vertical coordinate without hiding content

### Requirement: Reading-module content remains structured and responsive
The AI outlook page SHALL retain visible module headers, evidence facts, badges, and conclusion text while preserving its narrow-screen single-column reading layout.

#### Scenario: Narrow reading area
- **WHEN** the viewport reaches the existing narrow-screen breakpoint
- **THEN** the modules stack in one column with their content readable and without horizontal overflow

#### Scenario: Long live analysis text
- **WHEN** a module body contains more text than its counterpart
- **THEN** the reading row grows to fit the text and no module text is clipped or replaced
