## Context

The current Contract Radar implementation scans OKX SWAP instruments, filters by settlement and minimum 24h volume, keeps a bounded candidate pool, fetches recent candles, and ranks results by a deterministic opportunity score. The current score combines tradability and volatility, then subtracts risk penalties.

That approach is useful for surfacing active contracts, but it creates two UX problems:

- A lower-volume contract can appear near the top if its volatility is high enough.
- The displayed "24h volume" field can use different OKX ticker fields depending on availability, so the number may represent quote turnover, base currency volume, or contract volume without a clear label.

For contract selection, users need a simple answer first: "can this contract be played safely enough to inspect?" Ranking comes second.

## Goals / Non-Goals

**Goals:**

- Make liquidity and tradability a gate before opportunity ranking.
- Normalize radar volume/turnover output so users can understand what the displayed number means.
- Prevent low-liquidity contracts from ranking highly only because they are volatile.
- Explain ranking in the UI with concise labels and evidence metrics.
- Keep the existing radar endpoint and workflow handoff behavior stable.

**Non-Goals:**

- Do not place trades or create strategies automatically.
- Do not guarantee profitability or produce buy/sell instructions.
- Do not add a new exchange integration.
- Do not require private account or position data for radar ranking.

## Decisions

### Decision: Treat liquidity as a gate, not just a score component

The radar should calculate a tradability status before ranking. A contract must pass minimum liquidity, live state, and data completeness checks to be considered "playable". Contracts that fail the gate can still be returned when filters allow them, but they must be visibly labeled as "流动性不足" or "仅观察" and must not outrank playable contracts in the default opportunity ranking.

Rationale: users use the radar to choose contracts. A high-volatility but thin contract is a risk case, not the best default candidate.

Alternative considered: increase the liquidity score weight in the existing opportunity formula. This is simpler, but it still allows volatility to offset liquidity and does not explain the decision clearly.

### Decision: Use quote turnover as the preferred liquidity basis

The backend should expose both the raw OKX ticker volume source and a normalized display model. For USDT/USDC-settled swaps, quote turnover should be preferred when available because it is comparable across contracts. If quote turnover is unavailable but base volume and last price are available, the radar should derive an estimated quote turnover and label it as estimated. If no comparable turnover can be produced, the response should mark the unit/source explicitly instead of silently falling back.

Rationale: comparing base coin volume or contract count across different instruments is misleading. The UI needs to know whether it is showing quote turnover, base volume, or contract volume.

Alternative considered: continue using the first available ticker field. This keeps the payload small but makes rankings hard to trust.

### Decision: Sort by playable status before opportunity score

Default ranking should sort playable contracts first, then opportunity score, then liquidity, then volatility. Non-playable contracts should only appear after playable contracts or when users explicitly choose a low-liquidity/risk filter.

Rationale: this matches the product question: "which contract can I play and is active enough?" not "which candle moved the most?"

Alternative considered: add separate liquidity and volatility sorting controls without changing default order. This helps advanced users but leaves the default confusing.

### Decision: Keep numeric scoring deterministic and auditable

All numeric ranking must remain deterministic. LLM explanations may summarize reasons and warnings, but they must not change tradability status, normalized volume fields, scores, or ranking.

Rationale: users need to trust that ranking is reproducible and based on visible market data.

Alternative considered: let the LLM produce a final qualitative rank. This would be less auditable and harder to test.

### Decision: Make ranking semantics visible in the UI

The frontend should label the default rank as a combined contract-selection rank and show the key gates near the score: liquidity status, volume basis, risk level, and volatility level. "机会分" can remain, but it must not be the only visible explanation for rank.

Rationale: the ranking should be understandable without opening every detail panel.

Alternative considered: only improve backend scoring. That would reduce bad ranks but still leave users guessing why a result appears first.

## Risks / Trade-offs

- [Risk] Stricter liquidity gates may hide newly active contracts. -> Mitigation: keep filters for observing low-liquidity or high-volatility contracts, but label them clearly and keep them out of the default top rank.
- [Risk] Some OKX tickers may lack quote turnover. -> Mitigation: expose volume basis metadata and lower data quality or tradability confidence when comparable turnover is missing.
- [Risk] Changing score weights can surprise users comparing old and new results. -> Mitigation: update labels and tests so the new ranking is framed as contract suitability rather than raw opportunity.
- [Risk] Cached snapshots may contain old payload shapes. -> Mitigation: include a response version or tolerate missing new fields in the frontend.

## Migration Plan

1. Extend backend radar result shape with liquidity/tradability status and volume basis metadata.
2. Update scoring to apply tradability gates before default ranking.
3. Update frontend labels and table/detail fields to show why a contract is playable, watch-only, or low-liquidity.
4. Update tests for deterministic gate behavior, ranking order, and volume unit display.
5. Keep stale cache fallback tolerant of previous radar snapshots.

Rollback: restore the previous opportunity-only sort and keep the new UI fields optional so old radar payloads still render.

## Open Questions

- What default quote-turnover threshold should define "可玩" for USDT swaps: 10M, 50M, or user-configurable by risk profile?
- Should the radar expose explicit sort modes such as "综合", "流动性", and "波动" in this change or a later one?
- Should low-liquidity contracts be hidden by default or shown below playable contracts with a warning?
