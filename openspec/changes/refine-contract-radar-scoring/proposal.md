## Why

Contract Radar currently ranks contracts by a combined opportunity score, but the ranking can look confusing when a contract with lower visible volume appears near the top because volatility offsets liquidity. The volume field also falls back across multiple OKX ticker fields, so the UI may mix quote turnover, base volume, and contract volume without making the unit clear.

This change makes the radar feel more trustworthy for contract selection: first decide whether a contract is liquid enough to play, then rank suitable contracts by volatility and opportunity.

## What Changes

- Normalize the radar's 24h volume/turnover metrics so displayed values have a clear unit and scoring uses a consistent liquidity basis when possible.
- Split radar evaluation into two concepts:
  - tradability gate: whether a contract is liquid, live, and data-complete enough to consider.
  - opportunity ranking: among tradable contracts, which have useful volatility and activity.
- Prevent low-liquidity contracts from ranking highly only because short-term volatility is large.
- Add clearer result labels such as "可玩", "观察", or "流动性不足" so users can quickly understand why a contract is ranked.
- Add UI cues explaining whether the ranking is sorted by opportunity, liquidity, volatility, or a combined view.
- Preserve existing radar actions that open the selected contract in market, trade, or automation flows.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `contract-radar-agent`: refine liquidity normalization, tradability gating, ranking semantics, and radar UI explanation so contract selection is clearer and low-volume contracts cannot misleadingly rank first.

## Impact

- Backend radar scoring helpers and API response fields in `backend/app/main.py`.
- Radar unit tests covering liquidity gates, normalized volume fields, and ranking order.
- Frontend radar types and UI labels in `frontend/src/main.tsx`.
- Frontend smoke tests for radar ranking labels and volume display.
- No database migration is expected unless persisted radar snapshots require versioned response metadata.
