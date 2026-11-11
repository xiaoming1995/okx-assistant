## Why

Users currently have to choose automation contracts manually from raw market rows, volume sorting, and single-contract charts. This makes it hard to quickly identify which perpetual swap contracts are liquid enough, volatile enough, and worth further review before configuring a strategy.

This change adds a contract radar agent that scans OKX SWAP contracts, scores tradability and volatility, and explains why selected contracts are suitable to watch or risky to avoid.

## What Changes

- Add a contract radar capability that ranks perpetual swap contracts by tradability, volatility, and combined opportunity score.
- Combine instrument metadata, 24h ticker data, and recent candle-derived statistics into a structured radar result.
- Apply deterministic scoring and risk filters before any LLM explanation is generated.
- Use LLM output only for concise human-readable explanations for top candidates, not as the source of numeric ranking.
- Add a simple radar UI that presents top contracts, scores, key metrics, tags, reasons, and warnings.
- Allow users to filter radar results by settlement currency, minimum volume, volatility level, and risk status.
- Support opening a selected radar result in existing market, trade, or automation flows.
- Persist or cache radar scan results so repeated UI refreshes do not repeatedly fetch all market data or call the LLM.

## Capabilities

### New Capabilities

- `contract-radar-agent`: Scans OKX SWAP contracts, calculates market suitability scores, and presents ranked contract candidates with reasons and risk warnings.

### Modified Capabilities

- None.

## Impact

- Backend OKX client may need additional market endpoints beyond existing instruments, tickers, and candles if order book, open interest, or funding metrics are included.
- Backend API will need a radar scan endpoint and result normalization layer.
- Database or app settings storage may need radar snapshot persistence for scan history and cache reuse.
- Frontend navigation will need a new contract radar page or market-page mode.
- Existing market, trade, and automation pages should receive links or actions from radar results without changing their core behavior.
- Tests should cover scoring, filters, API payload shape, cache behavior, and frontend rendering states.
