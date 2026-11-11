## Why

AI 看行情已经能基于受控的行情、宏观与多周期证据生成只读报告，但其领域约束主要散落在提示词中，无法独立版本化、审计或随规则变化而使旧报告缓存失效。引入固定版本的 OKX 公开行情 Skill Profile，可以让模型输入的数据范围、只读边界和报告用语成为可测试的产品合同，而不把外部 CLI 或交易能力暴露给模型。

## What Changes

- 新增一个固定版本、可校验哈希的 `okx-market-reading` Skill Profile，记录其参考的 `okx/agent-skills` 市场数据 Skill 来源与 MIT 许可。
- 在每次手动 AI 看行情分析前，将 Profile 的公开行情只读规则与现有经过验证的市场、交易统计、宏观和多周期证据一起传给 LLM。
- 在 AI 看行情响应、缓存键和 LLM 用量审计中记录 Profile 身份与版本；Profile 更新后不复用旧报告缓存。
- 在 AI 看行情页面的来源区域以紧凑、可访问的方式显示本次分析所用的只读行情规则；旧响应保持兼容。
- 明确禁止运行 `okx` CLI、下载上游 Skill、访问私有账户数据、提交订单、创建机器人或让模型自由执行工具。

## Capabilities

### New Capabilities

- `readonly-okx-market-skill-profile`: 为手动 AI 看行情定义、应用、审计和展示固定版本的公开行情只读 Skill Profile。

### Modified Capabilities

- None.

## Impact

- 后端：`backend/app/main.py` 的 AI 行情 Prompt、缓存键、响应元数据和用量审计；新增 Profile 模块与测试。
- 前端：`frontend/src/main.tsx` 的 AI 看行情类型与来源说明，以及对应静态测试。
- 文档与许可：新增上游来源、固定提交和 MIT 说明；生产运行不增加 CLI、账户权限或外部运行时依赖。
