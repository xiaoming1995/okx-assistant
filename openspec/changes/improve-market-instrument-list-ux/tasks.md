## 1. Instrument Semantics

- [x] 1.1 Add shared frontend helpers for settlement labels, settlement priority, and instrument relevance sorting.
- [x] 1.2 Use the shared helpers in market, trade, and automation contract selection paths where they describe the same instrument metadata.

## 2. Market List Experience

- [x] 2.1 Default the market page instrument filter to USDT-settled contracts.
- [x] 2.2 Change market search to filter the loaded instrument list locally while keeping manual refresh behavior.
- [x] 2.3 Update market list rows to show human-readable settlement type and contract-value context.
- [x] 2.4 Adjust default sorting so selected, watched, USDT-settled, live, and higher-volume contracts appear before lexical fallback.

## 3. Validation

- [x] 3.1 Add or update focused frontend static tests for default filter, local search, settlement labels, and default sort behavior.
- [x] 3.2 Run focused frontend tests and production build.
- [x] 3.3 Run OpenSpec validation for the change.
