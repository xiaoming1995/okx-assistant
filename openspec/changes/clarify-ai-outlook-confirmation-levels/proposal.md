## Why

当 AI 看行情给出“观望”时，现有“条件水位”虽然展示区间上下沿，却将价格、确认要求与失效情形混在解释文字中。读者无法快速判断下一步该观察哪一个价格、到价后还缺少什么证据、或何时应放弃该方向。

## What Changes

- 将观望状态下的条件水位重新组织为“条件确认价”：当前观望状态、偏多候选、偏空候选，以及各自的确认与失效条件。
- 明确每个候选方向的图表确认价、所需的已收盘 K 线、量能与可用交易结构要求；条件未共同满足时继续观望。
- 将突破后回到原区间定义为候选方向失效，并绑定报告快照与手动刷新状态。
- 保持只读、公共行情解读属性；不增加下单、仓位、杠杆、止盈止损或承诺性收益内容。

## Capabilities

### New Capabilities

- `ai-outlook-confirmation-levels`: 在 AI 行情报告观望时，提供可核对的偏多、偏空条件确认价与失效规则。

### Modified Capabilities

<!-- None. Existing specifications do not define this confirmation-level capability. -->

## Impact

- `backend/app/main.py`：扩展报告快照派生的条件水位响应，提供候选方向、确认要求与失效状态。
- `frontend/src/main.tsx`、`frontend/src/styles.css`：以“下一步观察”方式呈现确认价，取代难以快速判断的四项散列说明。
- `tests/test_market_ai_outlook.py`、`frontend/src/marketAiOutlook.static.test.mjs`：覆盖价格来源、确认/失效规则、部分数据与只读边界。
- 不引入外部数据源、订单接口、账户数据或自动刷新分析。
