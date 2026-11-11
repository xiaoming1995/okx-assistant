## 1. Scenario decision contract

- [x] 1.1 Add a deterministic scenario-board payload with one primary evidence score, current price position, data limitations, and two conditional scenarios.
- [x] 1.2 Derive scenario conditions and limitations from the existing chart snapshot, evidence gaps, and confirmation levels without weakening confirmed-direction rules.
- [x] 1.3 Keep LLM narrative confidence separate from the rule-based scenario evidence score in fresh and fallback reports.

## 2. Scenario-board reading experience

- [x] 2.1 Render a compact current-state and bullish/bearish scenario board before detailed evidence, with safe compatibility for older cached reports.
- [x] 2.2 Make unavailable trading data visually explain its confirmation impact, and move detailed evidence, narrative metadata, and sources to secondary disclosure.
- [x] 2.3 Remove conflicting primary confidence labels and refine responsive, accessible scenario-board layout.

## 3. Verification

- [x] 3.1 Add backend coverage for score consistency, range scenarios, directional clues, and data-limited candidates.
- [x] 3.2 Update frontend coverage for the scenario board, score label, unavailable-data limitation, and cached-report fallback.
- [x] 3.3 Run focused tests, build, OpenSpec validation, container/API checks, and visual page verification.
