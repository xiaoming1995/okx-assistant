## Why

左侧合约栏在用户看到可选合约前，同时展示搜索、五项筛选、三项排序和列表表头；高频选择路径被低频配置挤占，导致首屏层级过多且“2/2”这类计数不易理解。需要将它收敛为以快速找到、切换和关注合约为中心的选择器，同时保留高级筛选能力。

## What Changes

- 将共享左侧合约栏重组为“搜索 + 常用范围 + 高级条件”的渐进式选择体验。
- 将首屏范围收敛为本地已关注和全部合约，并以易懂的计数表达当前范围与结果数量。
- 将 USDT 本位、可交易、币本位等低频范围，以及涨跌、成交量等排序选项收纳到按需展开的控件中。
- 移除冗余列表表头，保留代码、易读名称、永续/结算上下文、价格、涨跌和关注操作的清晰行内层级。
- 明确“已关注”仅表示本系统保存的星标收藏，不承诺同步欧易 App 或官网的自选数据。
- 将行情图表、AI 看行情和交易数据收拢到同一个市场工作台：三页共享当前选中合约、搜索、筛选、排序和左栏行情快照，切换标签时不重置左栏上下文。
- 保持图表页当前的默认本地已关注策略、空状态恢复入口、深链合约展示、实时订阅和星标增删行为不变；直接进入 AI 或交易数据页时保留其现有默认范围。
- 保持合约雷达作为独立候选发现入口，并允许候选合约带入行情图表、AI 看行情和交易数据工作台。
- 为桌面市场工作台的共享左侧合约栏增加可访问的收缩/展开操作，释放右侧行情、AI 与数据面板的横向空间，同时保留已加载的合约与行情上下文。

## Capabilities

### New Capabilities

- `market-instrument-rail-simplification`: 定义市场工作台共享合约选择器的简洁浏览、渐进式筛选、排序、跨标签状态连续性、本地关注表达，以及雷达候选的工作台联动。

### Modified Capabilities

- None.

## Impact

- Affected frontend: `frontend/src/main.tsx`, `frontend/src/styles.css`, and focused market-instrument frontend tests.
- Reuses the existing `/api/instruments` watched flag and `/api/watchlist` add/remove endpoints; no backend API, database schema, external data source, or trading behavior changes are required.
- The shared rail affects the market chart, AI outlook, and trading-data pages. Contract-level analysis and trading-statistics requests remain page-specific.
