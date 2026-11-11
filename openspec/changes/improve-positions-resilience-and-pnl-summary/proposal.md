## Why

The positions view exposes an upstream OKX transport exception directly to users when an account refresh is interrupted, even though a complete in-memory or saved snapshot may still be available. Its floating P&L values are also hard to scan: the intended positive/negative colours are overridden by table styles, and the existing aggregate is an unexplained compact chip.

## What Changes

- Make account and position snapshot refreshes resilient to interrupted upstream responses: retain a complete snapshot, retry refreshes in the background with bounded backoff, and return only display-safe Chinese freshness state to the client.
- Add an explicit floating P&L summary for currently open positions, including total unrealized P&L, profitable/loss/breakeven position counts, margin, notional value, snapshot time, and source state.
- Render row and aggregate floating P&L consistently as profit, loss, or neutral values, including a signed numeric presentation.

## Capabilities

### New Capabilities

- `resilient-position-snapshots`: Safe account/position snapshot fallback, retry metadata, and user-readable degradation states.
- `position-pnl-summary`: Explainable open-position floating P&L aggregation and positive/negative/neutral visual treatment.

### Modified Capabilities

- None.

## Impact

- `backend/app/main.py` account cache and `GET /api/account` response contract.
- `frontend/src/main.tsx` positions page and `frontend/src/styles.css` P&L visual styles.
- Focused backend and frontend regression tests, plus Docker runtime verification of the account endpoint and positions page.
