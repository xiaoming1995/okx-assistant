## 1. Forecast Layout Structure

- [x] 1.1 Add a bounded forecast-count layout marker and compact timeframe-plus-confidence header without changing forecast data mapping or manual behavior.
- [x] 1.2 Keep directional observation, complete chart-grounded summary, and one concise re-read footer in every rendered forecast card.

## 2. Responsive Visual Refinement

- [x] 2.1 Replace the fixed three-column forecast grid with one-, two-, or three-card equal-width layouts that do not leave an empty track.
- [x] 2.2 Keep one and two forecast cards readable at desktop and laptop widths, then stack cards only at the narrow-display breakpoint.
- [x] 2.3 Align forecast-card spacing, metadata badges, borders, and footer emphasis with the existing report-reading system.

## 3. Verification

- [x] 3.1 Update frontend regression tests for count-aware layout, compact hierarchy, responsive stacking, and retained read-only messaging.
- [x] 3.2 Run frontend tests, production build, strict OpenSpec validation, rebuild the local frontend service, and verify a generated two-card report in the browser.
