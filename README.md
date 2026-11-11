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
- 不产生策略信号，不自动下单；实盘交易默认关闭

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

本项目只实现手动交易，不会产生策略信号，也不会自动下单。后端默认阻止真实盘交易请求，只有 `OKX_ENABLE_LIVE_TRADING=1` 时才允许真实盘下单/撤单。为了保护账户，建议 OKX API Key 禁用提现权限，并配置 IP 白名单。
