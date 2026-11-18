# P2-2 交易所侧止盈止损条件单兜底：实施方案（待评审）

> 状态：**已实施，默认关闭（灰度）**。PR1–PR4 已落地，开关 `OKX_ENABLE_EXCHANGE_ALGO_TPSL` 默认 false；
> 关闭时行为与原先完全一致。上线前须按本文 §6 在模拟盘逐项实测，通过后再考虑开启开关。
> 前置结论：技术上可接入，但涉及策略口径变更、双轨平仓协调、条件单生命周期三部分系统性改造，
> 且会改变 README 已披露的"无交易所侧兜底"产品语义，故采用默认关闭的灰度策略。

---

## 1. 背景与目标

### 1.1 现状

- 自动化的止盈止损是**本地 10 秒轮询**：`automation_exit_signal()`（`main.py:7900`）每轮读取仓位，
  用 `position_profit_pct()`（`main.py:7884`）算 `(markPx - avgPx) / avgPx × 100`（做空取反；
  读不到均价时退回 `uplRatio × 100`），与策略的 `take_profit_pct` / `stop_loss_pct` 比较，命中后由
  `execute_automation_exit()` 发市价全平。
- **口径特征**：按"价格变动百分比"判定，**不乘杠杆**（20 倍杠杆下价格反向 2% 即触发 2% 止损）。
- **对外承诺**：README:211 明确写明"不开具交易所条件单、进程停止即失去保护"。
- 执行模式仅 `signal_only` / `simulated_auto`，自动化下单硬编码 `simulated`（`execute_automation_order`）。

### 1.2 目标

在开仓时向 OKX 附带交易所侧止盈止损条件单（`attachAlgoOrds`），使**后台进程停止 / 断网期间**
仍有交易所侧保护。保持现有本地轮询作为"响应式主路径"，条件单作为"兜底防线"。

### 1.3 非目标（明确排除）

- 不改变手动下单行为（手动交易不附带条件单）。
- 不引入实盘自动交易（仍仅 `simulated_auto`）。
- 不做移动止损 / 追踪止损 / 分批止盈。

---

## 2. 三个核心难点与解法

### 2.1 难点一：口径转换（价格变动 % → 绝对触发价）

**问题**：本地口径是"相对开仓均价的价格变动百分比、不乘杠杆"；OKX 条件单要的是绝对触发价
（`tpTriggerPx` / `slTriggerPx`）。自动化开仓多为市价单（`ord_type` 可为 market），下单时成交均价未知，
无法在发单瞬间精确算出触发价。

**解法：成交后补挂（fill-then-attach），而非随开仓单附带**

1. 开仓单发出后，从下单响应 `data[].ordId` 取订单号；轮询 `GET /api/v5/trade/order` 或读 WS
   `orders` 频道，等该单**完全成交**，取成交均价 `avgPx`。
2. 用成交均价换算触发价：
   - 做多（`posSide=long`）：`slTriggerPx = avgPx × (1 - slPct/100)`，`tpTriggerPx = avgPx × (1 + tpPct/100)`
   - 做空（`posSide=short`）：`slTriggerPx = avgPx × (1 + slPct/100)`，`tpTriggerPx = avgPx × (1 - tpPct/100)`
   - 按合约 `tickSz` 向**触发方向取整**（价格向下取 floor / 向上取 ceil），保证不会因精度被 OKX 拒单。
3. 用独立的算法下单接口 `POST /api/v5/trade/order-algo` 挂 OCO（止盈止损二选一，`reduceOnly=true`，
   `sz` = 实际成交张数），而不是塞在开仓单的 `attachAlgoOrds` 里——**因为成交价未知，必须先成交再挂**。
   - 触发价类型用 `markPx`（与本地轮询的 `markPx` 口径一致；需模拟盘实测确认 `slTriggerPxType` 是否支持 mark）。
   - `tpOrdPx` / `slOrdPx` 设为 `-1`（市价触发，OKX 语义：触发后以市价单发出）。
4. 若策略只设了止盈或只设了止损，OCO 退化为单腿条件单；两者都为 0 则不挂。

> **备选方案（随开仓单附带 `attachAlgoOrds`）**：仅在开仓是限价单且价格确定时可用，触发价以委托价为基准。
> 但自动化策略大量用市价单，覆盖面不足，且委托价 ≠ 成交价仍有偏差。故主方案采用"成交后补挂"。

**口径一致性校验**：本地轮询仍用 `avgPx` 与 `markPx`，条件单触发价也基于 `avgPx`。两者基准一致，
只有"百分比 → 绝对价"的一次性换算，无累计漂移。取整方向须保证条件单触发不早于本地阈值（略放宽），
避免条件单先于本地轮询触发造成双轨竞争。

### 2.2 难点二：双轨平仓协调（本地轮询 + 条件单）

**问题**：本地轮询命中会市价全平；条件单命中也会平仓。若不协调，可能出现同一仓位被平两次
（第二次 OKX 返回 51000 "无仓位"），产生错误告警与审计噪音。

**解法：本地轮询"优先、去重"，条件单"兜底"**

1. **本地为主**：进程运行时，止盈止损仍由本地轮询触发（响应快、可写业务审计与信号记录）。
2. **条件单兜底**：仅在进程停止 / 本地未及时触发时由 OKX 触发。
3. **去重机制**：
   - 本地平仓提交前，先查该合约是否已有对应算法单在途；若有，先撤条件单再本地平仓
     （避免条件单随后触发）。撤销失败不阻断本地平仓，仅记 warning。
   - 本地平仓成功后，主动撤销该合约残留的止盈止损算法单（按 `attachAlgoClOrdId` 精确定位）。
   - 条件单触发（OKX 侧成交）会通过 WS `orders` / `positions` 事件推送，本地轮询读到仓位归零后
     自然不再触发；`automation_exit_signal` 已校验持仓存在（`main.py:7900` 读 `position_state["rows"]`），
     无仓就不会生成平仓信号——这层天然去重须保留并补测试。
4. **幂等键**：算法单也用确定性 `attachAlgoClOrdId`（由 execution_id 派生，类似
   `client_order_id_for_execution`），防止重试重复挂单。

### 2.3 难点三：条件单生命周期管理

| 场景 | 处理 |
|---|---|
| 开仓成交后挂单 | 见 2.1，成交后补挂 OCO |
| 信号反转（先平后开） | 平仓前撤销旧算法单；新仓成交后挂新算法单 |
| 部分成交 | 按实际成交张数挂单；未成交部分不开条件单 |
| 开仓单撤单 / 超时未成交 | 无成交则不挂；清理可能的孤儿单 |
| 本地平仓 / 手动平仓 | 平仓成功后撤销该合约残留算法单 |
| 策略归档 / 停用 | 撤销该策略关联的全部算法单（需记录 strategy_id → 算法单映射） |
| 进程重启 | 启动时对账：本地记录的在途算法单 vs OKX 实际算法单，清理孤儿单、补挂缺失单 |
| 条件单被 OKX 拒绝 | 记 warning + 审计，不阻断本地轮询保护；本地仍是主防线 |

**持久化映射**：新增表 `automation_algo_orders`，字段
`strategy_id / inst_id / pos_side / attach_algo_cl_ord_id / main_ord_id / state / created_at / updated_at`，
用于精确定位撤改与重启对账。`state` 取值 `pending / attached / triggered / cancelled / orphan`。

---

## 3. 改动清单

### 3.1 后端

| 文件 | 改动 |
|---|---|
| `backend/app/okx.py` | 新增 `place_algo_order(payload)`、`cancel_algo_order(payload)`、`get_algo_orders(inst_id?)`、`get_order(ord_id)`（均走 `_request`，auth=True）。方法名与 OKX 端点：`POST /api/v5/trade/order-algo`、`POST /api/v5/trade/cancel-algo-order`、`GET /api/v5/trade/algo-current-orders`、`GET /api/v5/trade/order`。 |
| `backend/app/main.py` | ① `algo_trigger_prices(avg_px, side, tp_pct, sl_pct, tick_sz)` 纯函数（口径换算 + 取整，便于测试）；② `build_algo_order_payload(...)`；③ `attach_algo_orders_for_fill(...)`（成交后补挂，含幂等）；④ `cancel_algo_orders_for_position(...)`；⑤ 在 `execute_automation_order` 的开仓成功后调用补挂；⑥ 在 `execute_automation_exit` / 手动平仓 / 策略归档处调用撤单；⑦ 启动时对账任务。 |
| `backend/app/db.py` | 新增 `automation_algo_orders` 表的 CRUD。 |
| `backend/app/config.py` | 新增开关 `OKX_ENABLE_EXCHANGE_ALGO_TPSL`（默认 **false**，灰度用）+ 轮询/超时参数。 |

### 3.2 前端

| 文件 | 改动 |
|---|---|
| `frontend/src/main.tsx` | 策略表单止盈止损提示文案更新：从"不挂条件单"改为"成交后在 OKX 附带交易所侧条件单兜底（需开关开启）"；信号详情展示关联算法单状态。 |
| `frontend/src/*.static.test.mjs` | 更新断言（现有断言可能锁定"不挂条件单"文案，需同步）。 |

### 3.3 文档

- `README.md:211`：更新口径，明确"条件单兜底 + 本地轮询主路径"双轨语义，以及开关状态。
- 本设计稿状态改为"已实施"。

---

## 4. 实施步骤（建议分 4 个可独立验收的 PR）

1. **PR1 纯函数与数据层**：`algo_trigger_prices` / `build_algo_order_payload` + `automation_algo_orders` 表 + OKX client 四个方法。测试：口径换算边界、取整方向、payload 字段。此时不改变任何交易行为。
2. **PR2 挂单链路**：成交后补挂（开关默认关闭）。测试：mock 成交回报 → 挂单 payload 正确；幂等键；只设单边；tick 取整。开关关闭时不挂。
3. **PR3 撤单与协调**：本地平仓/反转/归档撤单 + 去重；启动对账。测试：双轨场景不重复平仓、撤单失败不阻断、重启清理孤儿单。
4. **PR4 灰度与文档**：默认关闭开关下模拟盘实测（见 §6），验证通过后再考虑开启；更新前端文案与 README。

---

## 5. 测试计划

- **单元**：口径换算（多空 × 止盈止损 × 边界百分比 × tick 取整）、payload 构造、幂等键派生、状态机流转。
- **集成**：mock 成交回报 → 补挂 → 条件单成交事件 → 本地不重复平仓；反转先撤后开；部分成交。
- **契约**：用 OKX 模拟盘真实调用一次 `order-algo` / `cancel-algo-order` / `algo-current-orders`，核对字段与返回码（见 §6）。
- **回归**：后端 374+、前端静态 165+、tsc + build 全绿。

---

## 6. 上线前必须实测验证的未知项（重要）

本方案中 OKX 字段语义基于既有 API 知识，**当前项目未接入过算法单，文档页为动态渲染未能实时抓取核实**。
动手前须在 OKX **模拟盘**用最小仓位逐项实测：

1. `POST /api/v5/trade/order-algo` 的必填字段、OCO（`tpTriggerPx` + `slTriggerPx` 同时传）是否被支持。
2. `slTriggerPxType` / `tpTriggerPxType` 是否支持 `mark`（若不支持，改用 `last`，并把本地口径同步改为 latest 价，或接受口径偏差并在文档披露）。
3. `tpOrdPx` / `slOrdPx = -1` 的市价触发语义在该品种是否有效。
4. 模拟盘是否支持 `attachAlgoClOrdId` 幂等，以及重复提交返回码。
5. 算法单成交后 WS 事件类型与字段，确认本地去重能读到。
6. `amendPxOnTriggerTime` 等可选字段是否需要显式关闭。

> 若实测发现模拟盘不支持 mark 触发或 OCO，需回退到"单腿条件单 + 本地轮询"组合，并重新评估收益。

---

## 7. 风险与回滚

- **风险**：口径偏差导致条件单早于/晚于本地阈值触发；双轨竞争；孤儿算法单；模拟盘 API 限制。
- **缓解**：开关默认关闭、灰度开启；条件单触发价取整时向"不利方向"放宽（宁可晚触发，不早触发）；
  完整的撤单与对账逻辑；所有条件单失败都只记 warning、不阻断本地主防线。
- **回滚**：关闭 `OKX_ENABLE_EXCHANGE_ALGO_TPSL` 开关即回到纯本地轮询；已挂算法单由运维脚本
  按 `automation_algo_orders` 表批量撤销。

---

## 8. 决策建议

保持"本地轮询为主、条件单为兜底"的双轨结构，按 PR1→PR4 推进，**PR4 前不开启开关**。
若 §6 实测发现 mark 触发 / OCO 不可用，或团队不接受"双轨 + 生命周期"的维护成本，
则维持现状（纯本地轮询），README 口径不变——这也是当前推荐项。
