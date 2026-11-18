# OKX Perpetual Futures Dashboard

本地运行的 OKX 永续合约行情与账户看板。

## 前端设计规范

所有前端改动均以 [前端设计规范](docs/frontend-design-guidelines.md) 为基线。该规范定义了简洁工具型风格、间距、颜色语义、组件、交互、响应式和验收要求。

第一版范围：

- 支持 OKX `SWAP` 永续合约列表
- 选择任意合约查看动态 K 线
- 支持 `1m / 5m / 15m / 1H / 4H / 1D`
- PostgreSQL 保存合约缓存、关注列表、K 线、账户快照、持仓快照
- 显示 OKX 账户总权益、保证金、持仓、未实现盈亏
- 支持虚拟盘/真实盘环境切换
- 支持 OKX 手动下单、撤单、未成交订单查看、本地订单审计
- 支持自动化交易（策略信号 → 风控闸门 → 自动执行），但执行范围**仅限 OKX 模拟盘**；实盘交易默认关闭

## 配置

```bash
cp .env.example .env
```

如果只看公开行情，可以不填 API Key。显示账户信息需要填写对应环境的 API Key。

推荐分别配置虚拟盘和真实盘：

```bash
OKX_DEMO_API_KEY=
OKX_DEMO_API_SECRET=
OKX_DEMO_API_PASSPHRASE=
OKX_LIVE_API_KEY=
OKX_LIVE_API_SECRET=
OKX_LIVE_API_PASSPHRASE=
```

旧配置 `OKX_API_KEY / OKX_API_SECRET / OKX_API_PASSPHRASE` 仍然兼容：当 `OKX_SIMULATED_TRADING=0` 时按真实盘 Key 处理；当 `OKX_SIMULATED_TRADING=1` 时按虚拟盘 Key 处理。

### 交易环境切换

启动默认环境：

```bash
OKX_TRADING_ENVIRONMENT=live
```

可选值：

- `simulated`：虚拟盘，OKX 请求会带 `x-simulated-trading: 1`
- `live`：真实盘，默认只读

页面里的“手动交易”可以在虚拟盘和真实盘之间切换，选择会保存到数据库，后端重启后继续使用上次选择。

### 实盘交易授权

真实盘环境默认只能看账户、持仓和挂单。要允许真实盘下单，必须显式开启：

```bash
OKX_ENABLE_LIVE_TRADING=1
```

不开启时，真实盘下单和撤单接口会返回 403。

### 手动交易安全加固

订单页顶部提供「当前挂单」区，展示 OKX 实时挂单（`live` / `partially_filled`），每行可二次确认后撤销；撤单请求同样经过实盘授权闸门，成功后写入本地订单审计并刷新挂单。挂单来源显示为实时或缓存。

下单 / 撤单 / 平仓 / 杠杆四个写接口在请求体中携带 `environment`，后端以请求环境为准（`resolve_request_environment`，非法值 fail-closed 返回 400），不再只依赖进程的全局交易环境。这避免了多标签页场景下「一个标签切到真实盘，导致另一个标签的订单落到真实盘」的串扰；请求里的 `environment` 仅用于选择环境与授权校验，不会转发给 OKX。未携带时回退全局环境，自动化链路（硬编码模拟盘）不受影响。

手动下单使用**确定性幂等键** `clOrdId`（`OKXQ` + 时间戳 + 随机串，≤32 位）：同一次提交意图内复用（含网络重试），提交成功后清空、下次提交生成新键；配合按钮的 `submitting` 重入保护，避免重复点击或重试造成 OKX 重复成交。失败时保留键以便安全重试。自动化订单仍沿用由幂等键派生的确定性 `clOrdId`，两套机制互不干扰。

**服务端下单规格强校验**：手动下单在发往 OKX 前，用本地合约规格缓存（`lot_sz` / `tick_sz` / `ct_val`）校验张数为每张规格整数倍、委托价为最小报价单位整数倍、限价单名义价值不低于 5 USDT，越界订单本地返回中文 400，不再等 OKX 拒单。规格缓存缺失时降级放行（由 OKX 兜底），不影响首次启动或离线交易；市价单无委托价时跳过名义价值校验。

**账户刷新去重**：`loadTradingAccount` 增加请求序号（旧响应不覆盖新快照）与 1.5 秒节流，REST 轮询与 WebSocket 私有频道事件共用同一刷新入口、短窗口内合并，避免 `account.update` / `position.update` 事件风暴放大 `/api/account` 调用；下单 / 切环境 / 设杠杆等关键操作跳过节流以保证状态即时刷新。

**结算账单翻页**：历史成交超过 100 笔的账户，结算盈亏改为按 `billId` 游标翻页拉取全部成交账单后再聚合（最多 10 页防无限循环、按 billId 去重），不再只取最近 100 笔；账单接口未就绪或失败时沿用原有估算盈亏，不阻断订单列表。

## 后端

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 前端

```bash
cd frontend
npm install
npm run dev
```

打开 Vite 输出的本地地址，通常是 `http://localhost:5173`。

页面结构：顶部一级导航为 **市场 / 交易 / 订单 / 自动化 / 账户 / 设置**，其余子页走二级 Tabs（市场概况·雷达·行情图表·AI 展望·AI 纪录·市场统计·美国日历·公告，持仓·账户·链上赚币，策略·信号，AI 配置·AI 用量）。交易页只保留下单面板与杠杆设置（单列布局），**订单记录独立成页**（路由 `#/orders`），自带虚拟盘/真实盘切换、合约筛选、来源/动作/状态筛选、本页盈亏汇总与分页，并订阅 orders 实时频道；两页互相有「订单记录 / 去下单」跳转按钮。路由用 hash 保存，刷新后停留在同一页。

## Docker 运行

先准备配置文件：

```bash
cp .env.example .env
```

只看公开行情可以不填写 OKX API Key。需要账户信息时再填写 `.env`：

```bash
OKX_API_KEY=
OKX_API_SECRET=
OKX_API_PASSPHRASE=
OKX_DEMO_API_KEY=
OKX_DEMO_API_SECRET=
OKX_DEMO_API_PASSPHRASE=
OKX_LIVE_API_KEY=
OKX_LIVE_API_SECRET=
OKX_LIVE_API_PASSPHRASE=
OKX_TRADING_ENVIRONMENT=live
OKX_ENABLE_LIVE_TRADING=0
POSTGRES_DB=okx_dashboard
POSTGRES_USER=okx
POSTGRES_PASSWORD=okx_password
```

启动：

```bash
docker compose up -d --build
```

如果 Docker Hub 拉基础镜像比较慢，可以先在 `.env` 里覆盖这些构建参数：

```bash
PYTHON_BASE_IMAGE=python:3.12-slim
NODE_BASE_IMAGE=node:22-alpine
NGINX_BASE_IMAGE=nginx:1.27-alpine
NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
```

在网络不稳定的环境里，也可以把 `NODE_BASE_IMAGE`、`NGINX_BASE_IMAGE`、`PYTHON_BASE_IMAGE` 改成你本机已经缓存的镜像版本，再重新执行 `docker compose up -d --build`。

访问：

- 前端页面：`http://127.0.0.1:5174`
- 后端接口：`http://127.0.0.1:8000/api/health`

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

### Docker 数据持久化

Docker 模式下 PostgreSQL 数据会保存在 Docker named volume：

```text
okx_postgres_data
```

PostgreSQL 容器内路径是：

```text
/var/lib/postgresql/data
```

迁移到新电脑时，至少复制这些内容：

- `.env`
- `docker-compose.yml`
- `Dockerfile.backend`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- 项目源码

并导出数据库备份：

```bash
docker compose exec -T postgres pg_dump -U okx okx_dashboard > okx_dashboard.sql
```

在新电脑安装 Docker 后执行：

```bash
docker compose up -d --build
docker compose exec -T postgres psql -U okx okx_dashboard < okx_dashboard.sql
```

## 安全边界

本项目同时包含手动交易与自动化交易（策略信号 → 风控闸门 → 自动执行）。自动化链路硬编码使用 `simulated` 环境，**只在 OKX 模拟盘下单**，不读取 `OKX_ENABLE_LIVE_TRADING` 开关，也不会向真实盘提交订单。

自动化执行的约束：

- 全局暂停 / 熔断状态读取或解析失败时按「已暂停」处理（fail-closed），不会静默继续下单；
- 后台轮询、手动运行、单策略运行按策略互斥，并以「策略 + 动作 + K 线（止盈止损按分钟）+ 合约」为业务幂等键；单合约策略沿用历史键格式，避免升级后已有幂等记录失效；自动订单使用由幂等键派生的确定性 `clOrdId`，由 OKX 侧再做一层重复订单拒绝；
- 一条策略可绑定多个永续合约（最多 10 个），每轮对每个合约独立生成信号、独立风控、独立下单；K 线去重按合约记录，同一合约只允许一条启用中的策略；
- 策略可设置「每日仓位%」（0 表示不限制）。额度 = 模拟盘账户总权益（回退可用保证金）× 百分比，按 UTC+8 自然日累计**已提交开仓的名义金额**（张数 × 合约面值 × 信号价格）；超出额度、权益读不到或合约面值缺失时一律拦截开仓（fail-closed）。额度在同一条策略的多合约间共享累计，次日零点重置；止盈止损平仓不占用额度；
- 「每次下单」是固定张数，表单不再单独暴露「单笔上限」：提交时按同一张数派生并存库，后端仍保留 `max_order_contracts` 字段与 `sz <= max_order_contracts` 一致性校验。正常策略不会在风控面板生成恒真通过的「单笔限制」检查项；只有数据库出现不一致的脏数据（旧数据、绕过 API 写入）时才会生成拦截项，作为 fail-closed 兜底；
- 策略表单通过 `GET /api/automation/equity` 回显模拟盘账户总权益、可用保证金、按当前百分比折算的每日额度与当日已用额度，口径与风控闸门同源；凭证未配置或读取失败时明确提示「不可读」而不是显示 0，避免误判；
- 止盈止损与开仓共用统一风控闸门，但开仓专属的下单额度 / 冷却期 / LLM 置信度 / 每日仓位限制不会阻拦平仓；平仓前会校验持仓确实存在；
- **止盈止损主路径是本地轮询**：默认不挂交易所条件单，OKX 侧只有持仓、没有止盈止损挂单。后台每 10 秒轮询一次持仓，按 `(标记价格 − 开仓均价) / 开仓均价 × 100`（做空取反）算出**价格变动百分比**，与策略的止盈% / 止损% 比较（**不乘杠杆**：20 倍杠杆下价格反向 2% 即触发 2% 止损），命中后对该合约发市价全平（一次平完，不分批）。阈值为 0 表示关闭该项；执行方式非 `simulated_auto` 时完全不检查；
- **交易所侧条件单兜底（默认关闭，灰度开关 `OKX_ENABLE_EXCHANGE_ALGO_TPSL=1`）**：开启后，仅在 `simulated_auto` 且开仓单取得成交均价时，按同一口径换算绝对触发价，在 OKX 补挂 OCO 止盈止损算法单（单腿退化为 conditional，`reduceOnly`，mark 触发，触发后市价成交），作为进程停止 / 断网时的兜底。本地轮询仍是主防线：本地平仓、反向、策略归档前会先撤销残留算法单避免双轨重复平仓；启动时对账标记孤儿单；算法单失败只记告警、不阻断本地平仓。字段语义上线前须按 `docs/exchange-algo-order-design.md` §6 在模拟盘逐项实测。开关关闭时行为与原先完全一致（无交易所侧兜底）；
- 反向信号「先平后开」失败时保留已发生的平仓步骤、触发熔断并生成需人工补偿的 critical 告警；
- 风控快照与执行步骤写入信号审计记录，可在信号详情中查看。

LLM 直判信号提示词（`llm_direct` 模板，`LLM_PROMPT_VERSION=signal-analysis-v3`）：分两层组装——① 系统 Prompt 在 AI 配置页可编辑（默认含「分析框架 / 决策原则 / 输出纪律」三段：自上而下先看市场环境再看个币，按市场环境 → 趋势结构 → 动量位置 → 量价配合 → 情绪与一致性顺序判断，置信度按证据充分度分档校准，并要求失效条件可验证、环境优先、赛道共振、风险优先、已有同向持仓不重复加仓）；② 用户 Prompt 由 `llm_direct_signal_prompt()` 动态组装为紧凑 JSON，含 `constraints` / `decision_guide`（第 0 步定环境 + 四步个币分析）/ `expected_json_schema` / **`market_context`**，以及策略参数、K 线摘要与最近 60 根 K 线、当前持仓、近期信号、账户摘要。输出字段契约（`action / confidence / summary / reasons / risks / invalidation / notes`）与 70 分置信度闸门均保持不变。系统 Prompt 命中历史默认文案（含更早两版）时自动迁移到 v3，用户自定义文案不受影响；前端配置页默认值与后端保持同源。

市场上下文（`market_context`，由 `backend/app/market_context.py` 纯函数聚合、`main.py` 负责拉取与缓存）：每轮给 LLM 提供「大盘 → 赛道 → 情绪」三层背景，**仅作为 LLM 判断参考，不参与风控拦截**。① 大盘：BTC/ETH 24h 涨跌与区间位置、全市场涨跌家数与上涨占比、中位涨跌；② 赛道：L1 / L2 / Meme / AI / DeFi 五个篮子按成分币 24h 涨跌聚合出平均涨跌、上涨占比与龙头，成分按 OKX 实际合约自动过滤；③ 情绪：资金费率正负分布（BTC/ETH + 赛道龙头采样）、全市场未平仓量（OI）。综合出 `bias`（risk-on / mixed / risk-off，阈值保守）。缓存 60 秒刷新、失败时 15 分钟内复用旧快照；彻底不可读时字段标记 `available=false` 并提示 LLM 更保守，不阻断信号生成。该层不改变开仓/平仓风控闸门与每日额度。

订单盈亏口径：订单页「本地订单记录」新增「盈亏」列与本页合计，分两级口径，优先展示**交易所结算值**：

- **已结算（主口径）**：读取 OKX 交易账单 `/api/v5/account/bills`（type=2），按 `clOrdId` 把同一订单的多笔成交聚合为毛盈亏 `pnl` 与手续费 `fee` 之和，即含手续费的真实结算净盈亏（`pnl_basis=okx-bills-settled`，界面标注「OKX 已结算（含手续费）」，虚线下划线区分）。单元格同时展开「毛盈亏 / 手续费 / 成交笔数」。账单是已结算不可变流水，缓存 30 秒、过期 10 分钟内可降级复用；无凭证或接口失败时静默回退到估算值，不阻断订单列表。新平仓单落库后主动使缓存失效。
- **估算（降级口径）**：`sim_order_events` 保存 `pnl_usd / pnl_pct / pnl_basis`；平仓请求发出前读取 OKX 持仓快照的 `upl`（未实现盈亏，USDT）作为**平仓前浮动盈亏**近似值，来源标签为实时 / 平仓前 / 信号留存 / 历史持仓快照 / 价格估算。历史订单按 `clOrdId` 关联自动化信号，或缺快照时取平仓前 2 分钟内最近一次同合约持仓快照回填。该值不含成交滑点、手续费、资金费，也不做开平配对；缺少快照且无账单的平仓单显示 `—` 并说明原因。

订单行同时显示订单号与来源策略 / 信号。`pnlSummary` 增加 `settledCloses`（本页按账单结算的笔数），合计以每单最终展示值为准。SQLite 与 Postgres 均通过新增列平滑迁移，旧库无需重建。

订单来源区分（`sim_order_events.origin`）：订单记录按**发起方**拆成 `manual`（手动下单 / 平仓 / 撤单、本地模拟单、从本地页提交的任何委托）与 `automation`（自动化策略在 `execute_automation_order` / `execute_automation_exit` 里提交的开仓与平仓）。订单页「本地订单记录」提供「全部来源 / 自动化 / 手动」三档切换（带条数，条数不受来源筛选影响），每行「来源」列显示徽章并附策略 / 信号编号或「手动操作」。`GET /api/trading/orders` 支持 `origin` 参数（非法值按全部处理），返回 `origin` 与 `originCounts{manual,automation,all}`。WS 订单推送（`ws-order`）沿用该 `clOrdId` 首次落库的来源，不会把自动化单翻成手动；老库升级后默认 `manual`，启动时 `backfill_automation_order_origins()` 用信号审计里的 `clOrdId` 把历史上由策略提交的订单回填为 `automation`（幂等，只更新不一致的行）；读取时若订单能对上自动化信号也会强制归为自动化。口径是「谁发起了这笔操作」，因此自动化开的仓被手动平掉时，那条平仓单记 `manual`。

平仓归属（`close_strategy_id` / `close_strategy_name`）：来源只回答「谁按下了这个操作」，回答不了「平的是谁的仓」。订单列表对平仓单额外做一次归属回填——按「同合约 + 平仓时间之前最近一笔 `decision=submitted` 的自动化开仓信号（long/short）」匹配，默认 24 小时窗口；平仓单若带了 `side`，还要求方向与开仓相反（`sell` 平多、`buy` 平空），净持仓全平不带 side 时只按合约与时间匹配。命中后界面在来源列补一行「平 策略 #N 仓」，鼠标悬停显示策略名与「本次平仓由手动/接口发起」。因此自动化开仓 + 手动平仓的单据会读成「手动 · 平 策略 #4 仓」，两层信息都不丢。

手动交易的真实盘下单仍须显式开启 `OKX_ENABLE_LIVE_TRADING=1`，未开启时真实盘下单和撤单接口返回 403。建议 OKX API Key 禁用提现权限，并配置 IP 白名单。
