## 1. Report layout rhythm

- [x] 1.1 Define local AI outlook spacing tokens and refactor scenario, multi-timeframe, and detail containers to use non-stacking module gaps.
- [x] 1.2 Align the multi-timeframe card internal structure while preserving existing responsive behavior and report content.

## 2. Manual analysis feedback

- [x] 2.1 Derive first-analysis and refresh states from the existing request lifecycle and render concise accessible status feedback.
- [x] 2.2 Add a stable first-analysis skeleton and a non-blocking refresh indicator that preserves the previous report.
- [x] 2.3 Add motion-respectful spinner and skeleton styling, including reduced-motion behavior.

## 3. Verification

- [x] 3.1 Extend static front-end coverage for spacing and loading feedback contracts.
- [x] 3.2 Run the targeted static test and production front-end build.
- [x] 3.3 Rebuild the front-end service and manually verify first-analysis, refresh, and completed-report states in the browser.
