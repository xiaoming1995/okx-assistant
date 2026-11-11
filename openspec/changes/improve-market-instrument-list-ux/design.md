## Context

The market page currently loads instruments through `/api/instruments?query=...&limit=200`, keeps a separate ticker map for prices, and renders a compact left rail list. The list supports filters, sort modes, watch toggles, and chart selection, but it displays settlement differences as short currency labels such as `USDT` or `BTC`.

That compact display is ambiguous for searches like `BTC`, where OKX legitimately returns both a USDT-settled swap and a coin-settled swap. Trade and automation pickers already expose more metadata than the market rail, so the first browsing experience is less explanatory than later contract-picking experiences.

## Goals / Non-Goals

**Goals:**

- Make similar symbol results visually understandable without hiding valid OKX contracts.
- Prefer USDT-settled, live contracts in the default market browsing path.
- Keep searching responsive and predictable while ticker data refreshes.
- Reuse shared instrument helper semantics where practical so market, trade, and automation entry points describe contracts consistently.

**Non-Goals:**

- Do not remove coin-settled instruments.
- Do not change the `/api/instruments` response shape.
- Do not change chart WebSocket behavior, ticker polling cadence, radar ranking, automation signals, or order submission rules.
- Do not add trading advice or buy/sell recommendations to the market list.

## Decisions

1. Load the full bounded instrument set once and filter in the frontend for the market list.

   Rationale: The local instrument universe is small enough for client filtering, and this avoids a visible reload on every search keystroke. Manual refresh still calls `/api/instruments/refresh` and then reloads the list.

   Alternative considered: Keep server-side query on every keystroke. This preserves smaller payloads but causes avoidable jitter and makes search feel coupled to network latency.

2. Default the market rail filter to USDT-settled contracts.

   Rationale: USDT-settled swaps are the common default path for this app's manual trading and automation workflows. Users can still switch to all contracts or coin-settled contracts when they need those markets.

   Alternative considered: Keep `全部` as default. This keeps maximum visibility but makes common symbols look duplicated before the user understands settlement differences.

3. Add human-readable instrument subtype labels and metadata in list rows.

   Rationale: `USDT本位`, `币本位 BTC结算`, and contract-value labels explain why `BTC-USDT-SWAP` and `BTC-USD-SWAP` are different. This is clearer than displaying only `USDT` or `BTC`.

   Alternative considered: Deduplicate search results by base symbol. This would hide valid instruments and could prevent users from opening the coin-settled market intentionally.

4. Sort market results by user intent before lexical order.

   Rationale: The selected contract, watched contracts, USDT-settled contracts, live contracts, and high-volume markets better match how users choose an instrument than alphabetical order alone.

   Alternative considered: Preserve the current lexical default. It is predictable for developers, but not very helpful for ordinary browsing.

## Risks / Trade-offs

- [Risk] Defaulting to USDT-settled contracts could make coin-settled markets less discoverable. -> Mitigation: keep visible `全部` and `币本位` filters and show accurate result counts.
- [Risk] Showing more metadata could make the left rail dense on smaller screens. -> Mitigation: use compact badges and allow secondary metadata to truncate instead of expanding row height unpredictably.
- [Risk] Different pickers could drift again if helpers stay ad hoc. -> Mitigation: centralize settlement labeling and default instrument sort helpers in shared frontend functions.
