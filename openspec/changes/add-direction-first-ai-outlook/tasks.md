## 1. Direction-first decision contract

- [x] 1.1 Add a deterministic direction summary derived from the existing decision, scenario levels, strongest evidence, and data limitations.
- [x] 1.2 Classify complete evidence as confirmed `偏多观察` or `偏空观察`; classify all incomplete, split, and data-limited states as `暂不追向`.
- [x] 1.3 Provide one readable reason and one next complete-candle or data-restoration condition without adding execution advice.

## 2. Compact result experience

- [x] 2.1 Replace the first-screen scenario-card grid with a direction-first summary card and move bilateral scenario cards to secondary disclosure.
- [x] 2.2 Render current price, relevant confirmation price, reason, next condition, snapshot period, and non-execution boundary in a compact responsive layout.
- [x] 2.3 Derive a safe direction-first fallback for cached reports that lack the new payload.

## 3. Verification

- [x] 3.1 Add backend coverage for confirmed upward/downward, unconfirmed range, and data-limited summaries.
- [x] 3.2 Update frontend coverage for concise direction wording, fallback, disclosure, and read-only boundary.
- [x] 3.3 Run focused tests, production build, OpenSpec strict validation, container/API checks, and visual page verification.
