## ADDED Requirements

### Requirement: Forecast cards keep a stable internal reading rhythm
The manual AI outlook SHALL present the metadata, directional observation, chart-grounded summary, and re-read condition in consistent internal tracks for all cards within the same forecast row. The implementation MUST preserve complete generated content without fixed card heights or line clamping.

#### Scenario: Forecast cards contain different direction lengths
- **WHEN** two forecast directions require different numbers of lines at a desktop width
- **THEN** each card preserves its full direction and the summaries start after the shared direction track without clipping content

#### Scenario: Forecast cards contain different summary lengths
- **WHEN** two forecast summaries have different lengths in the same forecast row
- **THEN** both cards retain equal outer-row height and their re-read conditions share a bottom baseline

### Requirement: Forecast content alignment preserves responsive and read-only behavior
The content-alignment layout SHALL retain the existing count-aware forecast columns on readable desktop widths and SHALL stack cards only at the established narrow-display breakpoint. It MUST NOT change manual generation, chart-snapshot inputs, or the no-trading safety messaging.

#### Scenario: User views a narrow display
- **WHEN** the forecast grid reaches the narrow-display breakpoint
- **THEN** cards stack in one column while every direction, summary, and re-read condition remains fully readable

#### Scenario: User views a generated manual report
- **WHEN** the content-alignment layout is rendered for a generated report
- **THEN** the report remains conditional, chart-grounded, manually requested, and explicitly read-only
