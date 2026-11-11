## 1. Evidence and deterministic price plan

- [x] 1.1 Add a bounded 15m completed-candle price context with prior 20-candle levels, quote and tick-size validation.
- [x] 1.2 Derive a single directional plan or numeric two-sided re-evaluation from 15m, 1H, 1D and trading-structure evidence.
- [x] 1.3 Calculate tick-aligned entry, stop and target prices, status, provenance and expiry; reject stale, missing or inconsistent inputs.
- [x] 1.4 Attach the plan to normal, fallback and cached AI outlook responses without allowing LLM text to replace computed prices.
- [x] 1.5 Freeze numeric direction, entry, stop, target and validity explanations with each new priced plan and prediction sample.

## 2. Report presentation

- [x] 2.1 Add a compact first-screen price-plan section with direction, three prices, condition, expiry and explicit reference-price wording.
- [x] 2.2 Present unavailable, expired, missed-price and old-cache states in Chinese while retaining the existing report during refresh.
- [x] 2.3 Follow the frontend design guide and verify desktop, narrow-screen and keyboard-focus rendering.
- [x] 2.4 Show the frozen calculation trail in the report and behind a keyboard-accessible disclosure in prediction records; identify older records with missing inputs.

## 3. Verification

- [x] 3.1 Add focused backend cases for prior-window breakout, open candle, opposite direction, missing data, tick precision, expiry and cache identity.
- [x] 3.2 Add focused frontend coverage for plan and fallback states, run relevant tests and production build.
- [x] 3.3 Replay available historical candles for plan trigger and validity sanity, run strict OpenSpec validation, and report limitations.
