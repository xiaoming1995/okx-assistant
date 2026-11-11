## Why

The market page currently derives the visible change percentage from the rolling 24-hour open price.  That baseline can disagree with the OKX app's \"今日涨跌\" percentage, making the same contract look as though it has moved in the opposite direction and reducing users' confidence in the data.

## What Changes

- Define the market-facing \"今日涨跌\" percentage from the ticker's UTC+8 day-open price (`sodUtc8`), so it aligns with the OKX app's China-market convention.
- Apply that calculation consistently to contract-list percentages, daily-change sorting, market summary cards, and contract-selection surfaces.
- Provide an ordered fallback for incomplete tickers while retaining a usable percentage.
- Preserve rolling-24-hour calculations based on `open24h` for Radar, AI evidence, and any surface explicitly labelled \"24h 涨跌\".
- Keep raw ticker APIs, K-line data, watchlist selection, and trading behavior unchanged.

## Capabilities

### New Capabilities

- `market-today-change-alignment`: Calculate and present market-facing daily price changes from the same daily baseline as the OKX app, without altering explicit 24-hour analytics.

### Modified Capabilities

<!-- None. No existing OpenSpec capability defines market percentage semantics. -->

## Impact

- Frontend market data utilities and the UI surfaces that show or sort a daily price change, primarily `frontend/src/main.tsx`.
- Frontend and focused backend regression tests that distinguish daily-display semantics from rolling-24-hour analytics.
- No new external API, no data migration, and no change to the backend ticker payload.
