## ADDED Requirements

### Requirement: Short Desktop Height Keeps Market Metrics Reachable
The market chart page SHALL keep the lower market metrics row reachable when the desktop viewport height is too small to fit the full chart workspace.

#### Scenario: Desktop viewport height is short
- **WHEN** the market chart page is rendered at desktop width with a short viewport height
- **THEN** the right market content area MUST allow vertical scrolling instead of clipping the lower metrics row

#### Scenario: Chart content competes with lower metrics
- **WHEN** the chart panel and upper summaries consume more height than the viewport can display
- **THEN** the chart panel MUST shrink within a bounded short-height layout and the lower metrics row MUST remain reachable

#### Scenario: Normal desktop height remains workbench-like
- **WHEN** the market chart page is rendered at a normal desktop viewport height
- **THEN** the page MUST preserve the existing two-column market layout without forcing whole-page scrolling
