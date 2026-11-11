## Why

未确认的行情目前统一显示为“暂不追向”，即使已经出现短线偏多或偏空线索，用户也无法分辨是没有方向、方向分歧，还是仅差最后一个确认条件。首屏需要减少解释性噪音，直接说明当前倾向及其确认进度。

## What Changes

- 将未确认方向拆分为“短线偏多（未确认）”“短线偏空（未确认）”和“无明确方向”。
- 以紧凑的“当前倾向 / 已满足 / 还差什么”替代长段落与重复的场景说明。
- 对已确认方向保留“偏多观察 / 偏空观察”；不改变既有确认门槛。
- 将双向细节和完整数据证据留在可展开区域，保持公开行情快照与非执行边界。

## Capabilities

### New Capabilities

- `layered-market-direction-reading`: 将规则化行情状态呈现为确认、短线偏向或无方向的可读分层。

### Modified Capabilities

- None.

## Impact

- `backend/app/main.py` 方向摘要的状态和简洁原因字段。
- `frontend/src/main.tsx`、`frontend/src/styles.css` 的 AI 看行情首屏信息层级。
- 后端方向状态与前端阅读文案测试。
