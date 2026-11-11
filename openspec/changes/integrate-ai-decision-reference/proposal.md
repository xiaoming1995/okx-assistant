## Why

AI 看行情已能解释图表状态和给出条件推演，但没有把已有的行动参考字段和合约交易结构转化为用户可阅读的决策信息；多空人数、主动买卖和持仓变化仍分散在“交易数据”页面。用户无法快速判断当前更适合偏多观察、偏空观察、等待确认或降低关注，也看不到该判断是否得到资金与参与结构的支持。

## What Changes

- 在手动生成的 AI 报告中增加“决策参考”模块，清楚呈现当前行动倾向、触发条件、失效/重评条件、置信度和数据完整性。
- 将已接入的合约交易统计（多空人数比、主动买卖占比、持仓量及其变化）复用到 AI 报告，形成可核对的交易结构依据。
- 用一致的冲突和降级规则解释图表与交易结构是否一致；数据缺失、统计滞后或信号冲突时明确引导为等待确认，而非制造方向结论。
- 将“等待确认”和持仓变化缺失状态改写为可理解的市场阅读说明，明确它们不等于等待时长、个人持仓或数值为零。
- 保持手动生成、公开行情数据、只读和不影响订单/自动化的边界；不提供个性化仓位、杠杆、保证收益或自动执行。

## Capabilities

### New Capabilities

- `ai-market-decision-reference`: 基于图表快照和已接入合约交易统计，提供可解释、条件化且只读的 AI 决策参考。

### Modified Capabilities

<!-- None. Existing archived change specifications do not define a base spec for this new combined decision surface. -->

## Impact

- `backend/app/main.py`：将现有市场统计以与图表快照一致的方式提供给 AI 报告，并保留来源、时间和部分失败状态。
- `frontend/src/main.tsx` 与 `frontend/src/styles.css`：渲染决策参考与紧凑交易结构证据，不新增交易控制。
- `tests/test_market_ai_outlook.py`、`tests/test_market_stats.py` 和 `frontend/src/marketAiOutlook.static.test.mjs`：覆盖数据映射、冲突/降级、只读边界与展示行为。
- 外部依赖不变：继续使用已接入的 OKX 公共 K 线、Ticker 和 Trading Statistics 数据。
