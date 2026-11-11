## Why

行情图表首次进入时默认展示大量 USDT 本位合约，用户必须先切换到“自选”才能看到自己持续关注的标的。将默认入口改为自选可让左侧合约列表直接服务于日常观察，同时仍保留全部现有筛选方式。

## What Changes

- 行情图表页首次进入时默认启用“自选”筛选。
- 自选为空时，显示明确的空状态和一个切换到“全部”合约的恢复入口。
- 通过链接或其他页面打开指定合约时，保留右侧当前合约，不因左侧自选筛选自动切换合约或自动添加收藏。
- 保持用户在页面内手动选择的筛选、搜索、排序、星标收藏和实时订阅行为不变。
- 此次范围仅限行情图表页；AI 看行情和交易数据页保持现有默认筛选。

## Capabilities

### New Capabilities

- `market-chart-watchlist-default`: 行情图表页以持久化自选合约作为默认左侧合约列表，并在自选为空时提供可恢复的浏览路径。

### Modified Capabilities

- None.

## Impact

- Affected frontend: `frontend/src/main.tsx` and market-instrument focused tests.
- Reuses the existing `/api/instruments` watched flag and watchlist add/remove endpoints; no backend API, storage schema, market-data source, or external dependency changes are required.
- Does not change trading, AI analysis, or order-entry behavior.
