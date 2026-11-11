## Why

当前 AI 看行情的首屏只突出一个所选周期的方向，15 分钟、1 小时和日线的关系藏在长段说明或旧报告卡片中。用户难以快速判断短线波动是否与更大周期一致，也不知道哪些结论来自真实行情数据。

## What Changes

- 在手动生成的 AI 行情报告中提供 15 分钟、1 小时和日线三个独立的趋势读取结果。
- 每个周期只展示趋势状态、最多两项行情依据和一个可验证的确认/失效条件，数据不足时明确标注该周期不可判定。
- 在首屏方向结论下增加紧凑的多周期趋势条，说明周期是否同向或存在分歧；详细证据继续留在可展开区域。
- 保持现有报告为公开市场快照阅读，不增加下单、仓位、杠杆或个性化投资建议。

## Capabilities

### New Capabilities

- `multi-timeframe-market-trend-reading`: 基于各自周期的行情快照生成并清晰展示 15 分钟、1 小时和日线趋势读取及确认条件。

### Modified Capabilities

- None.

## Impact

- `backend/app/main.py`：补充多周期 K 线获取、趋势归纳及 API 响应字段。
- `frontend/src/main.tsx`、`frontend/src/styles.css`：增加方向优先、低噪音的多周期趋势区。
- `tests/test_market_ai_outlook.py`、`frontend/src/marketAiOutlook.static.test.mjs`：覆盖周期数据、缺失降级与阅读边界。
