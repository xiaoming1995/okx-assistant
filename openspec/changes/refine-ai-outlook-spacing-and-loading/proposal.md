## Why

AI 看行情已能给出方向与多周期阅读，但报告模块同时使用 `gap`、`margin-top` 和 `margin-bottom`，造成模块间的距离缺乏一致节奏。手动分析期间也只改变按钮文字，用户无法判断请求是否正在处理、旧报告是否仍然有效。

## What Changes

- 为 AI 看行情报告定义一致的模块、卡片和文字层级间距，减少嵌套卡片造成的视觉噪音。
- 将方向结果、多周期趋势与可展开详情的分隔统一为稳定的垂直节奏，并保持三周期卡片的等高和对齐。
- 增加明确、无布局跳动的加载反馈：首次分析显示与最终结构一致的骨架状态；刷新时保留上一份报告并说明正在更新。
- 为加载与刷新状态提供可访问的状态文本和禁用重复触发的按钮反馈。
- 保持 AI 行情为只读市场快照，不改变方向判断、K 线数据、交易结构或交易执行逻辑。

## Capabilities

### New Capabilities

- `ai-outlook-visual-feedback`: AI 看行情报告的统一布局节奏，以及首次分析和刷新期间的可理解状态反馈。

### Modified Capabilities

- None.

## Impact

- `frontend/src/main.tsx`：补充 AI 行情首次分析、刷新中与失败后的展示状态。
- `frontend/src/styles.css`：增加局部间距令牌、对齐规则、骨架与轻量加载动画。
- `frontend/src/marketAiOutlook.static.test.mjs`：覆盖加载反馈、阅读边界与紧凑布局合同。
- 不修改后端 API、行情计算、AI 提示词、交易数据或自动交易功能。
