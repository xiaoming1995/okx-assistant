from __future__ import annotations

import asyncio
import calendar
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from copy import deepcopy
import hashlib
from html import unescape
import json
import logging
import re
import time
import uuid
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from http.client import IncompleteRead
from threading import Condition, RLock, Thread
from typing import Annotated, Any, Optional, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import Settings
from .db import Database
from .ai_skills.okx_market_reading import (
    compile_okx_market_reading_context,
    unavailable_okx_market_reading_metadata,
)
from .ai_outlook_verification import (
    grade_sample,
    prompt_sample_context,
    public_sample,
    sample_summary,
    samples_for_report,
)
from .okx import OkxClient, OkxError, net_mode_retry_payload, now_ms
from .okx_ws import (
    OkxWsError,
    candle_channel,
    stream_market_data,
    stream_private_account_data,
    stream_public_candles,
    stream_public_tickers,
)
from .realtime import (
    AUTOMATION_TOPICS,
    MARKET_TOPICS,
    PRIVATE_TOPICS,
    RealtimeHub,
    RealtimeSession,
    cancel_tasks,
    normalize_inst_ids,
    normalize_subscription_message,
)


SUPPORTED_BARS = {"1m", "5m", "15m", "1H", "4H", "1D"}
CANDLE_BAR_MILLISECONDS = {
    "1m": 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "1H": 60 * 60_000,
    "4H": 4 * 60 * 60_000,
    "1D": 24 * 60 * 60_000,
}
CANDLE_CACHE_FRESHNESS_BARS = 3
CANDLE_GAP_TOLERANCE_BARS = 2
TICKER_REFRESH_BACKOFF_BASE_MS = 5_000
TICKER_REFRESH_BACKOFF_MAX_MS = 60_000
ORDER_BOOK_CACHE_MS = 2_000
ORDER_BOOK_MAX_AGE_MS = 15_000
ORDER_BOOK_RETRY_MS = 5_000
PLATFORM_VOLUME_CACHE_MS = 60_000
PLATFORM_VOLUME_MAX_AGE_MS = 15 * 60_000
PLATFORM_VOLUME_RETRY_MS = 30_000
ACCOUNT_REFRESH_BACKOFF_BASE_MS = 5_000
ACCOUNT_REFRESH_BACKOFF_MAX_MS = 60_000
MARKET_STATS_SUPPORTED_PERIODS = {"5m", "15m", "30m", "1H", "2H", "4H", "6H", "12H", "1D"}
MARKET_STATS_DEFAULT_PERIOD = "5m"
MARKET_STATS_CACHE_SECONDS = 45
MARKET_AI_OUTLOOK_PROMPT_VERSION = "market-ai-outlook-v8-verified-samples"
MARKET_AI_OUTLOOK_CACHE_SECONDS = 180
MARKET_AI_MACRO_CACHE_SECONDS = 3600
MARKET_AI_MACRO_STALE_SECONDS = 86400
MARKET_AI_CANDLE_LIMIT = 120
MARKET_AI_PROMPT_CANDLES = 30
MARKET_AI_HORIZON_CANDLE_LIMIT = 90
MARKET_AI_HORIZON_DETAIL_LIMIT = 8
CHART_SNAPSHOT_CACHE_SECONDS = 300
CHART_SNAPSHOT_CANDLE_LIMIT = 200
US_EVENT_TIMEZONE = "America/New_York"
US_EVENT_CATEGORIES = {"monetary", "inflation", "employment", "growth", "consumption", "trade", "treasury"}
US_EVENT_STATES = {"scheduled", "released", "revised", "cancelled"}
US_EVENT_MAX_DAYS = 31
US_EVENT_CACHE_SECONDS = 1800
US_EVENT_NEAR_CACHE_SECONDS = 300
US_EVENT_NEAR_WINDOW_MS = 6 * 60 * 60 * 1000
BLS_RELEASE_SERIES = {
    "Consumer Price Index": {
        "series_id": "CUUR0000SA0",
        "unit": "CPI-U（1982-84=100）",
    },
    "Producer Price Index": {
        "series_id": "WPUFD4",
        "unit": "PPI 最终需求（1982=100）",
    },
    "Employment Situation": {
        "series_id": "CES0000000001",
        "unit": "非农就业人数（千人）",
    },
    "Job Openings and Labor Turnover": {
        "series_id": "JTS000000000000000JOL",
        "unit": "职位空缺（千人）",
    },
}
BLS_RELEASE_DATA_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_RELEASE_MATCH_WINDOW_MS = 45 * 24 * 60 * 60 * 1000
# This verified cache is used only when BLS's public calendar is blocked by
# Akamai.  Its dates/times are copied from BLS's per-release official schedule
# pages and are replaced by a successful live calendar read.  Keeping it local
# means an upstream 403 cannot turn an already published historical timeline
# into an empty screen.
BLS_VERIFIED_SCHEDULE_2026 = {
    "Consumer Price Index": [
        ("2026-01-13", "08:30 AM"), ("2026-02-13", "08:30 AM"), ("2026-03-11", "08:30 AM"),
        ("2026-04-10", "08:30 AM"), ("2026-05-12", "08:30 AM"), ("2026-06-10", "08:30 AM"),
        ("2026-07-14", "08:30 AM"), ("2026-08-12", "08:30 AM"), ("2026-09-11", "08:30 AM"),
        ("2026-10-14", "08:30 AM"), ("2026-11-10", "08:30 AM"), ("2026-12-10", "08:30 AM"),
    ],
    "Producer Price Index": [
        ("2026-01-14", "08:30 AM"), ("2026-01-30", "08:30 AM"), ("2026-02-27", "08:30 AM"),
        ("2026-03-18", "08:30 AM"), ("2026-04-14", "08:30 AM"), ("2026-05-13", "08:30 AM"),
        ("2026-06-11", "08:30 AM"), ("2026-07-15", "08:30 AM"), ("2026-08-13", "08:30 AM"),
        ("2026-09-10", "08:30 AM"), ("2026-10-15", "08:30 AM"), ("2026-11-13", "08:30 AM"),
        ("2026-12-15", "08:30 AM"),
    ],
    "Employment Situation": [
        ("2026-01-09", "08:30 AM"), ("2026-02-11", "08:30 AM"), ("2026-03-06", "08:30 AM"),
        ("2026-04-03", "08:30 AM"), ("2026-05-08", "08:30 AM"), ("2026-06-05", "08:30 AM"),
        ("2026-07-02", "08:30 AM"), ("2026-08-07", "08:30 AM"), ("2026-09-04", "08:30 AM"),
        ("2026-10-02", "08:30 AM"), ("2026-11-06", "08:30 AM"), ("2026-12-04", "08:30 AM"),
    ],
    "Job Openings and Labor Turnover": [
        ("2026-01-07", "10:00 AM"), ("2026-02-05", "10:00 AM"), ("2026-03-13", "10:00 AM"),
        ("2026-03-31", "10:00 AM"), ("2026-05-05", "10:00 AM"), ("2026-06-02", "10:00 AM"),
        ("2026-06-30", "10:00 AM"), ("2026-08-04", "10:00 AM"), ("2026-09-01", "10:00 AM"),
        ("2026-09-29", "10:00 AM"), ("2026-11-03", "10:00 AM"), ("2026-12-01", "10:00 AM"),
    ],
}
MARKET_AI_HORIZON_BARS = {
    "15m": ["1m", "5m"],
    "1h": ["5m", "15m"],
    "today": ["15m", "1H", "4H"],
}
MARKET_AI_FIXED_TREND_PERIODS = (
    ("15m", "15m", "15分钟"),
    ("1H", "1H", "1小时"),
    ("1D", "1D", "日线"),
)
EARN_CACHE_SECONDS = 60
EARN_STAKING_CACHE_SECONDS = 60
EARN_APY_CACHE_SECONDS = 300
ANNOUNCEMENT_TYPES_CACHE_SECONDS = 3600
ANNOUNCEMENTS_CACHE_SECONDS = 120
ANNOUNCEMENT_LANGUAGES = {"zh-CN", "en-US"}
DEFAULT_ANNOUNCEMENT_TYPES = [
    {"annType": "announcements-new-listings", "annTypeDesc": "新币种上线"},
    {"annType": "announcements-delistings", "annTypeDesc": "币对下线"},
    {"annType": "latest-events", "annTypeDesc": "最新活动"},
    {"annType": "announcements-trading-updates", "annTypeDesc": "交易规则更新"},
    {"annType": "announcements-deposit-withdrawal-suspension-resumption", "annTypeDesc": "充提暂停/恢复公告"},
    {"annType": "announcements-p2p-trading", "annTypeDesc": "C2C 公告"},
    {"annType": "announcements-web3", "annTypeDesc": "Web3"},
    {"annType": "announcements-earn-and-loan", "annTypeDesc": "赚币与借币"},
    {"annType": "announcements-jumpstart", "annTypeDesc": "Jumpstart"},
    {"annType": "announcements-api", "annTypeDesc": "API 公告"},
    {"annType": "announcements-okb-buy-back-burn", "annTypeDesc": "OKB 销毁"},
    {"annType": "announcements-others", "annTypeDesc": "其他"},
]
EARN_PROTOCOL_TYPES = {"", "defi", "staking"}
EARN_ACTIVE_ORDER_STATES = {"", "8", "13", "9", "1", "2"}
EARN_STAKING_HISTORY_TYPES = {"", "purchase", "redeem"}
EARN_STAKING_HISTORY_STATUSES = {"", "pending", "success", "failed", "cancelled"}
EARN_APY_DEFAULT_DAYS = 30
TRADING_ENVIRONMENTS = {"simulated", "live"}
TRADE_MODES = {"cross", "isolated"}
ORDER_SIDES = {"buy", "sell"}
POSITION_SIDES = {"net", "long", "short"}
ORDER_TYPES = {"market", "limit", "post_only", "fok", "ioc", "optimal_limit_ioc"}
ORDER_TYPES_WITH_PRICE = {"limit", "post_only", "fok", "ioc"}
ORDER_TAG = "OKXQUANTDEMO"
ORDER_CACHE_MS = 5_000
ORDER_STALE_MS = 60_000
AUTOMATION_INTERVAL_SECONDS = 10
AUTOMATION_TEMPLATES = {"ma_cross", "llm_direct"}
AUTOMATION_EXECUTION_MODES = {"signal_only", "simulated_auto"}
AUTOMATION_ACTIONS = {"hold", "long", "short"}
AUTOMATION_LLM_MIN_CONFIDENCE = 70
AUTOMATION_LLM_LOOKBACK_CANDLES = 120
AUTOMATION_LLM_PROMPT_CANDLES = 60
AUTOMATION_GLOBAL_STATE_KEY = "automation_global_state"
LLM_DEFAULT_TIMEOUT_SECONDS = 20
LLM_DIRECT_MIN_TIMEOUT_SECONDS = 20
LLM_CONFIG_KEY = "llm_signal_config"
RADAR_CACHE_KEY = "contract_radar_snapshot"
RADAR_ANALYSIS_CACHE_KEY = "contract_radar_analysis_snapshot"
RADAR_CACHE_SECONDS = 60
RADAR_ANALYSIS_CACHE_SECONDS = 180
RADAR_DEFAULT_BAR = "15m"
RADAR_CANDLE_LIMIT = 80
RADAR_DEFAULT_LIMIT = 30
RADAR_CANDIDATE_LIMIT = 60
RADAR_CANDLE_MAX_WORKERS = 4
RADAR_CANDLE_RECOVERY_MAX_WORKERS = 2
RADAR_DEFAULT_SORT = "turnover_1h"
RADAR_SORT_KEYS = {"turnover_1h", "turnover_24h"}
RADAR_ONE_HOUR_CANDLE_COUNT = 4
RADAR_LLM_EXPLAIN_LIMIT = 10
RADAR_MARKET_TOP_LIST_LIMIT = 8
RADAR_MARKET_LEADER_LIMIT = 10
RADAR_PLAYABLE_QUOTE_VOLUME = Decimal("10000000")
RADAR_SCHEMA_VERSION = 4
LLM_PROVIDERS = {"openai_compatible", "custom"}
LLM_MODES = {"explain_only", "review", "direct_signal"}
LLM_PROMPT_VERSION = "signal-analysis-v1"
LEGACY_LLM_SYSTEM_PROMPT = (
    "你是一个谨慎的永续合约量化交易信号分析助手。"
    "只基于输入的结构化数据分析，不编造不存在的行情。"
    "你的输出必须是 JSON，不要输出 Markdown。"
    "LLM 不能直接下单，只能解释或复核候选信号。"
)
DEFAULT_LLM_SYSTEM_PROMPT = (
    "你是一个谨慎的永续合约量化交易信号分析助手。"
    "只基于输入的结构化数据分析，不编造不存在的行情。"
    "你可以输出做多、做空或观望信号，但不能声称已经下单。"
    "系统会独立执行风控，自动执行仅限 OKX 模拟盘。"
    "你的输出必须是 JSON，不要输出 Markdown。"
)

settings = Settings.from_env()
logger = logging.getLogger(__name__)
database = Database(settings.database_url)
client = OkxClient(settings)
realtime_hub = RealtimeHub()
ticker_cache_lock = RLock()
ticker_cache_condition = Condition(ticker_cache_lock)
ticker_cache: dict[str, Any] = {
    "data": [],
    "ts": 0,
    "refreshing": False,
    "warning": "",
    "failureCount": 0,
    "nextRetryAt": 0,
}
platform_volume_cache_lock = RLock()
platform_volume_cache: dict[str, Any] = {"snapshot": None, "receivedAt": 0, "refreshing": False, "nextRetryAt": 0}
radar_cache_lock = RLock()
radar_cache: dict[str, Any] = {"payload": None, "ts": 0, "cacheKey": ""}
radar_analysis_cache_lock = RLock()
radar_analysis_cache: dict[str, Any] = {"payload": None, "ts": 0, "cacheKey": ""}
market_stats_cache_lock = RLock()
market_stats_cache: dict[str, Any] = {"payload": None, "ts": 0, "cacheKey": ""}
market_stats_metric_cache: dict[str, dict[str, Any]] = {}
market_ai_macro_cache_lock = RLock()
market_ai_macro_cache: dict[str, dict[str, Any]] = {}
market_ai_outlook_cache_lock = RLock()
market_ai_outlook_cache: dict[str, dict[str, Any]] = {}
chart_snapshot_cache_lock = RLock()
chart_snapshot_cache: dict[str, dict[str, Any]] = {}
us_event_refresh_lock = RLock()
us_event_cache_lock = RLock()
us_event_refresh_state_lock = RLock()
us_event_refresh_cache: dict[str, Any] = {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": US_EVENT_CACHE_SECONDS}
us_event_refreshing = False
earn_cache_lock = RLock()
earn_cache: dict[str, dict[str, Any]] = {}
announcement_cache_lock = RLock()
announcement_types_cache: dict[str, dict[str, Any]] = {}
announcements_cache: dict[str, dict[str, Any]] = {}
account_cache_lock = RLock()
account_cache_condition = Condition(account_cache_lock)
account_cache: dict[str, Any] = {
    "environment": "",
    "payload": None,
    "ts": 0,
    "refreshing": False,
    "failureCount": 0,
    "nextRetryAt": 0,
}
order_cache_lock = RLock()
order_cache: dict[tuple[str, str], dict[str, Any]] = {}
candle_refresh_lock = RLock()
candle_refreshing: set[tuple[str, str]] = set()
trading_environment_lock = RLock()
active_trading_environment = settings.default_trading_environment
automation_state_lock = RLock()
automation_state: dict[str, Any] = {
    "running": False,
    "startedAt": 0,
    "lastRunAt": 0,
    "warning": "",
}

app = FastAPI(title="OKX Perpetual Futures Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlaceSimOrderRequest(BaseModel):
    instId: str = Field(min_length=1, max_length=64)
    tdMode: str = "cross"
    side: str = Field(min_length=1, max_length=8)
    posSide: str = "net"
    ordType: str = "limit"
    sz: str = Field(min_length=1, max_length=40)
    px: Optional[str] = Field(default=None, max_length=40)
    reduceOnly: bool = False


class CancelSimOrderRequest(BaseModel):
    instId: str = Field(min_length=1, max_length=64)
    ordId: Optional[str] = Field(default=None, max_length=64)
    clOrdId: Optional[str] = Field(default=None, max_length=32)


class ClosePositionRequest(BaseModel):
    instId: str = Field(min_length=1, max_length=64)
    mgnMode: str = "cross"
    posSide: str = "net"
    ccy: Optional[str] = Field(default=None, max_length=20)
    autoCxl: bool = False


class SetLeverageRequest(BaseModel):
    instId: str = Field(min_length=1, max_length=64)
    mgnMode: str = "cross"
    lever: str = Field(min_length=1, max_length=16)
    posSide: str = "net"


class TradingEnvironmentRequest(BaseModel):
    environment: str = Field(min_length=1, max_length=16)


class AutomationStrategyRequest(BaseModel):
    name: str = Field(default="LLM BTC 5m 自动策略", min_length=1, max_length=80)
    enabled: bool = False
    instId: str = Field(default="BTC-USDT-SWAP", min_length=1, max_length=64)
    bar: str = "5m"
    template: str = "llm_direct"
    executionMode: str = "simulated_auto"
    tdMode: str = "cross"
    ordType: str = "market"
    sz: str = Field(default="1", min_length=1, max_length=40)
    fastWindow: int = Field(default=5, ge=2, le=100)
    slowWindow: int = Field(default=20, ge=3, le=300)
    maxOrderContracts: str = Field(default="1", min_length=1, max_length=40)
    maxPositionContracts: str = Field(default="5", min_length=1, max_length=40)
    cooldownSeconds: int = Field(default=300, ge=0, le=86400)
    takeProfitPct: str = Field(default="0", min_length=1, max_length=40)
    stopLossPct: str = Field(default="0", min_length=1, max_length=40)


class AutomationToggleRequest(BaseModel):
    enabled: bool


class AutomationPauseRequest(BaseModel):
    reason: str = Field(default="", max_length=200)


class AutomationArchiveRequest(BaseModel):
    reason: str = Field(default="", max_length=200)


class AutomationPreviewRequest(AutomationStrategyRequest):
    strategyId: int = Field(default=0, ge=0)


class AutomationBacktestRequest(AutomationPreviewRequest):
    limit: int = Field(default=240, ge=50, le=300)
    initialCapital: str = Field(default="10000", min_length=1, max_length=40)


class LlmConfigRequest(BaseModel):
    enabled: bool = False
    provider: str = "openai_compatible"
    baseUrl: str = Field(default="", max_length=300)
    apiKey: Optional[str] = Field(default=None, max_length=500)
    clearApiKey: bool = False
    model: str = Field(default="", max_length=120)
    temperature: float = Field(default=0.2, ge=0, le=2)
    maxTokens: int = Field(default=800, ge=128, le=4000)
    timeoutSeconds: int = Field(default=LLM_DEFAULT_TIMEOUT_SECONDS, ge=3, le=60)
    mode: str = "explain_only"
    systemPrompt: str = Field(default=DEFAULT_LLM_SYSTEM_PROMPT, max_length=4000)


class RadarScanRequest(BaseModel):
    settlement: str = "usdt"
    minVolume: str = "1000000"
    volatility: str = "all"
    risk: str = "all"
    limit: int = Field(default=RADAR_DEFAULT_LIMIT, ge=1, le=100)
    candidateLimit: int = Field(default=RADAR_CANDIDATE_LIMIT, ge=5, le=200)
    bar: str = RADAR_DEFAULT_BAR
    sortBy: str = RADAR_DEFAULT_SORT
    explain: bool = False


class RadarMarketSummary(BaseModel):
    scan: dict[str, Any]
    breadth: dict[str, Any]
    liquidity: dict[str, Any]
    volatility: dict[str, Any]
    risk: dict[str, Any]
    leaders: list[dict[str, Any]]
    topTurnover: list[dict[str, Any]]
    topVolatility: list[dict[str, Any]]
    volumeSpikes: list[dict[str, Any]]


class RadarAnalysisWatchItem(BaseModel):
    instId: str
    reason: str
    riskNote: str


class RadarMarketAnalysisResponse(BaseModel):
    marketRegime: str
    confidence: int = Field(ge=0, le=100)
    summary: str
    highlights: list[str]
    watchlist: list[RadarAnalysisWatchItem]
    riskWarnings: list[str]
    suggestedFilters: list[str]
    generatedAt: int
    source: str
    warnings: list[str]
    scanTs: int
    cacheAgeMs: Optional[int] = None
    marketSummary: RadarMarketSummary


class MarketAiOutlookRequest(BaseModel):
    instId: str = Field(default="BTC-USDT-SWAP", min_length=1, max_length=64)
    bar: str = Field(default="1m", max_length=8)
    limit: int = Field(default=MARKET_AI_CANDLE_LIMIT, ge=30, le=300)
    snapshotId: Optional[str] = Field(default=None, max_length=96)
    forceAnalysis: bool = False
    forceMacro: bool = False


async def send_ws_json(websocket: WebSocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, RuntimeError):
        return False


def realtime_capabilities(environment: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "endpoint": "/ws/realtime",
        "publicTopics": ["market.ticker", "market.candles"],
        "privateTopics": ["account", "positions", "orders"],
        "automationTopics": ["automation.status", "automation.alert", "automation.signal"],
        "environment": environment,
        "hasPrivateCredentials": settings.has_credentials_for_environment(environment),
        "requiresRestSnapshot": True,
        "restFirstTopics": ["leverage", "announcements", "earn", "settings", "historical-orders", "signal-logs"],
    }


def broadcast_realtime_event(event: dict[str, Any], topic: str | None = None) -> None:
    payload = dict(event)
    payload.setdefault("ts", now_ms())
    realtime_hub.broadcast_threadsafe(payload, topic=topic)


def normalize_trading_environment(environment: str) -> str:
    value = environment.strip().lower()
    if value not in TRADING_ENVIRONMENTS:
        raise HTTPException(status_code=400, detail="交易环境仅支持 simulated 或 live。")
    return value


def environment_label(environment: str) -> str:
    return "虚拟盘" if environment == "simulated" else "真实盘"


def current_trading_environment() -> str:
    with trading_environment_lock:
        return active_trading_environment


def active_settings() -> Settings:
    return settings.for_environment(current_trading_environment())


def client_for_environment(environment: str) -> OkxClient:
    return OkxClient(settings.for_environment(environment))


def can_trade(environment: str) -> bool:
    if not settings.has_credentials_for_environment(environment):
        return False
    if environment == "simulated":
        return True
    return settings.live_trading_enabled


def require_trading_enabled(environment: str) -> None:
    if not settings.has_credentials_for_environment(environment):
        raise HTTPException(status_code=400, detail=f"{environment_label(environment)} API Key 未配置。")
    if environment == "live" and not settings.live_trading_enabled:
        raise HTTPException(status_code=403, detail="实盘交易未开启。请设置 OKX_ENABLE_LIVE_TRADING=1 后重启后端。")


def set_current_trading_environment(environment: str, persist: bool = True) -> str:
    normalized = normalize_trading_environment(environment)
    global active_trading_environment
    with trading_environment_lock:
        active_trading_environment = normalized
    reset_account_cache()
    if persist:
        database.set_app_setting("trading_environment", normalized, now_ms())
        broadcast_realtime_event(
            {
                "type": "stale",
                "topic": "account",
                "environment": normalized,
                "source": "settings",
                "refreshRequired": True,
                "message": "交易环境已切换，请刷新账户、持仓和订单快照。",
            },
            topic="account",
        )
        broadcast_realtime_event(
            {
                "type": "stale",
                "topic": "orders",
                "environment": normalized,
                "source": "settings",
                "refreshRequired": True,
                "message": "交易环境已切换，请刷新订单快照。",
            },
            topic="orders",
        )
    return normalized


def load_persisted_trading_environment() -> None:
    persisted = database.get_app_setting("trading_environment")
    set_current_trading_environment(persisted or settings.default_trading_environment, persist=False)


def decimal_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"{field_name}不能为空")
    try:
        numeric = Decimal(text)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail=f"{field_name}必须是数字") from exc
    if numeric <= 0:
        raise HTTPException(status_code=400, detail=f"{field_name}必须大于 0")
    return text


def automation_percent_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    try:
        numeric = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"{field_name}必须是数字") from exc
    if numeric < 0:
        raise HTTPException(status_code=400, detail=f"{field_name}不能小于 0")
    if numeric > Decimal("1000"):
        raise HTTPException(status_code=400, detail=f"{field_name}不能超过 1000%")
    return decimal_display(numeric)


def client_order_id() -> str:
    return f"OKXQ{uuid.uuid4().hex[:28].upper()}"


def build_place_order_payload(order: PlaceSimOrderRequest) -> dict[str, Any]:
    inst_id = order.instId.strip().upper()
    if not inst_id.endswith("-SWAP"):
        raise HTTPException(status_code=400, detail="手动交易当前只支持 OKX 永续合约 SWAP。")

    td_mode = order.tdMode.strip().lower()
    if td_mode not in TRADE_MODES:
        raise HTTPException(status_code=400, detail="交易模式仅支持 cross 或 isolated。")

    side = order.side.strip().lower()
    if side not in ORDER_SIDES:
        raise HTTPException(status_code=400, detail="买卖方向仅支持 buy 或 sell。")

    pos_side = order.posSide.strip().lower() or "net"
    if pos_side not in POSITION_SIDES:
        raise HTTPException(status_code=400, detail="持仓方向仅支持 net、long 或 short。")

    ord_type = order.ordType.strip().lower()
    if ord_type not in ORDER_TYPES:
        raise HTTPException(status_code=400, detail="订单类型不受支持。")

    payload: dict[str, Any] = {
        "instId": inst_id,
        "tdMode": td_mode,
        "side": side,
        "ordType": ord_type,
        "sz": decimal_text(order.sz, "下单数量"),
        "clOrdId": client_order_id(),
        "tag": ORDER_TAG,
    }

    if pos_side != "net":
        payload["posSide"] = pos_side
    if ord_type in ORDER_TYPES_WITH_PRICE:
        payload["px"] = decimal_text(order.px, "委托价格")
    if order.reduceOnly:
        payload["reduceOnly"] = True

    return payload


def build_close_position_payload(order: ClosePositionRequest) -> dict[str, Any]:
    inst_id = order.instId.strip().upper()
    if not inst_id.endswith("-SWAP"):
        raise HTTPException(status_code=400, detail="平仓当前只支持 OKX 永续合约 SWAP。")

    margin_mode = order.mgnMode.strip().lower()
    if margin_mode not in TRADE_MODES:
        raise HTTPException(status_code=400, detail="平仓保证金模式仅支持 cross 或 isolated。")

    pos_side = order.posSide.strip().lower() or "net"
    if pos_side not in POSITION_SIDES:
        raise HTTPException(status_code=400, detail="平仓持仓方向仅支持 net、long 或 short。")

    payload: dict[str, Any] = {
        "instId": inst_id,
        "mgnMode": margin_mode,
        "autoCxl": order.autoCxl,
        "clOrdId": client_order_id(),
        "tag": ORDER_TAG,
    }
    if pos_side != "net":
        payload["posSide"] = pos_side
    if order.ccy:
        payload["ccy"] = order.ccy.strip().upper()
    return payload


def build_set_leverage_payload(order: SetLeverageRequest) -> dict[str, Any]:
    inst_id = order.instId.strip().upper()
    if not inst_id.endswith("-SWAP"):
        raise HTTPException(status_code=400, detail="杠杆设置当前只支持 OKX 永续合约 SWAP。")

    margin_mode = order.mgnMode.strip().lower()
    if margin_mode not in TRADE_MODES:
        raise HTTPException(status_code=400, detail="杠杆设置保证金模式仅支持 cross 或 isolated。")

    pos_side = order.posSide.strip().lower() or "net"
    if pos_side not in POSITION_SIDES:
        raise HTTPException(status_code=400, detail="杠杆设置持仓方向仅支持 net、long 或 short。")

    payload: dict[str, Any] = {
        "instId": inst_id,
        "mgnMode": margin_mode,
        "lever": decimal_text(order.lever, "杠杆倍数"),
    }
    if margin_mode == "isolated" and pos_side != "net":
        payload["posSide"] = pos_side
    return payload


def first_response_item(response: dict[str, Any]) -> dict[str, Any]:
    rows = response.get("data")
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return {}


def sim_order_event(
    environment: str,
    action: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
    state: str,
) -> dict[str, Any]:
    row = first_response_item(response_payload)
    code = str(row.get("sCode") or response_payload.get("code") or "")
    message = str(row.get("sMsg") or response_payload.get("msg") or "")
    event = {
        "environment": environment,
        "ts": now_ms(),
        "action": action,
        "inst_id": str(request_payload.get("instId", "")).upper(),
        "td_mode": request_payload.get("tdMode"),
        "side": request_payload.get("side"),
        "pos_side": request_payload.get("posSide", "net"),
        "ord_type": request_payload.get("ordType"),
        "px": request_payload.get("px"),
        "sz": request_payload.get("sz"),
        "reduce_only": bool(request_payload.get("reduceOnly")),
        "cl_ord_id": row.get("clOrdId") or request_payload.get("clOrdId"),
        "ord_id": row.get("ordId") or request_payload.get("ordId"),
        "state": state,
        "code": code,
        "message": message,
        "request_json": json.dumps(request_payload, ensure_ascii=False, separators=(",", ":")),
        "response_json": json.dumps(response_payload, ensure_ascii=False, separators=(",", ":")),
    }
    database.insert_sim_order_event(event)
    broadcast_realtime_event(
        {
            "type": "order.update",
            "topic": "orders",
            "environment": environment,
            "data": event,
            "source": "local-order-record",
            "refreshRequired": True,
        },
        topic="orders",
    )
    return event


def record_private_order_update(environment: str, order_row: dict[str, Any], raw_payload: dict[str, Any]) -> dict[str, Any]:
    state = str(order_row.get("state") or "updated")
    request_payload = {
        "instId": order_row.get("instId") or "",
        "tdMode": order_row.get("tdMode"),
        "side": order_row.get("side"),
        "posSide": order_row.get("posSide"),
        "ordType": order_row.get("ordType"),
        "px": order_row.get("px"),
        "sz": order_row.get("sz"),
        "reduceOnly": order_row.get("reduceOnly"),
        "clOrdId": order_row.get("clOrdId"),
        "ordId": order_row.get("ordId"),
    }
    response_payload = {"code": "0", "msg": "", "data": [order_row], "raw": raw_payload}
    row = first_response_item(response_payload)
    event = {
        "environment": environment,
        "ts": now_ms(),
        "action": "ws-order",
        "inst_id": str(order_row.get("instId") or "").upper(),
        "td_mode": order_row.get("tdMode"),
        "side": order_row.get("side"),
        "pos_side": order_row.get("posSide", "net"),
        "ord_type": order_row.get("ordType"),
        "px": order_row.get("px"),
        "sz": order_row.get("sz"),
        "reduce_only": bool(order_row.get("reduceOnly")),
        "cl_ord_id": row.get("clOrdId") or order_row.get("clOrdId"),
        "ord_id": row.get("ordId") or order_row.get("ordId"),
        "state": state,
        "code": "0",
        "message": str(order_row.get("msg") or order_row.get("sMsg") or ""),
        "request_json": json.dumps(request_payload, ensure_ascii=False, separators=(",", ":")),
        "response_json": json.dumps(response_payload, ensure_ascii=False, separators=(",", ":")),
    }
    database.insert_sim_order_event(event)
    invalidate_order_cache(environment, event["inst_id"])
    return event


def success_code(event: dict[str, Any]) -> bool:
    return event.get("code") in {"", "0"}


def response_successful(response: dict[str, Any]) -> bool:
    row = first_response_item(response)
    code = str(row.get("sCode") or response.get("code") or "")
    return code in {"", "0"}


def order_error_detail(event: dict[str, Any], fallback: str) -> str:
    code = str(event.get("code") or "").strip()
    message = str(event.get("message") or "").strip()
    if code == "50123":
        return "API Key 没有该品种交易权限。请在 OKX 后台重新创建或编辑模拟盘 API Key，勾选交易权限，并确认该合约在模拟盘账户可交易范围内。（OKX 50123）"
    if code == "51008":
        return "保证金不足，当前模拟盘可用权益不足以提交该订单。请减小张数、换低面值合约，或在 OKX 模拟盘补充资金/调整杠杆后重试。（OKX 51008）"
    if code == "51001":
        return "该合约不在当前 OKX 交易账户可下单范围内。请换用账户支持的合约，或刷新账户可交易合约列表后重试。（OKX 51001）"
    if code == "51000" and "posSide" in message:
        return "账户持仓模式与下单方向不匹配，系统已尝试兼容单向持仓模式后仍被 OKX 拒绝。（OKX 51000）"
    if code and message:
        return f"{message}（OKX {code}）"
    return message or fallback


def decimal_value(value: str | None, field_name: str) -> Decimal:
    return Decimal(decimal_text(value, field_name))


def decimal_display(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return "0" if text == "-0" else text


def decimal_display_fixed(value: Decimal | str | int | float | None, places: int = 2) -> str:
    numeric = safe_decimal(value)
    if numeric is None:
        return "0"
    quant = Decimal("1") if places <= 0 else Decimal("1").scaleb(-places)
    return decimal_display(numeric.quantize(quant))


def normalize_automation_strategy(payload: AutomationStrategyRequest, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    inst_id = payload.instId.strip().upper()
    if not inst_id.endswith("-SWAP"):
        raise HTTPException(status_code=400, detail="自动交易第一版只支持 OKX 永续合约 SWAP。")

    bar = payload.bar.strip()
    if bar not in SUPPORTED_BARS:
        raise HTTPException(status_code=400, detail="策略周期不受支持。")

    template = payload.template.strip().lower()
    if template not in AUTOMATION_TEMPLATES:
        raise HTTPException(status_code=400, detail="策略模板不受支持。")

    execution_mode = payload.executionMode.strip().lower()
    if execution_mode not in AUTOMATION_EXECUTION_MODES:
        raise HTTPException(status_code=400, detail="执行模式仅支持 signal_only 或 simulated_auto。")

    td_mode = payload.tdMode.strip().lower()
    if td_mode not in TRADE_MODES:
        raise HTTPException(status_code=400, detail="保证金模式仅支持 cross 或 isolated。")

    ord_type = payload.ordType.strip().lower()
    if ord_type not in {"market", "limit"}:
        raise HTTPException(status_code=400, detail="自动交易第一版只支持市价或限价。")

    if payload.fastWindow >= payload.slowWindow:
        raise HTTPException(status_code=400, detail="快线周期必须小于慢线周期。")

    sz = decimal_text(payload.sz, "策略下单张数")
    max_order_contracts = decimal_text(payload.maxOrderContracts, "单笔最大张数")
    max_position_contracts = decimal_text(payload.maxPositionContracts, "单合约最大持仓")
    take_profit_pct = automation_percent_text(payload.takeProfitPct, "止盈幅度")
    stop_loss_pct = automation_percent_text(payload.stopLossPct, "止损幅度")
    if Decimal(sz) > Decimal(max_order_contracts):
        raise HTTPException(status_code=400, detail="策略下单张数不能超过单笔最大张数。")

    now = now_ms()
    return {
        "name": payload.name.strip(),
        "enabled": payload.enabled,
        "archived": bool(existing.get("archived")) if existing else False,
        "archived_at": existing.get("archived_at") if existing else None,
        "archived_reason": str(existing.get("archived_reason") or "") if existing else "",
        "inst_id": inst_id,
        "bar": bar,
        "template": template,
        "execution_mode": execution_mode,
        "td_mode": td_mode,
        "ord_type": ord_type,
        "sz": sz,
        "fast_window": payload.fastWindow,
        "slow_window": payload.slowWindow,
        "max_order_contracts": max_order_contracts,
        "max_position_contracts": max_position_contracts,
        "cooldown_seconds": payload.cooldownSeconds,
        "take_profit_pct": take_profit_pct,
        "stop_loss_pct": stop_loss_pct,
        "last_eval_ts": existing.get("last_eval_ts") if existing else None,
        "created_at": int(existing.get("created_at") or now) if existing else now,
        "updated_at": now,
    }


def strategy_response(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    result["enabled"] = bool(result.get("enabled"))
    result["archived"] = bool(result.get("archived"))
    return result


def ensure_single_enabled_strategy(strategy: dict[str, Any], strategy_id: int = 0) -> None:
    if not bool(strategy.get("enabled")):
        return
    if bool(strategy.get("archived")):
        raise HTTPException(status_code=400, detail="已归档策略请先恢复后再启动。")
    inst_id = str(strategy.get("inst_id") or "").upper()
    for row in list_automation_strategies_safe(include_archived=True):
        if int(row.get("id") or 0) == strategy_id:
            continue
        if bool(row.get("enabled")) and not bool(row.get("archived")) and str(row.get("inst_id") or "").upper() == inst_id:
            raise HTTPException(status_code=400, detail=f"{inst_id} 已有启用中的自动策略，请先暂停另一条策略。")


def ensure_strategy_enable_preconditions(strategy: dict[str, Any], strategy_id: int = 0) -> None:
    if not bool(strategy.get("enabled")):
        return
    ensure_single_enabled_strategy(strategy, strategy_id)
    if str(strategy.get("template") or "") != "llm_direct":
        return

    config = stored_llm_config()
    if not config.get("enabled"):
        raise HTTPException(status_code=400, detail="LLM 判断策略启用前，请先在 AI 配置中启用 LLM 信号分析。")
    if not config.get("baseUrl") or not config.get("model") or not config.get("apiKey"):
        raise HTTPException(status_code=400, detail="LLM 判断策略启用前，请先补全 Base URL、模型名称和 API Key。")


def normalized_strategy_from_preview_payload(payload: AutomationPreviewRequest) -> dict[str, Any]:
    existing = database.get_automation_strategy(payload.strategyId) if payload.strategyId else None
    if payload.strategyId and not existing:
        raise HTTPException(status_code=404, detail="策略不存在。")
    strategy = normalize_automation_strategy(payload, existing)
    if payload.strategyId:
        strategy["id"] = payload.strategyId
    return strategy


def default_automation_global_state() -> dict[str, Any]:
    return {
        "globalPaused": False,
        "pauseReason": "",
        "pauseStartedAt": 0,
        "pausedBy": "",
        "circuitBreakerActive": False,
        "circuitReason": "",
        "circuitTriggeredAt": 0,
        "resumedAt": 0,
        "updatedAt": 0,
    }


def automation_global_state() -> dict[str, Any]:
    state = default_automation_global_state()
    if not hasattr(database, "get_app_setting"):
        return state
    try:
        raw = database.get_app_setting(AUTOMATION_GLOBAL_STATE_KEY)
    except Exception:
        return state
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            state.update(payload)
    state["globalPaused"] = bool(state.get("globalPaused"))
    state["pauseReason"] = str(state.get("pauseReason") or "")
    state["pauseStartedAt"] = int(state.get("pauseStartedAt") or 0)
    state["pausedBy"] = str(state.get("pausedBy") or "")
    state["circuitBreakerActive"] = bool(state.get("circuitBreakerActive"))
    state["circuitReason"] = str(state.get("circuitReason") or "")
    state["circuitTriggeredAt"] = int(state.get("circuitTriggeredAt") or 0)
    state["resumedAt"] = int(state.get("resumedAt") or 0)
    state["updatedAt"] = int(state.get("updatedAt") or 0)
    return state


def persist_automation_global_state(state: dict[str, Any]) -> dict[str, Any]:
    payload = default_automation_global_state()
    payload.update(state)
    payload["globalPaused"] = bool(payload.get("globalPaused"))
    payload["pauseReason"] = str(payload.get("pauseReason") or "")
    payload["pauseStartedAt"] = int(payload.get("pauseStartedAt") or 0)
    payload["pausedBy"] = str(payload.get("pausedBy") or "")
    payload["circuitBreakerActive"] = bool(payload.get("circuitBreakerActive"))
    payload["circuitReason"] = str(payload.get("circuitReason") or "")
    payload["circuitTriggeredAt"] = int(payload.get("circuitTriggeredAt") or 0)
    payload["resumedAt"] = int(payload.get("resumedAt") or 0)
    payload["updatedAt"] = now_ms()
    if hasattr(database, "set_app_setting"):
        database.set_app_setting(AUTOMATION_GLOBAL_STATE_KEY, json.dumps(payload, ensure_ascii=False, separators=(",", ":")), int(payload["updatedAt"]))
    broadcast_realtime_event(
        {
            "type": "automation.status",
            "topic": "automation.status",
            "source": "automation",
            "data": payload,
            "refreshRequired": True,
        },
        topic="automation.status",
    )
    return payload


def automation_global_block_check(strategy: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any] | None:
    state = automation_global_state()
    if state.get("globalPaused"):
        return {
            "key": "global_pause",
            "label": "全局暂停",
            "status": "block",
            "message": state.get("pauseReason") or "自动交易当前处于全局暂停状态，已停止自动执行。",
            "value": "已暂停",
        }
    if state.get("circuitBreakerActive"):
        return {
            "key": "circuit_breaker",
            "label": "熔断状态",
            "status": "block",
            "message": state.get("circuitReason") or "自动交易已触发熔断，需人工恢复后才会继续执行。",
            "value": "已熔断",
        }
    return None


def list_automation_strategies_safe(include_archived: bool = False) -> list[dict[str, Any]]:
    try:
        rows = database.list_automation_strategies(include_archived=include_archived)
    except TypeError:
        rows = database.list_automation_strategies()
    if include_archived:
        return list(rows)
    return [row for row in rows if not bool(row.get("archived"))]


def list_automation_alerts_safe(
    active_only: bool = False,
    severity: str = "",
    source: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not hasattr(database, "list_automation_alerts"):
        return []
    try:
        return list(database.list_automation_alerts(active_only=active_only, severity=severity, source=source, limit=limit))
    except TypeError:
        return list(database.list_automation_alerts())


def count_automation_alerts_safe(active_only: bool = False, severity: str = "", source: str = "") -> int:
    if not hasattr(database, "count_automation_alerts"):
        return 0
    try:
        return int(database.count_automation_alerts(active_only=active_only, severity=severity, source=source))
    except TypeError:
        return len(list_automation_alerts_safe(active_only=active_only, severity=severity, source=source, limit=1000))


def automation_alert_payload(
    severity: str,
    source: str,
    message: str,
    strategy_id: int | None = None,
    signal_id: int | None = None,
    order_event_id: int | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ts": now_ms(),
        "severity": severity,
        "source": source,
        "message": message,
        "strategy_id": strategy_id,
        "signal_id": signal_id,
        "order_event_id": order_event_id,
        "acknowledged_at": None,
        "raw_json": json.dumps(raw_payload or {}, ensure_ascii=False, separators=(",", ":")),
    }


def find_active_automation_alert(
    severity: str,
    source: str,
    message: str,
    strategy_id: int | None = None,
    signal_id: int | None = None,
    order_event_id: int | None = None,
) -> dict[str, Any] | None:
    for alert in list_automation_alerts_safe(active_only=True, severity=severity, source=source, limit=200):
        if str(alert.get("message") or "") != message:
            continue
        if strategy_id is not None and int(alert.get("strategy_id") or 0) != int(strategy_id):
            continue
        if signal_id is not None and int(alert.get("signal_id") or 0) != int(signal_id):
            continue
        if order_event_id is not None and int(alert.get("order_event_id") or 0) != int(order_event_id):
            continue
        return alert
    return None


def create_automation_alert(
    severity: str,
    source: str,
    message: str,
    strategy_id: int | None = None,
    signal_id: int | None = None,
    order_event_id: int | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not hasattr(database, "insert_automation_alert"):
        return None
    existing = find_active_automation_alert(severity, source, message, strategy_id, signal_id, order_event_id)
    if existing:
        return existing
    row = database.insert_automation_alert(
        automation_alert_payload(
            severity=severity,
            source=source,
            message=message,
            strategy_id=strategy_id,
            signal_id=signal_id,
            order_event_id=order_event_id,
            raw_payload=raw_payload,
        )
    )
    if row:
        broadcast_realtime_event(
            {
                "type": "automation.alert",
                "topic": "automation.alert",
                "source": "automation",
                "data": dict(row),
                "refreshRequired": True,
            },
            topic="automation.alert",
        )
    return row


def trigger_automation_circuit_breaker(reason: str, strategy_id: int | None = None, signal_id: int | None = None) -> dict[str, Any]:
    now = now_ms()
    updated = persist_automation_global_state(
        {
            **automation_global_state(),
            "globalPaused": False,
            "pauseReason": "",
            "pauseStartedAt": 0,
            "pausedBy": "",
            "circuitBreakerActive": True,
            "circuitReason": reason,
            "circuitTriggeredAt": now,
            "updatedAt": now,
        }
    )
    create_automation_alert(
        "critical",
        "circuit_breaker",
        reason or "自动交易已触发熔断。",
        strategy_id=strategy_id,
        signal_id=signal_id,
        raw_payload={"state": updated, "reason": reason, "action": "circuit_breaker"},
    )
    return updated


def attach_automation_audit_records(signal_row: dict[str, Any], raw_payload: dict[str, Any] | None = None) -> None:
    if not raw_payload:
        return
    raw_snapshot = raw_payload.get("risk_snapshot")
    if isinstance(raw_snapshot, dict) and hasattr(database, "insert_automation_risk_snapshot"):
        snapshot_payload = dict(raw_snapshot)
        snapshot_payload.setdefault("signal_id", signal_row.get("id"))
        snapshot_payload.setdefault("strategy_id", signal_row.get("strategy_id"))
        snapshot_payload.setdefault("ts", signal_row.get("ts") or now_ms())
        snapshot_payload.setdefault("allowed", bool(snapshot_payload.get("allowed")))
        snapshot_payload.setdefault("severity", "warning" if snapshot_payload.get("allowed") else "blocked")
        snapshot_payload.setdefault("message", signal_row.get("message") or signal_row.get("reason") or "")
        snapshot_payload.setdefault("checks_json", json.dumps(snapshot_payload.get("checks", []), ensure_ascii=False, separators=(",", ":")))
        snapshot_payload.setdefault("raw_json", json.dumps(raw_payload, ensure_ascii=False, separators=(",", ":")))
        database.insert_automation_risk_snapshot(snapshot_payload)

    execution_steps = raw_payload.get("execution_steps")
    if isinstance(execution_steps, list) and hasattr(database, "insert_automation_execution_step"):
        for index, step in enumerate(execution_steps):
            if not isinstance(step, dict):
                continue
            database.insert_automation_execution_step(
                {
                    "signal_id": signal_row.get("id"),
                    "strategy_id": signal_row.get("strategy_id"),
                    "step_order": step.get("step_order", index),
                    "ts": step.get("ts") or signal_row.get("ts") or now_ms(),
                    "action": str(step.get("action") or "step"),
                    "status": str(step.get("status") or "ok"),
                    "message": str(step.get("message") or ""),
                    "request_json": step.get("request_json")
                    or json.dumps(step.get("request") or {}, ensure_ascii=False, separators=(",", ":")),
                    "response_json": step.get("response_json")
                    or json.dumps(step.get("result") or {}, ensure_ascii=False, separators=(",", ":")),
                }
            )


def automation_alert_from_record(
    strategy: dict[str, Any],
    signal: dict[str, Any],
    decision: str,
    message: str,
    raw_payload: dict[str, Any] | None = None,
) -> tuple[str, str, str] | None:
    if decision == "llm_failed":
        return ("warning", "llm_failure", message or signal.get("reason") or "LLM 判断失败。")
    if decision == "failed":
        return ("critical", "execution_error", message or signal.get("reason") or "自动交易执行失败。")
    snapshot = raw_payload.get("risk_snapshot") if isinstance(raw_payload, dict) else None
    if not isinstance(snapshot, dict):
        return None
    checks = snapshot.get("checks") if isinstance(snapshot.get("checks"), list) else []
    for item in checks:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "")
        if key == "circuit_breaker" and item.get("status") == "block":
            return ("critical", "circuit_breaker", str(item.get("message") or message or "自动交易已触发熔断。"))
        if key == "global_pause" and item.get("status") == "block":
            return ("warning", "global_pause", str(item.get("message") or message or "自动交易当前处于全局暂停状态。"))
    if decision == "blocked":
        return ("warning", "risk_block", message or snapshot.get("message") or "自动交易被风控拦截。")
    return None


def automation_status_payload() -> dict[str, Any]:
    strategies = list_automation_strategies_safe(include_archived=True)
    active_strategies = [item for item in strategies if not bool(item.get("archived"))]
    with automation_state_lock:
        state = dict(automation_state)
    global_state = automation_global_state()
    return {
        "running": bool(state.get("running")),
        "startedAt": state.get("startedAt") or 0,
        "lastRunAt": state.get("lastRunAt") or 0,
        "warning": state.get("warning") or "",
        "intervalSeconds": AUTOMATION_INTERVAL_SECONDS,
        "strategyCount": len(active_strategies),
        "archivedCount": len(strategies) - len(active_strategies),
        "enabledCount": sum(1 for item in active_strategies if bool(item.get("enabled"))),
        "globalPaused": bool(global_state.get("globalPaused")),
        "pauseReason": global_state.get("pauseReason") or "",
        "pauseStartedAt": global_state.get("pauseStartedAt") or 0,
        "circuitBreakerActive": bool(global_state.get("circuitBreakerActive")),
        "circuitReason": global_state.get("circuitReason") or "",
        "circuitTriggeredAt": global_state.get("circuitTriggeredAt") or 0,
        "globalStateUpdatedAt": global_state.get("updatedAt") or 0,
        "alertCount": count_automation_alerts_safe(active_only=True),
        "criticalAlertCount": count_automation_alerts_safe(active_only=True, severity="critical"),
        "supportedModes": ["signal_only", "simulated_auto"],
        "supportedTemplates": ["ma_cross", "llm_direct"],
        "llmMinConfidence": AUTOMATION_LLM_MIN_CONFIDENCE,
        "llmLookbackCandles": AUTOMATION_LLM_LOOKBACK_CANDLES,
        "llmPromptCandles": AUTOMATION_LLM_PROMPT_CANDLES,
    }


def default_llm_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "provider": "openai_compatible",
        "baseUrl": "",
        "apiKey": "",
        "model": "",
        "temperature": 0.2,
        "maxTokens": 800,
        "timeoutSeconds": LLM_DEFAULT_TIMEOUT_SECONDS,
        "mode": "direct_signal",
        "systemPrompt": DEFAULT_LLM_SYSTEM_PROMPT,
        "updatedAt": 0,
    }


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}****{value[-4:]}"


def coerce_float(value: Any, fallback: float, minimum: float, maximum: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    return min(max(numeric, minimum), maximum)


def coerce_int(value: Any, fallback: int, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return fallback
    return min(max(numeric, minimum), maximum)


def stored_llm_config() -> dict[str, Any]:
    config = default_llm_config()
    if not hasattr(database, "get_app_setting"):
        return config
    try:
        raw = database.get_app_setting(LLM_CONFIG_KEY)
    except Exception:
        return config
    if raw:
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                config.update(payload)
        except json.JSONDecodeError:
            pass

    provider = str(config.get("provider") or "openai_compatible").strip().lower()
    config["provider"] = provider if provider in LLM_PROVIDERS else "openai_compatible"
    mode = str(config.get("mode") or "direct_signal").strip().lower()
    config["mode"] = mode if mode in LLM_MODES else "direct_signal"
    config["enabled"] = bool(config.get("enabled"))
    config["baseUrl"] = str(config.get("baseUrl") or "").strip()
    config["apiKey"] = str(config.get("apiKey") or "")
    config["model"] = str(config.get("model") or "").strip()
    config["temperature"] = coerce_float(config.get("temperature"), 0.2, 0, 2)
    config["maxTokens"] = coerce_int(config.get("maxTokens"), 800, 128, 4000)
    config["timeoutSeconds"] = coerce_int(config.get("timeoutSeconds"), LLM_DEFAULT_TIMEOUT_SECONDS, 3, 60)
    system_prompt = str(config.get("systemPrompt") or DEFAULT_LLM_SYSTEM_PROMPT).strip() or DEFAULT_LLM_SYSTEM_PROMPT
    if system_prompt == LEGACY_LLM_SYSTEM_PROMPT:
        system_prompt = DEFAULT_LLM_SYSTEM_PROMPT
        if config["mode"] == "explain_only":
            config["mode"] = "direct_signal"
    config["systemPrompt"] = system_prompt
    config["updatedAt"] = coerce_int(config.get("updatedAt"), 0, 0, 9_999_999_999_999)
    return config


def sanitize_llm_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "enabled": bool(config.get("enabled")),
        "provider": config.get("provider") or "openai_compatible",
        "baseUrl": config.get("baseUrl") or "",
        "apiKeyConfigured": bool(config.get("apiKey")),
        "apiKeyMasked": mask_secret(str(config.get("apiKey") or "")),
        "model": config.get("model") or "",
        "temperature": config.get("temperature"),
        "maxTokens": config.get("maxTokens"),
        "timeoutSeconds": config.get("timeoutSeconds"),
        "effectiveTimeoutSeconds": llm_request_timeout_seconds(config),
        "mode": config.get("mode") or "explain_only",
        "systemPrompt": config.get("systemPrompt") or DEFAULT_LLM_SYSTEM_PROMPT,
        "updatedAt": config.get("updatedAt") or 0,
    }


def normalize_llm_config(payload: LlmConfigRequest, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    provider = payload.provider.strip().lower()
    if provider not in LLM_PROVIDERS:
        raise HTTPException(status_code=400, detail="LLM 服务商类型不受支持。")
    mode = payload.mode.strip().lower()
    if mode not in LLM_MODES:
        raise HTTPException(status_code=400, detail="LLM 分析模式不受支持。")

    existing = existing or default_llm_config()
    api_key = "" if payload.clearApiKey else str(existing.get("apiKey") or "")
    if payload.apiKey is not None and payload.apiKey.strip():
        api_key = payload.apiKey.strip()

    base_url = payload.baseUrl.strip().rstrip("/")
    model = payload.model.strip()
    if payload.enabled:
        if not base_url:
            raise HTTPException(status_code=400, detail="启用 LLM 前必须填写 Base URL。")
        if not model:
            raise HTTPException(status_code=400, detail="启用 LLM 前必须填写模型名称。")
        if not api_key:
            raise HTTPException(status_code=400, detail="启用 LLM 前必须填写 API Key。")

    return {
        "enabled": payload.enabled,
        "provider": provider,
        "baseUrl": base_url,
        "apiKey": api_key,
        "model": model,
        "temperature": payload.temperature,
        "maxTokens": payload.maxTokens,
        "timeoutSeconds": payload.timeoutSeconds,
        "mode": mode,
        "systemPrompt": payload.systemPrompt.strip() or DEFAULT_LLM_SYSTEM_PROMPT,
        "updatedAt": now_ms(),
    }


def llm_completion_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if value.endswith("/chat/completions"):
        return value
    return f"{value}/chat/completions"


def is_deepseek_llm_config(config: dict[str, Any]) -> bool:
    base_url = str(config.get("baseUrl") or "").strip().lower()
    model = str(config.get("model") or "").strip().lower()
    return "api.deepseek.com" in base_url or model.startswith("deepseek-")


def llm_request_timeout_seconds(config: dict[str, Any]) -> int:
    configured_timeout = coerce_int(config.get("timeoutSeconds"), LLM_DEFAULT_TIMEOUT_SECONDS, 3, 60)
    if str(config.get("mode") or "") == "direct_signal" or is_deepseek_llm_config(config):
        return max(configured_timeout, LLM_DIRECT_MIN_TIMEOUT_SECONDS)
    return configured_timeout


class LlmCompletionError(ValueError):
    def __init__(self, message: str, usage_log: dict[str, Any] | None = None):
        super().__init__(message)
        self.usage_log = usage_log


def usage_int(payload: dict[str, Any], *keys: str) -> int:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return 0
        current = current.get(key)
    return coerce_int(current, 0, 0, 99_999_999)


def normalize_llm_usage(payload: dict[str, Any]) -> dict[str, int]:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    prompt_details = usage.get("prompt_tokens_details") if isinstance(usage.get("prompt_tokens_details"), dict) else {}
    completion_details = usage.get("completion_tokens_details") if isinstance(usage.get("completion_tokens_details"), dict) else {}
    return {
        "prompt_tokens": usage_int(usage, "prompt_tokens"),
        "completion_tokens": usage_int(usage, "completion_tokens"),
        "total_tokens": usage_int(usage, "total_tokens"),
        "cached_tokens": usage_int(prompt_details, "cached_tokens"),
        "reasoning_tokens": usage_int(completion_details, "reasoning_tokens"),
        "cache_hit_tokens": usage_int(usage, "prompt_cache_hit_tokens"),
        "cache_miss_tokens": usage_int(usage, "prompt_cache_miss_tokens"),
    }


def llm_usage_log_view(log: dict[str, Any] | None) -> dict[str, Any] | None:
    if not log:
        return None
    return {
        "id": log.get("id"),
        "request_id": log.get("request_id"),
        "prompt_tokens": log.get("prompt_tokens") or 0,
        "completion_tokens": log.get("completion_tokens") or 0,
        "total_tokens": log.get("total_tokens") or 0,
        "cached_tokens": log.get("cached_tokens") or 0,
        "reasoning_tokens": log.get("reasoning_tokens") or 0,
        "cache_hit_tokens": log.get("cache_hit_tokens") or 0,
        "cache_miss_tokens": log.get("cache_miss_tokens") or 0,
        "duration_ms": log.get("duration_ms") or 0,
        "finish_reason": log.get("finish_reason") or "",
    }


def record_llm_usage_log(
    config: dict[str, Any],
    request_id: str,
    request_type: str,
    status: str,
    usage: dict[str, int],
    duration_ms: int,
    timeout_seconds: int,
    finish_reason: str = "",
    error: str = "",
    context: dict[str, Any] | None = None,
    raw_usage: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    context = context or {}
    analysis_profile = context.get("analysis_profile") if isinstance(context.get("analysis_profile"), dict) else {}
    try:
        return database.insert_llm_usage_log(
            {
                "request_id": request_id,
                "ts": now_ms(),
                "provider": config.get("provider"),
                "model": config.get("model"),
                "mode": config.get("mode"),
                "request_type": request_type,
                "status": status,
                "strategy_id": context.get("strategy_id"),
                "signal_id": context.get("signal_id"),
                "inst_id": context.get("inst_id"),
                "bar": context.get("bar"),
                "profile_id": analysis_profile.get("id"),
                "profile_version": analysis_profile.get("profileVersion"),
                "profile_hash": analysis_profile.get("contentHash"),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cached_tokens": usage.get("cached_tokens", 0),
                "reasoning_tokens": usage.get("reasoning_tokens", 0),
                "cache_hit_tokens": usage.get("cache_hit_tokens", 0),
                "cache_miss_tokens": usage.get("cache_miss_tokens", 0),
                "duration_ms": duration_ms,
                "timeout_seconds": timeout_seconds,
                "finish_reason": finish_reason[:120] if finish_reason else "",
                "error": error[:1200] if error else "",
                "raw_usage_json": json.dumps(raw_usage or {}, ensure_ascii=False, separators=(",", ":")),
            }
        )
    except Exception:
        return None


def extract_balanced_json_object_text(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("LLM 未返回 JSON 对象。")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError("LLM JSON 对象不完整。")


def extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(extract_balanced_json_object_text(text))
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 返回格式不稳定，无法解析为 JSON。") from exc
    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON 结果必须是对象。")
    return parsed


def llm_chat_completion(
    config: dict[str, Any],
    messages: list[dict[str, str]],
    request_type: str = "unknown",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not config.get("baseUrl") or not config.get("model") or not config.get("apiKey"):
        raise ValueError("LLM 配置不完整。")
    body = {
        "model": config["model"],
        "messages": messages,
        "temperature": config["temperature"],
        "max_tokens": config["maxTokens"],
    }
    if is_deepseek_llm_config(config):
        body["response_format"] = {"type": "json_object"}
        body["thinking"] = {"type": "disabled"}
    request = Request(
        llm_completion_url(str(config["baseUrl"])),
        data=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config['apiKey']}",
            "Content-Type": "application/json",
            "User-Agent": "okx-dashboard-llm/0.1",
        },
        method="POST",
    )
    timeout_seconds = llm_request_timeout_seconds(config)
    request_id = uuid.uuid4().hex
    started = time.perf_counter()
    response_payload: dict[str, Any] = {}
    finish_reason = ""
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        raw_body = exc.read().decode("utf-8", errors="replace")
        message = f"LLM HTTP {exc.code}: {raw_body[:400]}"
        usage_log = record_llm_usage_log(
            config,
            request_id,
            request_type,
            "failed",
            {},
            duration_ms,
            timeout_seconds,
            error=message,
            context=context,
        )
        raise LlmCompletionError(message, usage_log) from exc
    except URLError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        message = f"LLM 连接失败：{exc.reason}"
        usage_log = record_llm_usage_log(
            config,
            request_id,
            request_type,
            "failed",
            {},
            duration_ms,
            timeout_seconds,
            error=message,
            context=context,
        )
        raise LlmCompletionError(message, usage_log) from exc
    except TimeoutError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        message = f"LLM 请求超时（{timeout_seconds}秒）。请提高 AI 配置中的超时秒数，或换用响应更快的模型。"
        usage_log = record_llm_usage_log(
            config,
            request_id,
            request_type,
            "timeout",
            {},
            duration_ms,
            timeout_seconds,
            error=message,
            context=context,
        )
        raise LlmCompletionError(message, usage_log) from exc

    duration_ms = int((time.perf_counter() - started) * 1000)
    usage = normalize_llm_usage(response_payload)
    raw_usage = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        message = "LLM 返回结果缺少 choices。"
        usage_log = record_llm_usage_log(
            config,
            request_id,
            request_type,
            "failed",
            usage,
            duration_ms,
            timeout_seconds,
            error=message,
            context=context,
            raw_usage=raw_usage,
        )
        raise LlmCompletionError(message, usage_log)
    first_choice = choices[0]
    finish_reason = str(first_choice.get("finish_reason") or "") if isinstance(first_choice, dict) else ""
    message = first_choice.get("message") if isinstance(first_choice, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not content:
        reasoning_content = message.get("reasoning_content") if isinstance(message, dict) else ""
        reasoning_hint = "；模型返回了 reasoning_content 但没有最终 JSON" if reasoning_content else ""
        error = f"LLM 返回结果缺少 content{reasoning_hint}；finish_reason={finish_reason or 'unknown'}。"
        usage_log = record_llm_usage_log(
            config,
            request_id,
            request_type,
            "failed",
            usage,
            duration_ms,
            timeout_seconds,
            finish_reason=finish_reason,
            error=error,
            context=context,
            raw_usage=raw_usage,
        )
        raise LlmCompletionError(error, usage_log)
    usage_log = record_llm_usage_log(
        config,
        request_id,
        request_type,
        "success",
        usage,
        duration_ms,
        timeout_seconds,
        finish_reason=finish_reason,
        context=context,
        raw_usage=raw_usage,
    )
    return {
        "content": str(content),
        "usage": usage,
        "usage_log": usage_log,
        "request_id": request_id,
        "duration_ms": duration_ms,
        "finish_reason": finish_reason,
    }


def normalize_llm_analysis(parsed: dict[str, Any], config: dict[str, Any], raw_text: str) -> dict[str, Any]:
    confidence = coerce_int(parsed.get("confidence"), 0, 0, 100)
    reasons = parsed.get("reasons")
    risks = parsed.get("risks")
    return {
        "status": "ok",
        "provider": config.get("provider"),
        "model": config.get("model"),
        "mode": config.get("mode"),
        "prompt_version": LLM_PROMPT_VERSION,
        "ts": now_ms(),
        "recommendation": str(parsed.get("recommendation") or "observe")[:40],
        "confidence": confidence,
        "summary": str(parsed.get("summary") or "")[:1200],
        "reasons": [str(item)[:300] for item in reasons[:8]] if isinstance(reasons, list) else [],
        "risks": [str(item)[:300] for item in risks[:8]] if isinstance(risks, list) else [],
        "invalidation": str(parsed.get("invalidation") or "")[:800],
        "notes": str(parsed.get("notes") or "")[:800],
        "raw_text": raw_text[:4000],
    }


def attach_llm_completion_meta(analysis: dict[str, Any], completion: dict[str, Any]) -> dict[str, Any]:
    usage_log = completion.get("usage_log") if isinstance(completion.get("usage_log"), dict) else None
    usage_view = llm_usage_log_view(usage_log)
    if usage_view:
        analysis["usage"] = usage_view
        analysis["usage_log_id"] = usage_view.get("id")
    analysis["request_id"] = completion.get("request_id")
    analysis["duration_ms"] = completion.get("duration_ms")
    analysis["finish_reason"] = completion.get("finish_reason")
    return analysis


def llm_signal_prompt(strategy: dict[str, Any], signal: dict[str, Any], decision: str, message: str, config: dict[str, Any]) -> str:
    payload = {
        "task": "analyze_okx_perpetual_signal",
        "mode": config.get("mode"),
        "constraints": [
            "不要直接下单",
            "不要建议绕过风控",
            "如果数据不足，明确说明不足",
            "输出 JSON 对象",
        ],
        "expected_json_schema": {
            "recommendation": "observe|approve|reject|hold",
            "confidence": "0-100 integer",
            "summary": "短结论",
            "reasons": ["做多/做空/观望的依据"],
            "risks": ["当前信号风险"],
            "invalidation": "信号失效条件",
            "notes": "补充说明",
        },
        "strategy": {
            "id": strategy.get("id"),
            "name": strategy.get("name"),
            "inst_id": strategy.get("inst_id"),
            "bar": strategy.get("bar"),
            "template": strategy.get("template"),
            "fast_window": strategy.get("fast_window"),
            "slow_window": strategy.get("slow_window"),
            "execution_mode": strategy.get("execution_mode"),
            "td_mode": strategy.get("td_mode"),
            "ord_type": strategy.get("ord_type"),
            "sz": strategy.get("sz"),
            "max_order_contracts": strategy.get("max_order_contracts"),
            "max_position_contracts": strategy.get("max_position_contracts"),
        },
        "signal": signal,
        "system_decision": {"decision": decision, "message": message},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def analyze_signal_with_llm(strategy: dict[str, Any], signal: dict[str, Any], decision: str, message: str) -> dict[str, Any] | None:
    config = stored_llm_config()
    if not config.get("enabled"):
        return None
    try:
        prompt = llm_signal_prompt(strategy, signal, decision, message, config)
        completion = llm_chat_completion(
            config,
            [
                {"role": "system", "content": str(config["systemPrompt"])},
                {"role": "user", "content": prompt},
            ],
            request_type="signal_review",
            context={
                "strategy_id": int(strategy.get("id") or 0) or None,
                "inst_id": strategy.get("inst_id"),
                "bar": strategy.get("bar"),
            },
        )
        raw_text = str(completion["content"])
        return attach_llm_completion_meta(normalize_llm_analysis(extract_json_object(raw_text), config, raw_text), completion)
    except Exception as exc:
        usage_log = llm_usage_log_view(exc.usage_log) if isinstance(exc, LlmCompletionError) else None
        return {
            "status": "failed",
            "provider": config.get("provider"),
            "model": config.get("model"),
            "mode": config.get("mode"),
            "prompt_version": LLM_PROMPT_VERSION,
            "ts": now_ms(),
            "error": str(exc)[:1200],
            "usage": usage_log,
            "usage_log_id": usage_log.get("id") if usage_log else None,
        }


def safe_decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def percent_change(start: Decimal | None, end: Decimal | None) -> str:
    if start is None or end is None or start == 0:
        return "0"
    return decimal_display((end - start) / start * Decimal("100"))


def compact_candle_for_llm(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "ts": item.get("ts"),
        "open": item.get("open"),
        "high": item.get("high"),
        "low": item.get("low"),
        "close": item.get("close"),
        "volume": item.get("volume"),
    }


def ma_value(closes: list[Decimal], window: int) -> str:
    if len(closes) < window:
        return ""
    return decimal_display(sum(closes[-window:], Decimal("0")) / Decimal(window))


def candle_market_summary(candles: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [value for value in (safe_decimal(item.get("close")) for item in candles) if value is not None]
    highs = [value for value in (safe_decimal(item.get("high")) for item in candles) if value is not None]
    lows = [value for value in (safe_decimal(item.get("low")) for item in candles) if value is not None]
    volumes = [value for value in (safe_decimal(item.get("volume")) for item in candles) if value is not None]
    last_close = closes[-1] if closes else None
    first_close = closes[0] if closes else None
    recent_window = closes[-20:] if len(closes) >= 20 else closes
    recent_high = max(highs[-20:]) if highs else None
    recent_low = min(lows[-20:]) if lows else None
    volatility = ""
    if recent_window and recent_high is not None and recent_low is not None and last_close:
        volatility = decimal_display((recent_high - recent_low) / last_close * Decimal("100"))
    return {
        "candles": len(candles),
        "firstTs": candles[0].get("ts") if candles else 0,
        "lastTs": candles[-1].get("ts") if candles else 0,
        "lastClose": decimal_display(last_close) if last_close is not None else "",
        "changePct": percent_change(first_close, last_close),
        "ma5": ma_value(closes, 5),
        "ma20": ma_value(closes, 20),
        "ma60": ma_value(closes, 60),
        "recent20High": decimal_display(recent_high) if recent_high is not None else "",
        "recent20Low": decimal_display(recent_low) if recent_low is not None else "",
        "recent20RangePct": volatility,
        "volume20Avg": decimal_display(sum(volumes[-20:], Decimal("0")) / Decimal(min(20, len(volumes)))) if volumes else "",
    }


def score_clamp(value: Decimal | int | float, minimum: int = 0, maximum: int = 100) -> int:
    try:
        numeric = int(Decimal(str(value)).to_integral_value())
    except (InvalidOperation, ValueError):
        numeric = minimum
    return min(max(numeric, minimum), maximum)


def radar_request_key(request: RadarScanRequest) -> str:
    return json.dumps(
        {
            "settlement": request.settlement.strip().lower(),
            "minVolume": decimal_display(safe_decimal(request.minVolume) or Decimal("0")),
            "volatility": request.volatility.strip().lower(),
            "risk": request.risk.strip().lower(),
            "limit": request.limit,
            "candidateLimit": request.candidateLimit,
            "bar": request.bar.strip(),
            "explain": bool(request.explain),
            "schemaVersion": RADAR_SCHEMA_VERSION,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def radar_result_decimal(result: dict[str, Any], key: str, nested_key: str = "") -> Decimal | None:
    value: Any
    if nested_key:
        nested = result.get(key) if isinstance(result.get(key), dict) else {}
        value = nested.get(nested_key)
    else:
        value = result.get(key)
    return safe_decimal(value)


def radar_decimal_median(values: list[Decimal]) -> str:
    if not values:
        return "0"
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return decimal_display(ordered[midpoint])
    return decimal_display((ordered[midpoint - 1] + ordered[midpoint]) / Decimal("2"))


def radar_market_contract_item(result: dict[str, Any]) -> dict[str, Any]:
    scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
    liquidity = result.get("liquidity") if isinstance(result.get("liquidity"), dict) else {}
    entry_assessment = result.get("entryAssessment") if isinstance(result.get("entryAssessment"), dict) else {}
    return {
        "instId": str(result.get("instId") or ""),
        "score": coerce_int(scores.get("opportunity"), 0, 0, 100),
        "tradabilityStatus": str(result.get("tradabilityStatus") or ""),
        "riskLevel": str(result.get("riskLevel") or ""),
        "volatilityLevel": str(result.get("volatilityLevel") or ""),
        "change24hPct": decimal_display_fixed(result.get("change24hPct"), 2),
        "range24hPct": decimal_display_fixed(result.get("range24hPct"), 2),
        "recent20RangePct": decimal_display_fixed(metrics.get("recent20RangePct"), 2),
        "volumeSpike": decimal_display_fixed(metrics.get("volumeSpike"), 2),
        "liquidity": {
            "value": decimal_display_fixed(liquidity.get("value"), 0) if liquidity.get("value") else "",
            "basis": str(liquidity.get("basis") or "missing"),
            "unit": str(liquidity.get("unit") or ""),
            "displayLabel": str(liquidity.get("displayLabel") or "24h 流动性"),
            "comparable": bool(liquidity.get("comparable")),
        },
        "entryAssessment": {
            "status": str(entry_assessment.get("status") or "watch"),
            "label": str(entry_assessment.get("label") or "谨慎观察"),
            "confidence": coerce_int(entry_assessment.get("confidence"), 0, 0, 100),
            "summary": str(entry_assessment.get("summary") or ""),
            "drivers": [str(item) for item in (entry_assessment.get("drivers") or [])[:4]],
        },
        "tags": [str(item) for item in (result.get("tags") or [])[:5]],
        "warnings": [str(item) for item in (result.get("warnings") or [])[:3]],
    }


def build_radar_market_summary(radar_payload: dict[str, Any], scan_results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [item for item in (scan_results if scan_results is not None else radar_payload.get("data") or []) if isinstance(item, dict)]
    summary = radar_payload.get("summary") if isinstance(radar_payload.get("summary"), dict) else {}
    scan_ts = coerce_int(radar_payload.get("ts"), now_ms(), 0, 9_999_999_999_999)

    changes = [value for value in (radar_result_decimal(item, "change24hPct") for item in rows) if value is not None]
    ranges = [value for value in (radar_result_decimal(item, "range24hPct") for item in rows) if value is not None]
    comparable_turnovers = [
        value
        for item in rows
        if isinstance(item.get("liquidity"), dict) and item["liquidity"].get("comparable")
        for value in [radar_result_decimal(item, "liquidity", "value")]
        if value is not None
    ]
    volume_spikes = [value for value in (radar_result_decimal(item, "metrics", "volumeSpike") for item in rows) if value is not None]

    rising = sum(1 for value in changes if value > Decimal("1"))
    falling = sum(1 for value in changes if value < Decimal("-1"))
    flat = max(0, len(rows) - rising - falling)
    high_volatility = sum(1 for item in rows if item.get("volatilityLevel") == "high")
    medium_volatility = sum(1 for item in rows if item.get("volatilityLevel") == "medium")
    low_volatility = sum(1 for item in rows if item.get("volatilityLevel") == "low")
    high_risk = sum(1 for item in rows if item.get("riskLevel") == "high")
    medium_risk = sum(1 for item in rows if item.get("riskLevel") == "medium")
    low_risk = sum(1 for item in rows if item.get("riskLevel") == "low")
    playable = sum(1 for item in rows if item.get("tradabilityStatus") == "playable")
    low_liquidity = sum(1 for item in rows if item.get("tradabilityStatus") == "low_liquidity")
    watch_only = sum(1 for item in rows if item.get("tradabilityStatus") == "watch_only")
    stale_or_missing = sum(
        1
        for item in rows
        if coerce_int((item.get("scores") or {}).get("dataQuality"), 0, 0, 100) < 70
        or coerce_int((item.get("metrics") or {}).get("candleCount"), 0, 0, 10_000) < 20
    )
    abnormal_moves = sum(
        1
        for item in rows
        if (radar_result_decimal(item, "range24hPct") or Decimal("0")) >= Decimal("18")
        or (radar_result_decimal(item, "metrics", "recent20RangePct") or Decimal("0")) >= Decimal("8")
    )

    top_turnover_rows = sorted(
        rows,
        key=lambda item: radar_result_decimal(item, "liquidity", "value") or Decimal("0"),
        reverse=True,
    )[:RADAR_MARKET_TOP_LIST_LIMIT]
    top_volatility_rows = sorted(
        rows,
        key=lambda item: radar_result_decimal(item, "range24hPct") or Decimal("0"),
        reverse=True,
    )[:RADAR_MARKET_TOP_LIST_LIMIT]
    volume_spike_rows = sorted(
        rows,
        key=lambda item: radar_result_decimal(item, "metrics", "volumeSpike") or Decimal("0"),
        reverse=True,
    )[:RADAR_MARKET_TOP_LIST_LIMIT]

    return {
        "scan": {
            "schemaVersion": RADAR_SCHEMA_VERSION,
            "total": coerce_int(summary.get("total"), len(rows), 0, 10_000),
            "candidates": coerce_int(summary.get("candidates"), len(rows), 0, 10_000),
            "returned": coerce_int(summary.get("returned"), len(rows), 0, 10_000),
            "analyzed": len(rows),
            "bar": str((radar_payload.get("filters") or {}).get("bar") or RADAR_DEFAULT_BAR),
            "source": str(radar_payload.get("source") or "radar-scan"),
            "ts": scan_ts,
            "cacheAgeMs": coerce_int(radar_payload.get("cacheAgeMs"), 0, 0, 86_400_000),
        },
        "breadth": {
            "rising": rising,
            "falling": falling,
            "flat": flat,
            "medianChange24hPct": decimal_display_fixed(radar_decimal_median(changes), 2),
            "maxChange24hPct": decimal_display_fixed(max(changes), 2) if changes else "0",
            "minChange24hPct": decimal_display_fixed(min(changes), 2) if changes else "0",
        },
        "liquidity": {
            "playable": playable,
            "lowLiquidity": low_liquidity,
            "watchOnly": watch_only,
            "comparableCount": len(comparable_turnovers),
            "totalComparableTurnover": decimal_display_fixed(sum(comparable_turnovers, Decimal("0")), 0),
            "medianComparableTurnover": decimal_display_fixed(radar_decimal_median(comparable_turnovers), 0),
        },
        "volatility": {
            "high": high_volatility,
            "medium": medium_volatility,
            "low": low_volatility,
            "medianRange24hPct": decimal_display_fixed(radar_decimal_median(ranges), 2),
            "maxRange24hPct": decimal_display_fixed(max(ranges), 2) if ranges else "0",
            "medianVolumeSpike": decimal_display_fixed(radar_decimal_median(volume_spikes), 2),
        },
        "risk": {
            "low": low_risk,
            "medium": medium_risk,
            "high": high_risk,
            "staleOrMissingData": stale_or_missing,
            "abnormalMoves": abnormal_moves,
            "warningCount": sum(len(item.get("warnings") or []) for item in rows),
        },
        "leaders": [radar_market_contract_item(item) for item in rows[:RADAR_MARKET_LEADER_LIMIT]],
        "topTurnover": [radar_market_contract_item(item) for item in top_turnover_rows],
        "topVolatility": [radar_market_contract_item(item) for item in top_volatility_rows],
        "volumeSpikes": [radar_market_contract_item(item) for item in volume_spike_rows],
    }


def ticker_decimal(ticker: dict[str, Any] | None, keys: list[str]) -> Decimal | None:
    if not ticker:
        return None
    for key in keys:
        value = safe_decimal(ticker.get(key))
        if value is not None:
            return value
    return None


def radar_liquidity(ticker: dict[str, Any] | None, settle_ccy: str) -> dict[str, Any]:
    settle = settle_ccy.upper()
    quote_turnover = ticker_decimal(ticker, ["volCcyQuote24h"])
    if quote_turnover is not None:
        return {
            "value": quote_turnover,
            "basis": "quote_turnover",
            "unit": settle if settle in {"USDT", "USDC"} else "QUOTE",
            "confidence": "high",
            "displayLabel": f"24h 成交额({settle if settle in {'USDT', 'USDC'} else '计价币'})",
            "comparable": True,
        }

    base_volume = ticker_decimal(ticker, ["volCcy24h"])
    last = ticker_decimal(ticker, ["last", "lastPx", "close"])
    if base_volume is not None and last is not None and last > 0 and settle in {"USDT", "USDC"}:
        return {
            "value": base_volume * last,
            "basis": "estimated_quote_turnover",
            "unit": settle,
            "confidence": "medium",
            "displayLabel": f"24h 估算成交额({settle})",
            "comparable": True,
        }
    if base_volume is not None:
        return {
            "value": base_volume,
            "basis": "base_volume",
            "unit": "BASE",
            "confidence": "medium",
            "displayLabel": "24h 基础币量",
            "comparable": False,
        }

    contract_volume = ticker_decimal(ticker, ["vol24h"])
    if contract_volume is not None:
        return {
            "value": contract_volume,
            "basis": "contract_volume",
            "unit": "张",
            "confidence": "low",
            "displayLabel": "24h 合约张数",
            "comparable": False,
        }

    return {
        "value": None,
        "basis": "missing",
        "unit": "",
        "confidence": "low",
        "displayLabel": "24h 流动性缺失",
        "comparable": False,
    }


def radar_liquidity_payload(liquidity: dict[str, Any]) -> dict[str, Any]:
    value = liquidity.get("value")
    return {
        "value": decimal_display(value) if isinstance(value, Decimal) else "",
        "basis": liquidity.get("basis") or "missing",
        "unit": liquidity.get("unit") or "",
        "confidence": liquidity.get("confidence") or "low",
        "displayLabel": liquidity.get("displayLabel") or "24h 流动性",
        "comparable": bool(liquidity.get("comparable")),
    }


def radar_turnover_window(
    candles: list[dict[str, Any]],
    liquidity: dict[str, Any],
) -> dict[str, Any]:
    if not liquidity.get("comparable"):
        return {
            "value": "",
            "unit": str(liquidity.get("unit") or ""),
            "comparable": False,
            "candleCount": 0,
            "label": "1小时成交额",
            "warning": "当前成交额口径无法统一比较，暂不参与小时成交额排行。",
        }

    confirmed = [item for item in candles if str(item.get("confirm", "1")) == "1"]
    window = confirmed[-RADAR_ONE_HOUR_CANDLE_COUNT:]
    if len(window) < RADAR_ONE_HOUR_CANDLE_COUNT:
        return {
            "value": "",
            "unit": str(liquidity.get("unit") or ""),
            "comparable": False,
            "candleCount": len(window),
            "label": "1小时成交额",
            "warning": "小时成交额等待四根已收盘的15分钟K线确认。",
        }

    values = [safe_decimal(item.get("volumeQuote")) for item in window]
    if any(value is None or value <= 0 for value in values):
        return {
            "value": "",
            "unit": str(liquidity.get("unit") or ""),
            "comparable": False,
            "candleCount": len(window),
            "label": "1小时成交额",
            "warning": "小时成交额数据待补齐，暂不使用估算值。",
        }

    return {
        "value": decimal_display(sum((value for value in values if value is not None), Decimal("0"))),
        "unit": str(liquidity.get("unit") or ""),
        "comparable": True,
        "candleCount": RADAR_ONE_HOUR_CANDLE_COUNT,
        "label": "1小时成交额",
        "warning": "",
    }


def radar_sort_label(sort_by: str) -> str:
    return "24小时成交额" if sort_by == "turnover_24h" else "1小时成交额"


def radar_turnover_for_sort(result: dict[str, Any], sort_by: str) -> tuple[Decimal | None, bool]:
    if sort_by == "turnover_24h":
        liquidity = result.get("liquidity") if isinstance(result.get("liquidity"), dict) else {}
        value = safe_decimal(liquidity.get("value"))
        return value, bool(liquidity.get("comparable")) and value is not None
    turnover = result.get("turnover") if isinstance(result.get("turnover"), dict) else {}
    one_hour = turnover.get("oneHour") if isinstance(turnover.get("oneHour"), dict) else {}
    value = safe_decimal(one_hour.get("value"))
    return value, bool(one_hour.get("comparable")) and value is not None


def radar_result_sort_key(result: dict[str, Any], sort_by: str) -> tuple[int, Decimal, Decimal, str]:
    value, comparable = radar_turnover_for_sort(result, sort_by)
    daily_value, daily_comparable = radar_turnover_for_sort(result, "turnover_24h")
    return (
        0 if comparable else 1,
        -(value or Decimal("0")),
        -(daily_value or Decimal("0")) if daily_comparable else Decimal("0"),
        str(result.get("instId") or ""),
    )


def radar_refresh_warning(inst_id: str, exc: OkxError) -> str:
    message = str(exc).lower()
    if "incompleteread" in message or "incomplete" in message or "remote end closed" in message:
        return f"{inst_id} K线暂时无法更新，已使用可用缓存或降级数据；可稍后重新扫描。"
    if "timeout" in message or "timed out" in message:
        return f"{inst_id} K线请求超时，已使用可用缓存或降级数据；可稍后重新扫描。"
    return f"{inst_id} K线暂时无法更新，已使用可用缓存或降级数据。"


def radar_refresh_warning_summary(warnings: list[str]) -> str:
    if not warnings:
        return ""
    return f"{len(warnings)} 个合约 K线暂时无法更新，已使用可用缓存或降级数据；可稍后重新扫描。"


def pct_from_values(low: Decimal | None, high: Decimal | None, base: Decimal | None) -> Decimal:
    if low is None or high is None or base is None or base <= 0 or high < low:
        return Decimal("0")
    return (high - low) / base * Decimal("100")


def radar_volume_score(volume: Decimal | None) -> int:
    if volume is None or volume <= 0:
        return 0
    thresholds = [
        (Decimal("1000000000"), 100),
        (Decimal("500000000"), 92),
        (Decimal("100000000"), 82),
        (Decimal("50000000"), 72),
        (Decimal("10000000"), 58),
        (Decimal("1000000"), 42),
        (Decimal("100000"), 25),
    ]
    for threshold, score in thresholds:
        if volume >= threshold:
            return score
    return 12


def radar_pct_score(value: Decimal, full_score_at: Decimal) -> int:
    if full_score_at <= 0:
        return 0
    return score_clamp(value / full_score_at * Decimal("100"))


def candle_return_stats(candles: list[dict[str, Any]]) -> dict[str, Decimal]:
    ranges: list[Decimal] = []
    returns: list[Decimal] = []
    volumes: list[Decimal] = []
    closes: list[Decimal] = []
    for item in candles:
        open_price = safe_decimal(item.get("open"))
        high = safe_decimal(item.get("high"))
        low = safe_decimal(item.get("low"))
        close = safe_decimal(item.get("close"))
        volume = safe_decimal(item.get("volume"))
        if close is not None:
            closes.append(close)
        if volume is not None:
            volumes.append(volume)
        if high is not None and low is not None and close is not None and close > 0:
            ranges.append((high - low) / close * Decimal("100"))
        if open_price is not None and close is not None and open_price > 0:
            returns.append(abs((close - open_price) / open_price * Decimal("100")))

    recent_volumes = volumes[-20:]
    baseline_volumes = volumes[-60:-20] if len(volumes) >= 60 else volumes[:-20]
    recent_volume_avg = sum(recent_volumes, Decimal("0")) / Decimal(len(recent_volumes)) if recent_volumes else Decimal("0")
    baseline_volume_avg = (
        sum(baseline_volumes, Decimal("0")) / Decimal(len(baseline_volumes)) if baseline_volumes else recent_volume_avg
    )
    volume_spike = recent_volume_avg / baseline_volume_avg if baseline_volume_avg > 0 else Decimal("1")
    recent_highs = [value for value in (safe_decimal(item.get("high")) for item in candles[-20:]) if value is not None]
    recent_lows = [value for value in (safe_decimal(item.get("low")) for item in candles[-20:]) if value is not None]
    recent_high = max(recent_highs) if recent_highs else None
    recent_low = min(recent_lows) if recent_lows else None
    last_close = closes[-1] if closes else None
    recent_closes = closes[-20:]
    recent_first_close = recent_closes[0] if recent_closes else None
    recent_change_pct = safe_decimal(percent_change(recent_first_close, last_close)) or Decimal("0")

    return {
        "candleCount": Decimal(len(candles)),
        "avgRangePct": sum(ranges[-20:], Decimal("0")) / Decimal(min(20, len(ranges))) if ranges else Decimal("0"),
        "avgAbsReturnPct": sum(returns[-20:], Decimal("0")) / Decimal(min(20, len(returns))) if returns else Decimal("0"),
        "recent20RangePct": pct_from_values(recent_low, recent_high, last_close),
        "recent20ChangePct": recent_change_pct,
        "volumeSpike": volume_spike,
        "volume20Avg": recent_volume_avg,
        "lastClose": last_close or Decimal("0"),
    }


def radar_risk_level(score: int, warnings: list[str]) -> str:
    if score >= 35 or len(warnings) >= 2:
        return "high"
    if score >= 15 or warnings:
        return "medium"
    return "low"


def radar_volatility_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def radar_market_condition(candle_stats: dict[str, Decimal], range24h_pct: Decimal) -> dict[str, str]:
    if candle_stats["candleCount"] < Decimal("20"):
        return {
            "key": "unknown",
            "label": "方向待确认",
            "summary": "近期已收盘 K 线不足，暂不判断市场方向。",
        }

    recent_range_pct = candle_stats["recent20RangePct"]
    directional_change_pct = abs(candle_stats["recent20ChangePct"])
    if range24h_pct >= Decimal("12") or recent_range_pct >= Decimal("8"):
        return {
            "key": "high_volatility",
            "label": "高波动运行",
            "summary": "近期区间扩大，价格可能快速反复，仓位和止损需要更保守。",
        }
    if recent_range_pct >= Decimal("1.2") and directional_change_pct <= max(
        Decimal("0.6"), recent_range_pct * Decimal("0.35")
    ):
        return {
            "key": "range",
            "label": "横盘震荡",
            "summary": "近20根 K 线在区间内来回波动，方向未确认；避免追突破，等待放量和收盘确认。",
        }
    if directional_change_pct >= max(Decimal("1.2"), recent_range_pct * Decimal("0.65")):
        return {
            "key": "trend",
            "label": "趋势运行",
            "summary": "近20根 K 线方向位移较明显，仍需结合量能和关键位置确认延续性。",
        }
    return {
        "key": "mixed",
        "label": "方向待确认",
        "summary": "近期波动与方向没有形成一致性，优先观察而非追价。",
    }


def radar_entry_assessment(
    tradability_status: str,
    liquidity: dict[str, Any],
    volume_score: int,
    volatility_score: int,
    risk_penalty: int,
    risk_level: str,
    range24h_pct: Decimal,
    recent_range_pct: Decimal,
    volume_spike: Decimal,
) -> dict[str, Any]:
    liquidity_value = liquidity.get("value") if isinstance(liquidity.get("value"), Decimal) else None
    liquidity_label = str(liquidity.get("displayLabel") or "24h 流动性")
    drivers = [
        f"{liquidity_label} {decimal_display_fixed(liquidity_value, 0) if liquidity_value is not None else '缺失'}",
        f"24h 振幅 {decimal_display_fixed(range24h_pct, 2)}%",
        f"近20根振幅 {decimal_display_fixed(recent_range_pct, 2)}%",
        f"量能脉冲 {decimal_display_fixed(volume_spike, 2)}x",
    ]

    if tradability_status == "low_liquidity":
        return {
            "status": "avoid",
            "label": "暂不入手",
            "confidence": 72,
            "summary": "成交量未达到可玩门槛，即使浮动较大也优先规避。",
            "drivers": drivers,
        }
    if tradability_status != "playable":
        return {
            "status": "watch",
            "label": "仅观察",
            "confidence": 58,
            "summary": "成交量口径或 K 线数据不够稳定，先观察，不建议直接入场。",
            "drivers": drivers,
        }
    if risk_level == "high" or risk_penalty >= 35 or range24h_pct >= Decimal("18") or recent_range_pct >= Decimal("10"):
        return {
            "status": "avoid",
            "label": "风险过高",
            "confidence": 68,
            "summary": "成交量满足基础条件，但浮动过大或风险扣分偏高，不适合追入。",
            "drivers": drivers,
        }
    if volatility_score < 40 or range24h_pct < Decimal("3") or recent_range_pct < Decimal("1.2"):
        return {
            "status": "wait",
            "label": "等待放量",
            "confidence": 62,
            "summary": "成交量可用，但当前浮动不足，短线入手机会还不清晰。",
            "drivers": drivers,
        }
    if volume_score >= 58 and 40 <= volatility_score <= 85 and risk_level in {"low", "medium"}:
        confidence = 82 if risk_level == "low" and volume_score >= 72 else 74
        return {
            "status": "ready",
            "label": "可入手观察",
            "confidence": confidence,
            "summary": "成交量和浮动同时满足观察条件，可进入候选池继续看盘口、止损和触发位。",
            "drivers": drivers,
        }
    return {
        "status": "watch",
        "label": "谨慎观察",
        "confidence": 60,
        "summary": "成交量或浮动只有一项较强，适合观察确认，不宜直接追入。",
        "drivers": drivers,
    }


def radar_tradability_status(
    state: str,
    liquidity: dict[str, Any],
    liquidity_score: int,
    candle_count: Decimal,
    min_volume: Decimal,
) -> str:
    value = liquidity.get("value")
    playable_threshold = max(min_volume, RADAR_PLAYABLE_QUOTE_VOLUME)
    if state != "live" or candle_count < Decimal("20"):
        return "watch_only"
    if not liquidity.get("comparable") or not isinstance(value, Decimal):
        return "watch_only"
    if value < playable_threshold or liquidity_score < 58:
        return "low_liquidity"
    return "playable"


def radar_tradability_rank(status: str) -> int:
    if status == "playable":
        return 2
    if status == "watch_only":
        return 1
    return 0


def radar_default_reasons(
    inst_id: str,
    volume_score: int,
    volatility_score: int,
    risk_level: str,
    volume24h: Decimal | None,
    tradability_status: str,
    liquidity: dict[str, Any],
    range24h_pct: Decimal,
    recent_range_pct: Decimal,
) -> tuple[list[str], list[str], list[str]]:
    tags: list[str] = []
    reasons: list[str] = []
    warnings: list[str] = []

    if volume_score >= 70:
        tags.append("流动性好")
        reasons.append("24h 成交量靠前，适合进一步观察。")
    elif volume_score >= 40:
        tags.append("流动性中等")
        reasons.append("成交量达到基础筛选线，但需要注意滑点。")
    else:
        warnings.append("成交量偏低，实盘交易前需要谨慎确认盘口深度。")

    if tradability_status == "playable":
        tags.append("可玩")
    elif tradability_status == "low_liquidity":
        tags.append("流动性不足")
        warnings.append("流动性未达到默认可玩门槛，不能只因波动大就作为首选。")
    else:
        tags.append("仅观察")
        if not liquidity.get("comparable"):
            warnings.append("24h 流动性不是统一成交额口径，排序可信度降低。")

    if volatility_score >= 70:
        tags.append("高波动")
        reasons.append("24h 区间和近期 K 线振幅较高，短线活跃度强。")
    elif volatility_score >= 40:
        tags.append("波动适中")
        reasons.append("波动处于中等水平，适合等待更清晰的机会。")
    else:
        tags.append("低波动")
        warnings.append("近期波动偏低，短线机会可能不足。")

    if range24h_pct >= Decimal("12"):
        warnings.append("24h 振幅较大，追涨追跌风险高。")
    if recent_range_pct >= Decimal("8"):
        warnings.append("近期 K 线区间扩大，仓位和止损需要更保守。")
    if volume24h is None:
        warnings.append("Ticker 成交量缺失，评分可信度降低。")
    if risk_level == "low":
        tags.append("适合关注")
    elif risk_level == "high":
        tags.append("高风险")

    if not reasons:
        reasons.append(f"{inst_id} 当前数据不足，只建议加入观察列表。")
    return tags[:5], reasons[:4], warnings[:5]


def score_radar_contract(
    instrument: dict[str, Any],
    ticker: dict[str, Any] | None,
    candles: list[dict[str, Any]],
    min_volume: Decimal,
) -> dict[str, Any]:
    inst_id = str(instrument.get("inst_id") or instrument.get("instId") or "").upper()
    state = str(instrument.get("state") or "").lower()
    last = ticker_decimal(ticker, ["last", "lastPx", "close"])
    open24h = ticker_decimal(ticker, ["open24h", "sodUtc0", "sodUtc8"])
    high24h = ticker_decimal(ticker, ["high24h"])
    low24h = ticker_decimal(ticker, ["low24h"])
    settle_ccy = str(instrument.get("settle_ccy") or instrument.get("settleCcy") or "")
    liquidity = radar_liquidity(ticker, settle_ccy)
    one_hour_turnover = radar_turnover_window(candles, liquidity)
    volume24h = liquidity.get("value") if isinstance(liquidity.get("value"), Decimal) else None
    change24h_pct = percent_change(open24h, last)
    range24h_pct = pct_from_values(low24h, high24h, last)
    candle_stats = candle_return_stats(candles)
    market_condition = radar_market_condition(candle_stats, range24h_pct)

    warnings: list[str] = []
    if state != "live":
        warnings.append("合约当前不是 live 状态。")
    if volume24h is None or volume24h < min_volume:
        warnings.append("24h 成交量低于筛选阈值。")
    if not liquidity.get("comparable"):
        warnings.append("24h 流动性不是统一成交额口径，评分可信度降低。")
    if candle_stats["candleCount"] < Decimal("20"):
        warnings.append("近期 K 线不足，波动评分可信度降低。")

    volume_score = radar_volume_score(volume24h)
    data_score = 100
    if not ticker:
        data_score -= 40
    if not liquidity.get("comparable"):
        data_score -= 15
    if candle_stats["candleCount"] < Decimal("20"):
        data_score -= 35
    if last is None or last <= 0:
        data_score -= 25
    state_score = 100 if state == "live" else 0
    tradability_score = score_clamp(
        Decimal(volume_score) * Decimal("0.65")
        + Decimal(state_score) * Decimal("0.2")
        + Decimal(max(data_score, 0)) * Decimal("0.15")
    )

    volatility_score = score_clamp(
        Decimal(radar_pct_score(range24h_pct, Decimal("12"))) * Decimal("0.45")
        + Decimal(radar_pct_score(candle_stats["recent20RangePct"], Decimal("8"))) * Decimal("0.25")
        + Decimal(radar_pct_score(candle_stats["avgAbsReturnPct"], Decimal("2.5"))) * Decimal("0.2")
        + Decimal(radar_pct_score(max(candle_stats["volumeSpike"] - Decimal("1"), Decimal("0")), Decimal("2"))) * Decimal("0.1")
    )

    risk_penalty = 0
    if volume24h is None or volume24h < min_volume:
        risk_penalty += 30
    if candle_stats["candleCount"] < Decimal("20"):
        risk_penalty += 20
    if range24h_pct >= Decimal("18"):
        risk_penalty += 15
    if state != "live":
        risk_penalty += 60
    if not liquidity.get("comparable"):
        risk_penalty += 10
    tradability_status = radar_tradability_status(state, liquidity, volume_score, candle_stats["candleCount"], min_volume)
    risk_level = radar_risk_level(risk_penalty, warnings)
    opportunity_score = score_clamp(
        Decimal(tradability_score) * Decimal("0.58") + Decimal(volatility_score) * Decimal("0.42") - Decimal(risk_penalty)
    )
    entry_assessment = radar_entry_assessment(
        tradability_status,
        liquidity,
        volume_score,
        volatility_score,
        risk_penalty,
        risk_level,
        range24h_pct,
        candle_stats["recent20RangePct"],
        candle_stats["volumeSpike"],
    )
    tags, reasons, default_warnings = radar_default_reasons(
        inst_id,
        volume_score,
        volatility_score,
        risk_level,
        volume24h,
        tradability_status,
        liquidity,
        range24h_pct,
        candle_stats["recent20RangePct"],
    )
    warnings = list(dict.fromkeys(warnings + default_warnings))
    if market_condition["key"] == "range":
        warnings.append(market_condition["summary"])

    return {
        "instId": inst_id,
        "instFamily": instrument.get("inst_family") or instrument.get("instFamily") or "",
        "settleCcy": settle_ccy,
        "state": state or "",
        "last": decimal_display(last) if last is not None else "",
        "change24hPct": change24h_pct,
        "range24hPct": decimal_display(range24h_pct),
        "volume24h": decimal_display(volume24h) if volume24h is not None else "",
        "liquidity": radar_liquidity_payload(liquidity),
        "turnover": {
            "oneHour": one_hour_turnover,
            "twentyFourHour": {
                "value": decimal_display(volume24h) if volume24h is not None else "",
                "unit": str(liquidity.get("unit") or ""),
                "comparable": bool(liquidity.get("comparable")),
                "label": radar_sort_label("turnover_24h"),
                "warning": "" if liquidity.get("comparable") else "当前成交额口径无法统一比较，暂不参与24小时成交额排行。",
            },
        },
        "tradabilityStatus": tradability_status,
        "bar": RADAR_DEFAULT_BAR,
        "metrics": {
            "candleCount": int(candle_stats["candleCount"]),
            "recent20RangePct": decimal_display(candle_stats["recent20RangePct"]),
            "recent20ChangePct": decimal_display(candle_stats["recent20ChangePct"]),
            "avgAbsReturnPct": decimal_display(candle_stats["avgAbsReturnPct"]),
            "avgRangePct": decimal_display(candle_stats["avgRangePct"]),
            "volumeSpike": decimal_display(candle_stats["volumeSpike"]),
            "volume20Avg": decimal_display(candle_stats["volume20Avg"]),
            "tickSize": instrument.get("tick_sz") or instrument.get("tickSz") or "",
            "lotSize": instrument.get("lot_sz") or instrument.get("lotSz") or "",
            "contractValue": instrument.get("ct_val") or instrument.get("ctVal") or "",
        },
        "scores": {
            "liquidity": volume_score,
            "tradability": tradability_score,
            "volatility": volatility_score,
            "riskPenalty": risk_penalty,
            "opportunity": opportunity_score,
            "dataQuality": score_clamp(data_score),
        },
        "entryAssessment": entry_assessment,
        "volatilityLevel": radar_volatility_level(volatility_score),
        "riskLevel": risk_level,
        "marketCondition": market_condition,
        "tags": list(dict.fromkeys(tags + [str(entry_assessment["label"])]))[:6],
        "reasons": list(dict.fromkeys([str(entry_assessment["summary"])] + reasons))[:4],
        "warnings": warnings[:6],
    }


def normalize_radar_request(
    settlement: str,
    min_volume: str,
    volatility: str,
    risk: str,
    limit: int,
    candidate_limit: int,
    bar: str,
    sort_by: str,
    explain: bool,
) -> RadarScanRequest:
    normalized_settlement = settlement.strip().lower() or "usdt"
    if normalized_settlement not in {"all", "usdt", "coin"}:
        raise HTTPException(status_code=400, detail="合约雷达结算币种仅支持 all、usdt 或 coin。")
    normalized_volatility = volatility.strip().lower() or "all"
    if normalized_volatility not in {"all", "low", "medium", "high"}:
        raise HTTPException(status_code=400, detail="合约雷达波动筛选仅支持 all、low、medium 或 high。")
    normalized_risk = risk.strip().lower() or "all"
    if normalized_risk not in {"all", "low", "medium", "high"}:
        raise HTTPException(status_code=400, detail="合约雷达风险筛选仅支持 all、low、medium 或 high。")
    normalized_bar = bar.strip() or RADAR_DEFAULT_BAR
    if normalized_bar not in SUPPORTED_BARS:
        raise HTTPException(status_code=400, detail="合约雷达 K 线周期不受支持。")
    normalized_sort_by = sort_by.strip() or RADAR_DEFAULT_SORT
    if normalized_sort_by not in RADAR_SORT_KEYS:
        raise HTTPException(status_code=400, detail="合约雷达排序仅支持 turnover_1h 或 turnover_24h。")
    decimal_text(min_volume, "最小成交量")
    return RadarScanRequest(
        settlement=normalized_settlement,
        minVolume=min_volume,
        volatility=normalized_volatility,
        risk=normalized_risk,
        limit=limit,
        candidateLimit=candidate_limit,
        bar=normalized_bar,
        sortBy=normalized_sort_by,
        explain=explain,
    )


def radar_filter_instrument(instrument: dict[str, Any], request: RadarScanRequest) -> bool:
    if str(instrument.get("state") or "").lower() != "live":
        return False
    settle = str(instrument.get("settle_ccy") or "").upper()
    if request.settlement == "usdt":
        return settle == "USDT"
    if request.settlement == "coin":
        return settle != "USDT"
    return True


def radar_result_matches_filters(result: dict[str, Any], request: RadarScanRequest) -> bool:
    if request.volatility != "all" and result.get("volatilityLevel") != request.volatility:
        return False
    if request.risk != "all" and result.get("riskLevel") != request.risk:
        return False
    return True


def normalize_legacy_radar_result(result: dict[str, Any]) -> dict[str, Any]:
    updated = dict(result)
    if not isinstance(updated.get("liquidity"), dict):
        value = str(updated.get("volume24h") or "")
        updated["liquidity"] = {
            "value": value,
            "basis": "legacy_volume",
            "unit": "",
            "confidence": "low" if value else "low",
            "displayLabel": "24h 量(旧缓存)",
            "comparable": False,
        }
    if not updated.get("tradabilityStatus"):
        risk_level = str(updated.get("riskLevel") or "")
        updated["tradabilityStatus"] = "watch_only" if risk_level == "high" else "playable"
    scores = updated.get("scores")
    if isinstance(scores, dict) and "liquidity" not in scores:
        scores["liquidity"] = scores.get("tradability", 0)
    if not isinstance(updated.get("entryAssessment"), dict):
        updated["entryAssessment"] = {
            "status": "watch",
            "label": "谨慎观察",
            "confidence": 50,
            "summary": "旧缓存缺少入手判断，请重新扫描获取成交量与浮动分析。",
            "drivers": [],
        }
    return updated


def normalize_radar_payload(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    filters = updated.get("filters") if isinstance(updated.get("filters"), dict) else {}
    sort_by = str(filters.get("sortBy") or "")
    legacy_sort = sort_by not in RADAR_SORT_KEYS
    if legacy_sort:
        filters = {**filters, "sortBy": RADAR_DEFAULT_SORT}
        updated["filters"] = filters
        updated["sort"] = {
            "key": RADAR_DEFAULT_SORT,
            "label": radar_sort_label(RADAR_DEFAULT_SORT),
            "candidateScope": "旧缓存未包含小时成交额排行，请重新扫描。",
            "legacy": True,
        }
    elif not isinstance(updated.get("sort"), dict):
        updated["sort"] = {
            "key": sort_by,
            "label": radar_sort_label(sort_by),
            "candidateScope": "按已筛选候选池排行。",
            "legacy": False,
        }
    rows = updated.get("data")
    if isinstance(rows, list):
        normalized_rows = [normalize_legacy_radar_result(item) if isinstance(item, dict) else item for item in rows]
        if legacy_sort:
            for item in normalized_rows:
                if not isinstance(item, dict):
                    continue
                item.setdefault(
                    "turnover",
                    {
                        "oneHour": {
                            "value": "",
                            "unit": "",
                            "comparable": False,
                            "candleCount": 0,
                            "label": radar_sort_label(RADAR_DEFAULT_SORT),
                            "warning": "旧缓存未包含小时成交额，请重新扫描。",
                        }
                    },
                )
        updated["data"] = normalized_rows
    rankings = updated.get("rankings")
    if isinstance(rankings, dict):
        normalized_rankings: dict[str, list[Any]] = {}
        for sort_key in RADAR_SORT_KEYS:
            ranking_rows = rankings.get(sort_key)
            if isinstance(ranking_rows, list):
                normalized_rankings[sort_key] = [
                    normalize_legacy_radar_result(item) if isinstance(item, dict) else item for item in ranking_rows
                ]
        if len(normalized_rankings) == len(RADAR_SORT_KEYS):
            updated["rankings"] = normalized_rankings
        else:
            updated.pop("rankings", None)
    return updated


def radar_payload_for_sort(payload: dict[str, Any], sort_by: str) -> dict[str, Any]:
    result = normalize_radar_payload(payload)
    rankings = result.get("rankings") if isinstance(result.get("rankings"), dict) else {}
    ranking_rows = rankings.get(sort_by)
    if not isinstance(ranking_rows, list):
        return result

    filters = result.get("filters") if isinstance(result.get("filters"), dict) else {}
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    sort = result.get("sort") if isinstance(result.get("sort"), dict) else {}
    market_summaries = result.get("marketSummaries") if isinstance(result.get("marketSummaries"), dict) else {}
    result["data"] = list(ranking_rows)
    result["filters"] = {**filters, "sortBy": sort_by}
    result["sort"] = {
        **sort,
        "key": sort_by,
        "label": radar_sort_label(sort_by),
        "legacy": False,
    }
    result["summary"] = {**summary, "returned": len(ranking_rows)}
    if isinstance(market_summaries.get(sort_by), dict):
        result["marketSummary"] = market_summaries[sort_by]
    return result


def radar_payload_with_cache_meta(
    payload: dict[str, Any], source: str, ts: int, warning: str = "", sort_by: str = ""
) -> dict[str, Any]:
    result = radar_payload_for_sort(payload, sort_by) if sort_by in RADAR_SORT_KEYS else normalize_radar_payload(payload)
    result["source"] = source
    result["ts"] = ts
    result["cacheAgeMs"] = max(0, now_ms() - ts)
    if warning:
        result["warning"] = warning
    return result


def save_radar_snapshot(cache_key: str, payload: dict[str, Any], ts: int) -> None:
    snapshot = {"cacheKey": cache_key, "ts": ts, "payload": payload}
    database.set_app_setting(RADAR_CACHE_KEY, json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), ts)
    with radar_cache_lock:
        radar_cache["cacheKey"] = cache_key
        radar_cache["payload"] = payload
        radar_cache["ts"] = ts


def load_radar_snapshot(cache_key: str = "") -> dict[str, Any] | None:
    with radar_cache_lock:
        cached_payload = radar_cache.get("payload")
        cached_ts = int(radar_cache.get("ts") or 0)
        cached_key = str(radar_cache.get("cacheKey") or "")
        if cached_payload and cached_ts and (not cache_key or cached_key == cache_key):
            return {"cacheKey": cached_key, "ts": cached_ts, "payload": cached_payload}

    raw = database.get_app_setting(RADAR_CACHE_KEY)
    if not raw:
        return None
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("payload"), dict):
        return None
    stored_key = str(snapshot.get("cacheKey") or "")
    if cache_key and stored_key != cache_key:
        return None
    ts = coerce_int(snapshot.get("ts"), 0, 0, 9_999_999_999_999)
    with radar_cache_lock:
        radar_cache["cacheKey"] = stored_key
        radar_cache["payload"] = snapshot["payload"]
        radar_cache["ts"] = ts
    return {"cacheKey": stored_key, "ts": ts, "payload": snapshot["payload"]}


def radar_candles(
    inst_id: str,
    bar: str,
    limit: int,
    *,
    require_hourly_quote_turnover: bool = True,
) -> list[dict[str, Any]]:
    cached = database.latest_candles(inst_id, bar, limit)
    completed = [item for item in cached if str(item.get("confirm", "1")) == "1"]
    has_hourly_quote_turnover = len(completed[-RADAR_ONE_HOUR_CANDLE_COUNT:]) == RADAR_ONE_HOUR_CANDLE_COUNT and all(
        (safe_decimal(item.get("volumeQuote")) or Decimal("0")) > 0
        for item in completed[-RADAR_ONE_HOUR_CANDLE_COUNT:]
    )
    cache_is_sufficient = bool(cached) and len(cached) >= min(20, limit)
    needs_hourly_quote_turnover = bar == "15m" and require_hourly_quote_turnover
    if cache_is_sufficient and (not needs_hourly_quote_turnover or has_hourly_quote_turnover):
        return cached
    try:
        rows = client.get_candles(inst_id, bar, limit)
    except OkxError as primary_error:
        message = str(primary_error).lower()
        is_transient = any(token in message for token in ("incompleteread", "incomplete", "remote end closed", "timeout"))
        if not is_transient:
            raise
        try:
            rows = client.get_history_candles(inst_id, bar, limit)
        except OkxError:
            # Keep the primary error so the caller can accurately classify the
            # refresh failure and retain its existing cached-data fallback.
            raise primary_error
    database.upsert_candles(inst_id, bar, rows)
    return rows


def radar_instruments() -> list[dict[str, Any]]:
    rows = database.list_instruments(query="", limit=500)
    if rows:
        return rows
    fresh = client.get_instruments()
    database.upsert_instruments(fresh, now_ms())
    return database.list_instruments(query="", limit=500)


def radar_metric_explanation(result: dict[str, Any]) -> dict[str, list[str]]:
    reasons = list(result.get("reasons") or [])
    warnings = list(result.get("warnings") or [])
    scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    if scores.get("opportunity", 0) >= 75:
        reasons.insert(0, "综合可交易性和波动性较突出，适合加入重点观察。")
    if scores.get("riskPenalty", 0) >= 30 and "风险扣分较高，实盘前需要复核成交量、盘口和止损空间。" not in warnings:
        warnings.append("风险扣分较高，实盘前需要复核成交量、盘口和止损空间。")
    return {"reasons": list(dict.fromkeys(reasons))[:4], "warnings": list(dict.fromkeys(warnings))[:6]}


def explain_radar_results_with_llm(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    config = stored_llm_config()
    if not config.get("enabled") or not config.get("baseUrl") or not config.get("model") or not config.get("apiKey"):
        return results, ""

    explain_rows = results[:RADAR_LLM_EXPLAIN_LIMIT]
    if not explain_rows:
        return results, ""
    prompt_payload = [
        {
            "instId": item["instId"],
            "scores": item.get("scores"),
            "riskLevel": item.get("riskLevel"),
            "volatilityLevel": item.get("volatilityLevel"),
            "metrics": {
                "volume24h": item.get("volume24h"),
                "range24hPct": item.get("range24hPct"),
                "change24hPct": item.get("change24hPct"),
                "recent20RangePct": item.get("metrics", {}).get("recent20RangePct"),
                "avgAbsReturnPct": item.get("metrics", {}).get("avgAbsReturnPct"),
                "volumeSpike": item.get("metrics", {}).get("volumeSpike"),
            },
            "currentReasons": item.get("reasons", []),
            "currentWarnings": item.get("warnings", []),
        }
        for item in explain_rows
    ]
    try:
        completion = llm_chat_completion(
            config,
            [
                {
                    "role": "system",
                    "content": (
                        "你是谨慎的合约雷达解释助手。只基于输入指标解释适合关注或风险点。"
                        "不要输出做多、做空、保证盈利、必须交易等措辞。只返回 JSON。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "instruction": (
                                "为每个合约生成简短 reasons 和 warnings。"
                                "格式：{\"items\":[{\"instId\":\"...\",\"reasons\":[\"...\"],\"warnings\":[\"...\"]}]}"
                            ),
                            "contracts": prompt_payload,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            request_type="contract_radar",
            context={"mode": "contract_radar", "inst_id": "MULTI", "bar": RADAR_DEFAULT_BAR},
        )
        parsed = extract_json_object(str(completion["content"]))
        items = parsed.get("items") if isinstance(parsed.get("items"), list) else []
        by_inst_id = {
            str(item.get("instId") or "").upper(): item for item in items if isinstance(item, dict) and item.get("instId")
        }
        next_results: list[dict[str, Any]] = []
        for result in results:
            updated = dict(result)
            llm_item = by_inst_id.get(str(result.get("instId") or "").upper())
            if llm_item:
                reasons = [str(item).strip() for item in llm_item.get("reasons", []) if str(item).strip()]
                warnings = [str(item).strip() for item in llm_item.get("warnings", []) if str(item).strip()]
                if reasons:
                    updated["reasons"] = reasons[:4]
                if warnings:
                    updated["warnings"] = list(dict.fromkeys((updated.get("warnings") or []) + warnings))[:6]
                updated["explainedBy"] = "llm"
            next_results.append(updated)
        return next_results, ""
    except Exception as exc:
        return results, f"AI 解释不可用，已显示指标解释：{str(exc)[:200]}"


def build_radar_scan(request: RadarScanRequest) -> dict[str, Any]:
    min_volume = safe_decimal(request.minVolume) or Decimal("0")
    instruments = [item for item in radar_instruments() if radar_filter_instrument(item, request)]
    ticker_payload = cached_tickers(force=False)
    ticker_rows = ticker_payload.get("data") if isinstance(ticker_payload.get("data"), list) else []
    tickers = {str(item.get("instId") or "").upper(): item for item in ticker_rows if isinstance(item, dict)}
    if not instruments or not tickers:
        return {
            "data": [],
            "filters": request.model_dump(),
            "summary": {"total": 0, "candidates": 0, "returned": 0, "explained": 0},
            "warning": "合约或 Ticker 行情数据不可用，暂时无法扫描合约雷达。",
        }

    initial_candidates = []
    for instrument in instruments:
        inst_id = str(instrument.get("inst_id") or "").upper()
        ticker = tickers.get(inst_id)
        liquidity = radar_liquidity(ticker, str(instrument.get("settle_ccy") or instrument.get("settleCcy") or ""))
        volume = liquidity.get("value") if isinstance(liquidity.get("value"), Decimal) else None
        if volume is not None and volume >= min_volume:
            initial_candidates.append((volume, instrument))
    initial_candidates.sort(key=lambda item: item[0], reverse=True)
    bounded_candidates = [item[1] for item in initial_candidates[: request.candidateLimit]]

    results: list[dict[str, Any]] = []
    candle_rows: dict[str, list[dict[str, Any]]] = {}
    candle_failures: dict[str, OkxError] = {}
    # Every manual scan prepares both turnover windows so the UI can switch
    # rankings locally without issuing another Radar or K-line request.
    require_hourly_quote_turnover = True
    with ThreadPoolExecutor(max_workers=min(RADAR_CANDLE_MAX_WORKERS, max(1, len(bounded_candidates)))) as executor:
        pending_candles = {
            str(instrument.get("inst_id") or "").upper(): executor.submit(
                radar_candles,
                str(instrument.get("inst_id") or "").upper(),
                request.bar,
                RADAR_CANDLE_LIMIT,
                require_hourly_quote_turnover=require_hourly_quote_turnover,
            )
            for instrument in bounded_candidates
        }
        for inst_id, future in pending_candles.items():
            try:
                candle_rows[inst_id] = future.result()
            except OkxError as exc:
                candle_failures[inst_id] = exc

    # A closed connection from the public API is often transient. Retry only
    # the items that already exhausted the client's bounded retry policy, and
    # do so at a lower concurrency so a scan does not amplify the burst.
    if candle_failures:
        with ThreadPoolExecutor(
            max_workers=min(RADAR_CANDLE_RECOVERY_MAX_WORKERS, len(candle_failures))
        ) as executor:
            recovery_candles = {
                inst_id: executor.submit(
                    radar_candles,
                    inst_id,
                    request.bar,
                    RADAR_CANDLE_LIMIT,
                    require_hourly_quote_turnover=require_hourly_quote_turnover,
                )
                for inst_id in candle_failures
            }
            for inst_id, future in recovery_candles.items():
                try:
                    candle_rows[inst_id] = future.result()
                    candle_failures.pop(inst_id, None)
                except OkxError as exc:
                    candle_failures[inst_id] = exc

    warnings = [radar_refresh_warning(inst_id, exc) for inst_id, exc in candle_failures.items()]
    if candle_failures:
        failed_details = ", ".join(
            f"{inst_id}: {str(exc)[:160]}" for inst_id, exc in list(candle_failures.items())[:8]
        )
        logger.warning(
            "Radar K-line refresh used cached or degraded data for %s/%s candidates after recovery: %s",
            len(candle_failures),
            len(bounded_candidates),
            failed_details,
        )
    for inst_id in candle_failures:
        candle_rows[inst_id] = database.latest_candles(inst_id, request.bar, RADAR_CANDLE_LIMIT)

    for instrument in bounded_candidates:
        inst_id = str(instrument.get("inst_id") or "").upper()
        candles = candle_rows.get(inst_id, [])
        result = score_radar_contract(instrument, tickers.get(inst_id), candles, min_volume)
        result["bar"] = request.bar
        explanation = radar_metric_explanation(result)
        result["reasons"] = explanation["reasons"]
        result["warnings"] = explanation["warnings"]
        if radar_result_matches_filters(result, request):
            results.append(result)

    ranked_results = {
        sort_key: sorted(results, key=lambda item: radar_result_sort_key(item, sort_key))
        for sort_key in sorted(RADAR_SORT_KEYS)
    }
    rankings = {sort_key: rows[: request.limit] for sort_key, rows in ranked_results.items()}
    results = list(rankings[request.sortBy])
    llm_warning = ""
    if request.explain:
        results, llm_warning = explain_radar_results_with_llm(results)
        rankings[request.sortBy] = results
    warning_parts = [radar_refresh_warning_summary(warnings)] if warnings else []
    if llm_warning:
        warning_parts.append(llm_warning)
    warning_text = "；".join(warning_parts)
    payload = {
        "schemaVersion": RADAR_SCHEMA_VERSION,
        "data": results,
        "rankings": rankings,
        "filters": request.model_dump(),
        "sort": {
            "key": request.sortBy,
            "label": radar_sort_label(request.sortBy),
            "candidateScope": "按已筛选的高流动性候选池排行，不代表全市场总榜。",
            "legacy": False,
        },
        "summary": {
            "total": len(instruments),
            "candidates": len(bounded_candidates),
            "returned": len(results),
            "explained": sum(1 for item in results if item.get("explainedBy") == "llm"),
        },
        "warning": warning_text,
    }
    market_summaries: dict[str, dict[str, Any]] = {}
    for sort_key, ranked_rows in ranked_results.items():
        summary_payload = {
            **payload,
            "data": rankings[sort_key],
            "filters": {**request.model_dump(), "sortBy": sort_key},
            "sort": {**payload["sort"], "key": sort_key, "label": radar_sort_label(sort_key)},
            "summary": {**payload["summary"], "returned": len(rankings[sort_key])},
        }
        market_summaries[sort_key] = build_radar_market_summary(summary_payload, ranked_rows)
    payload["marketSummaries"] = market_summaries
    payload["marketSummary"] = market_summaries[request.sortBy]
    return payload


def cached_radar_scan(request: RadarScanRequest, force: bool = False) -> dict[str, Any]:
    cache_key = radar_request_key(request)
    now = now_ms()
    snapshot = load_radar_snapshot(cache_key)
    if not force and snapshot:
        age_ms = now - int(snapshot["ts"])
        if age_ms <= RADAR_CACHE_SECONDS * 1000:
            return radar_payload_with_cache_meta(
                snapshot["payload"], "radar-cache", int(snapshot["ts"]), sort_by=request.sortBy
            )

    try:
        payload = build_radar_scan(request)
        ts = now_ms()
        save_radar_snapshot(cache_key, payload, ts)
        return radar_payload_with_cache_meta(
            payload, "okx-radar", ts, str(payload.get("warning") or ""), sort_by=request.sortBy
        )
    except OkxError as exc:
        fallback = snapshot or load_radar_snapshot()
        if fallback:
            return radar_payload_with_cache_meta(
                fallback["payload"],
                "radar-stale-cache",
                int(fallback["ts"]),
                "雷达暂时无法更新，正在显示最近一次缓存；可稍后重新扫描。",
                sort_by=request.sortBy,
            )
        return {
            "data": [],
            "filters": request.model_dump(),
            "summary": {"total": 0, "candidates": 0, "returned": 0, "explained": 0},
            "source": "okx-unavailable",
            "warning": "合约雷达暂时无法读取行情，请稍后重新扫描。",
            "ts": now_ms(),
            "cacheAgeMs": None,
        }


def normalize_market_stats_inst_id(inst_id: str) -> str:
    normalized = inst_id.strip().upper()
    if not normalized.endswith("-SWAP") or not normalized.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="行情交易统计当前仅支持 OKX SWAP 合约。")
    return normalized


def normalize_market_stats_period(period: str) -> str:
    normalized = period.strip() or MARKET_STATS_DEFAULT_PERIOD
    return normalized if normalized in MARKET_STATS_SUPPORTED_PERIODS else MARKET_STATS_DEFAULT_PERIOD


def market_stats_request_key(inst_id: str, period: str, limit: int) -> str:
    return json.dumps(
        {"instId": inst_id, "period": period, "limit": limit, "schemaVersion": 1},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def market_stats_metric_key(inst_id: str, period: str, limit: int, metric_key: str) -> str:
    return json.dumps(
        {"instId": inst_id, "period": period, "limit": limit, "metric": metric_key, "schemaVersion": 1},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def market_stats_metric_error_text(exc: OkxError) -> str:
    message = str(exc)
    lowered = message.lower()
    if "incompleteread" in lowered or "incomplete" in lowered:
        return "OKX 本次返回中断，已重试"
    if "remotedisconnected" in lowered or "remote end closed connection" in lowered:
        return "OKX 连接提前关闭，已重试"
    if "timed out" in lowered or "timeout" in lowered:
        return "OKX 请求超时，已重试"
    return message


def read_market_stats_metric_cache(inst_id: str, period: str, limit: int, metric_key: str) -> tuple[dict[str, Any] | None, int]:
    cache_key = market_stats_metric_key(inst_id, period, limit, metric_key)
    with market_stats_cache_lock:
        cached = market_stats_metric_cache.get(cache_key)
        if not cached:
            return None, 0
        return deepcopy(cached.get("payload")), int(cached.get("ts") or 0)


def write_market_stats_metric_cache(inst_id: str, period: str, limit: int, metric_key: str, payload: dict[str, Any], ts: int) -> None:
    cache_key = market_stats_metric_key(inst_id, period, limit, metric_key)
    with market_stats_cache_lock:
        market_stats_metric_cache[cache_key] = {"payload": deepcopy(payload), "ts": ts}


def decimal_text_or_empty(value: Any) -> str:
    numeric = safe_decimal(value)
    return decimal_display(numeric) if numeric is not None else ""


def percent_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    return decimal_display_fixed(value, 2)


def safe_ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def sorted_stat_rows(rows: list[list[str]], minimum_length: int) -> list[list[str]]:
    valid_rows = [row for row in rows if isinstance(row, list) and len(row) >= minimum_length and safe_decimal(row[0]) is not None]
    return sorted(valid_rows, key=lambda row: safe_decimal(row[0]) or Decimal("0"))


def long_short_bias(ratio: Decimal | None) -> str:
    if ratio is None:
        return "unavailable"
    if ratio >= Decimal("1.05"):
        return "more_long_accounts"
    if ratio <= Decimal("0.95"):
        return "more_short_accounts"
    return "balanced_accounts"


def taker_dominance(buy_share_pct: Decimal | None) -> str:
    if buy_share_pct is None:
        return "unavailable"
    if buy_share_pct >= Decimal("55"):
        return "active_buying_stronger"
    if buy_share_pct <= Decimal("45"):
        return "active_selling_stronger"
    return "balanced_taker_flow"


def open_interest_trend(change_pct: Decimal | None) -> str:
    if change_pct is None:
        return "unavailable"
    if change_pct >= Decimal("1"):
        return "increasing"
    if change_pct <= Decimal("-1"):
        return "decreasing"
    return "flat"


def normalize_long_short_account_ratio(rows: list[list[str]]) -> dict[str, Any]:
    points = [
        {"ts": int(safe_decimal(row[0]) or 0), "ratio": decimal_text_or_empty(row[1])}
        for row in sorted_stat_rows(rows, 2)
        if decimal_text_or_empty(row[1])
    ]
    latest_point = points[-1] if points else None
    latest_ratio = safe_decimal(latest_point.get("ratio")) if latest_point else None
    return {
        "latest": latest_point.get("ratio") if latest_point else "",
        "latestTs": latest_point.get("ts") if latest_point else 0,
        "bias": long_short_bias(latest_ratio),
        "points": points,
    }


def normalize_taker_volume(rows: list[list[str]]) -> dict[str, Any]:
    points: list[dict[str, Any]] = []
    for row in sorted_stat_rows(rows, 3):
        sell_vol = safe_decimal(row[1])
        buy_vol = safe_decimal(row[2])
        total_vol = (sell_vol or Decimal("0")) + (buy_vol or Decimal("0"))
        buy_share_pct = buy_vol / total_vol * Decimal("100") if buy_vol is not None and total_vol > 0 else None
        buy_sell_ratio = safe_ratio(buy_vol, sell_vol)
        points.append(
            {
                "ts": int(safe_decimal(row[0]) or 0),
                "sellVol": decimal_display(sell_vol) if sell_vol is not None else "",
                "buyVol": decimal_display(buy_vol) if buy_vol is not None else "",
                "totalVol": decimal_display(total_vol) if total_vol > 0 else "",
                "buySharePct": percent_text(buy_share_pct),
                "buySellRatio": decimal_display_fixed(buy_sell_ratio, 2) if buy_sell_ratio is not None else "",
            }
        )
    latest_point = points[-1] if points else None
    latest_buy_share = safe_decimal(latest_point.get("buySharePct")) if latest_point else None
    return {
        "latestTs": latest_point.get("ts") if latest_point else 0,
        "sellVol": latest_point.get("sellVol") if latest_point else "",
        "buyVol": latest_point.get("buyVol") if latest_point else "",
        "totalVol": latest_point.get("totalVol") if latest_point else "",
        "buySharePct": latest_point.get("buySharePct") if latest_point else "",
        "buySellRatio": latest_point.get("buySellRatio") if latest_point else "",
        "dominance": taker_dominance(latest_buy_share),
        "unit": "USDT",
        "points": points,
    }


def open_interest_value(point: dict[str, Any]) -> Decimal | None:
    for key in ["oiUsd", "oiCcy", "oi"]:
        value = safe_decimal(point.get(key))
        if value is not None:
            return value
    return None


def normalize_open_interest_history(rows: list[list[str]]) -> dict[str, Any]:
    points = [
        {
            "ts": int(safe_decimal(row[0]) or 0),
            "oi": decimal_text_or_empty(row[1]),
            "oiCcy": decimal_text_or_empty(row[2]) if len(row) > 2 else "",
            "oiUsd": decimal_text_or_empty(row[3]) if len(row) > 3 else "",
        }
        for row in sorted_stat_rows(rows, 2)
    ]
    latest_point = points[-1] if points else None
    first_value = open_interest_value(points[0]) if points else None
    latest_value = open_interest_value(latest_point) if latest_point else None
    change = latest_value - first_value if latest_value is not None and first_value is not None else None
    change_pct = change / first_value * Decimal("100") if change is not None and first_value and first_value > 0 else None
    return {
        "latestTs": latest_point.get("ts") if latest_point else 0,
        "oi": latest_point.get("oi") if latest_point else "",
        "oiCcy": latest_point.get("oiCcy") if latest_point else "",
        "oiUsd": latest_point.get("oiUsd") if latest_point else "",
        "change": decimal_display(change) if change is not None else "",
        "changePct": percent_text(change_pct),
        "trend": open_interest_trend(change_pct),
        "points": points,
    }


def empty_market_stats_payload(inst_id: str, requested_period: str, period: str, limit: int, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "instId": inst_id,
        "requestedPeriod": requested_period,
        "period": period,
        "limit": limit,
        "longShortAccountRatio": {"latest": "", "latestTs": 0, "bias": "unavailable", "points": []},
        "takerVolume": {
            "latestTs": 0,
            "sellVol": "",
            "buyVol": "",
            "totalVol": "",
            "buySharePct": "",
            "buySellRatio": "",
            "dominance": "unavailable",
            "unit": "USDT",
            "points": [],
        },
        "openInterest": {"latestTs": 0, "oi": "", "oiCcy": "", "oiUsd": "", "change": "", "changePct": "", "trend": "unavailable", "points": []},
        "warnings": warnings or [],
    }


def build_market_stats(inst_id: str, requested_period: str, period: str, limit: int) -> dict[str, Any]:
    payload = empty_market_stats_payload(inst_id, requested_period, period, limit)
    metric_ts = now_ms()
    metric_calls = [
        (
            "longShortAccountRatio",
            "多空人数比",
            lambda: normalize_long_short_account_ratio(client.get_contract_long_short_account_ratio(inst_id, period, limit)),
        ),
        (
            "takerVolume",
            "主动买卖量",
            lambda: normalize_taker_volume(client.get_contract_taker_volume(inst_id, period, limit, unit="2")),
        ),
        (
            "openInterest",
            "持仓量",
            lambda: normalize_open_interest_history(client.get_contract_open_interest_history(inst_id, period, limit)),
        ),
    ]
    for key, label, loader in metric_calls:
        try:
            metric_payload = loader()
            payload[key] = metric_payload
            write_market_stats_metric_cache(inst_id, period, limit, key, metric_payload, metric_ts)
        except OkxError as exc:
            cached_metric, cached_ts = read_market_stats_metric_cache(inst_id, period, limit, key)
            error_text = market_stats_metric_error_text(exc)
            if cached_metric:
                payload[key] = cached_metric
                cache_time = time.strftime("%H:%M:%S", time.localtime(cached_ts / 1000)) if cached_ts else "--"
                payload["warnings"].append(f"{label}本次刷新失败，显示上次缓存 {cache_time}：{error_text}")
            else:
                payload["warnings"].append(f"{label}本次刷新失败，暂无可用缓存：{error_text}")
    return payload


def market_stats_with_cache_meta(payload: dict[str, Any], source: str, ts: int, warning: str = "") -> dict[str, Any]:
    result = dict(payload)
    result["source"] = source
    result["ts"] = ts
    result["cacheAgeMs"] = max(0, now_ms() - ts)
    warnings = [str(item) for item in result.get("warnings") or [] if str(item)]
    if warning:
        warnings.insert(0, warning)
    result["warnings"] = list(dict.fromkeys(warnings))
    return result


def cached_market_stats(inst_id: str, requested_period: str, period: str, limit: int, force: bool = False) -> dict[str, Any]:
    cache_key = market_stats_request_key(inst_id, period, limit)
    now = now_ms()
    with market_stats_cache_lock:
        cached_payload = market_stats_cache.get("payload")
        cached_ts = int(market_stats_cache.get("ts") or 0)
        cached_key = str(market_stats_cache.get("cacheKey") or "")
        if not force and cached_payload and cached_key == cache_key and cached_ts:
            age_ms = now - cached_ts
            if age_ms <= MARKET_STATS_CACHE_SECONDS * 1000:
                payload = dict(cached_payload)
                payload["requestedPeriod"] = requested_period
                return market_stats_with_cache_meta(payload, "market-stats-cache", cached_ts)

    try:
        payload = build_market_stats(inst_id, requested_period, period, limit)
        ts = now_ms()
        with market_stats_cache_lock:
            market_stats_cache["cacheKey"] = cache_key
            market_stats_cache["payload"] = payload
            market_stats_cache["ts"] = ts
        source = "okx-market-stats-partial" if payload.get("warnings") else "okx-market-stats"
        return market_stats_with_cache_meta(payload, source, ts)
    except OkxError as exc:
        with market_stats_cache_lock:
            cached_payload = market_stats_cache.get("payload")
            cached_ts = int(market_stats_cache.get("ts") or 0)
            cached_key = str(market_stats_cache.get("cacheKey") or "")
            if cached_payload and cached_key == cache_key and cached_ts:
                payload = dict(cached_payload)
                payload["requestedPeriod"] = requested_period
                return market_stats_with_cache_meta(payload, "market-stats-stale-cache", cached_ts, f"交易统计刷新失败，显示缓存：{str(exc)}")
        return market_stats_with_cache_meta(
            empty_market_stats_payload(inst_id, requested_period, period, limit, [f"交易统计不可用：{str(exc)}"]),
            "okx-market-stats-unavailable",
            now_ms(),
        )


def http_json_request(url: str, method: str = "GET", body: dict[str, Any] | None = None, timeout: float = 8) -> dict[str, Any]:
    data = json.dumps(body or {}, ensure_ascii=False, separators=(",", ":")).encode("utf-8") if body is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "okx-dashboard-market-ai/0.1",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("响应不是 JSON 对象。")
    return payload


class OfficialSourceError(RuntimeError):
    """An official-source error that is safe to surface on the timeline."""

    def __init__(self, public_message: str, detail: str = ""):
        super().__init__(detail or public_message)
        self.public_message = public_message


def official_source_error(exc: Exception) -> OfficialSourceError:
    if isinstance(exc, OfficialSourceError):
        return exc
    if isinstance(exc, HTTPError):
        if exc.code == 403:
            return OfficialSourceError("官方站点拒绝当前服务请求", f"HTTP {exc.code}")
        if exc.code == 404:
            return OfficialSourceError("官方地址暂不可用", f"HTTP {exc.code}")
        return OfficialSourceError("官方站点暂时不可用", f"HTTP {exc.code}")
    if isinstance(exc, IncompleteRead):
        return OfficialSourceError("官方响应中断，稍后会自动重试", "incomplete response")
    if isinstance(exc, (URLError, TimeoutError, OSError)):
        return OfficialSourceError("暂时无法连接官方站点", type(exc).__name__)
    return OfficialSourceError("官方响应格式异常", type(exc).__name__)


def http_text_request(url: str, timeout: float = 10, retries: int = 2) -> str:
    """Fetch small official calendars without exposing transport errors to users."""
    last_error: OfficialSourceError | None = None
    for attempt in range(max(1, retries)):
        try:
            request = Request(url, headers={
                "Accept": "text/html,application/xhtml+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "identity",
                "User-Agent": "OKX Quant official calendar reader/1.0",
            })
            with urlopen(request, timeout=timeout) as response:
                content = response.read(2_000_001)
            if len(content) > 2_000_000:
                raise OfficialSourceError("官方响应过大，暂不加载", "response exceeded 2 MB")
            return content.decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = official_source_error(exc)
            # A rejection or an invalid path will not improve with an immediate retry.
            if isinstance(exc, HTTPError) and exc.code in {403, 404}:
                break
            if attempt + 1 < max(1, retries):
                time.sleep(0.2 * (attempt + 1))
    raise last_error or OfficialSourceError("官方日历暂不可用")


def market_ai_source_item(
    source: str,
    title: str,
    url: str,
    summary: str,
    kind: str,
    value: str = "",
    previous_value: str = "",
    published_at: str = "",
    scheduled_at: str = "",
    official: bool = True,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "kind": kind,
        "title": title,
        "url": url,
        "publishedAt": published_at,
        "scheduledAt": scheduled_at,
        "value": value,
        "previousValue": previous_value,
        "summary": summary[:600],
        "official": official,
        "cacheAgeMs": 0,
        "warnings": warnings or [],
    }


def market_ai_macro_cache_get(key: str) -> tuple[dict[str, Any] | None, int]:
    with market_ai_macro_cache_lock:
        cached = market_ai_macro_cache.get(key)
        if not cached:
            return None, 0
        return deepcopy(cached.get("payload")), int(cached.get("ts") or 0)


def market_ai_macro_cache_set(key: str, payload: dict[str, Any], ts: int) -> None:
    with market_ai_macro_cache_lock:
        market_ai_macro_cache[key] = {"payload": deepcopy(payload), "ts": ts}


def market_ai_cache_age(ts: int) -> int | None:
    return max(0, now_ms() - ts) if ts else None


def with_market_ai_cache_meta(payload: dict[str, Any], source: str, ts: int, warning: str = "") -> dict[str, Any]:
    result = deepcopy(payload)
    result["source"] = source
    result["ts"] = ts
    result["cacheAgeMs"] = market_ai_cache_age(ts)
    age_ms = result["cacheAgeMs"]
    for item in result.get("items", []):
        if isinstance(item, dict):
            item["cacheAgeMs"] = age_ms
    warnings = [str(item) for item in result.get("warnings") or [] if str(item)]
    if warning:
        warnings.insert(0, warning)
    result["warnings"] = list(dict.fromkeys(warnings))
    return result


def bls_cpi_period_label(row: dict[str, Any]) -> str:
    period_name = str(row.get("periodName") or "").strip()
    year = str(row.get("year") or "").strip()
    return f"{year} {period_name}".strip() or year


def load_cpi_evidence(force: bool = False) -> dict[str, Any]:
    cache_key = "bls-cpi-cu"
    now = now_ms()
    cached_payload, cached_ts = market_ai_macro_cache_get(cache_key)
    if cached_payload and cached_ts and not force and now - cached_ts <= MARKET_AI_MACRO_CACHE_SECONDS * 1000:
        return with_market_ai_cache_meta(cached_payload, "macro-cache", cached_ts)

    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0"
    year = time.gmtime(now / 1000).tm_year
    try:
        payload = http_json_request(
            url,
            method="POST",
            body={"seriesid": ["CUUR0000SA0"], "startyear": str(year - 1), "endyear": str(year)},
        )
        results = payload.get("Results") if isinstance(payload.get("Results"), dict) else {}
        series = results.get("series") if isinstance(results.get("series"), list) else []
        rows = series[0].get("data") if series and isinstance(series[0], dict) and isinstance(series[0].get("data"), list) else []
        if not rows:
            raise ValueError("BLS CPI 返回为空。")
        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else {}
        latest_value = str(latest.get("value") or "").strip()
        previous_value = str(previous.get("value") or "").strip()
        period = bls_cpi_period_label(latest)
        summary = f"美国 CPI-U 最新可用读数 {period} 为 {latest_value}"
        if previous_value:
            summary += f"，前值 {previous_value}"
        cpi_item = market_ai_source_item(
            "BLS",
            "US CPI-U 最新读数",
            url,
            summary,
            "cpi",
            value=latest_value,
            previous_value=previous_value,
            published_at=period,
            official=True,
        )
        schedule_item = market_ai_source_item(
            "BLS",
            "CPI 新闻发布时间表",
            "https://www.bls.gov/schedule/news_release/cpi.htm",
            "CPI 发布时间需要以 BLS 新闻发布日历为准；当前接口只提供最新已发布读数。",
            "cpi_schedule",
            official=True,
        )
        result = {"items": [cpi_item, schedule_item], "warnings": []}
        market_ai_macro_cache_set(cache_key, result, now_ms())
        return with_market_ai_cache_meta(result, "bls-cpi", now_ms())
    except Exception as exc:
        if cached_payload and cached_ts and now - cached_ts <= MARKET_AI_MACRO_STALE_SECONDS * 1000:
            return with_market_ai_cache_meta(cached_payload, "macro-stale-cache", cached_ts, f"BLS CPI 刷新失败，使用旧缓存：{str(exc)[:160]}")
        return with_market_ai_cache_meta(
            {
                "items": [
                    market_ai_source_item(
                        "BLS",
                        "US CPI-U 最新读数",
                        url,
                        "BLS CPI 官方数据暂不可用，AI 不会使用未验证的最新 CPI 数值。",
                        "cpi",
                        official=True,
                        warnings=[f"BLS CPI 获取失败：{str(exc)[:160]}"],
                    )
                ],
                "warnings": [f"BLS CPI 获取失败：{str(exc)[:160]}"],
            },
            "macro-unavailable",
            now_ms(),
        )


def fed_calendar_dates(text: str) -> list[str]:
    candidates = re.findall(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:-\d{1,2})?,\s+20\d{2}", text, flags=re.I)
    return list(dict.fromkeys(item.strip() for item in candidates))[:6]


def load_fed_evidence(force: bool = False) -> dict[str, Any]:
    cache_key = "fed-fomc-calendar"
    now = now_ms()
    cached_payload, cached_ts = market_ai_macro_cache_get(cache_key)
    if cached_payload and cached_ts and not force and now - cached_ts <= MARKET_AI_MACRO_CACHE_SECONDS * 1000:
        return with_market_ai_cache_meta(cached_payload, "macro-cache", cached_ts)

    calendar_url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    policy_url = "https://www.federalreserve.gov/economy-at-a-glance-policy-rate.htm"
    try:
        calendar_text = http_text_request(calendar_url)
        dates = fed_calendar_dates(calendar_text)
        summary = "FOMC 会议日程已从 Federal Reserve 公共页面读取。"
        scheduled_at = "；".join(dates[:3])
        if scheduled_at:
            summary += f" 页面中识别到的近期会议日期：{scheduled_at}。"
        else:
            summary += " 本次未能从页面中稳定抽取具体日期，请打开来源核对。"
        result = {
            "items": [
                market_ai_source_item(
                    "Federal Reserve",
                    "FOMC meeting calendar",
                    calendar_url,
                    summary,
                    "fomc_schedule",
                    scheduled_at=scheduled_at,
                    official=True,
                    warnings=[] if scheduled_at else ["未稳定抽取会议日期，仅保留官方页面来源。"],
                ),
                market_ai_source_item(
                    "Federal Reserve",
                    "Federal funds target range",
                    policy_url,
                    "政策利率上下限以 Federal Reserve 官方政策利率页面为准；本版本只提供来源引用，不伪造实时利率数值。",
                    "policy_rate",
                    official=True,
                ),
            ],
            "warnings": [] if scheduled_at else ["FOMC 日期抽取不完整，请核对官方日历。"],
        }
        market_ai_macro_cache_set(cache_key, result, now_ms())
        return with_market_ai_cache_meta(result, "fed-calendar", now_ms())
    except Exception as exc:
        if cached_payload and cached_ts and now - cached_ts <= MARKET_AI_MACRO_STALE_SECONDS * 1000:
            return with_market_ai_cache_meta(cached_payload, "macro-stale-cache", cached_ts, f"Fed 日历刷新失败，使用旧缓存：{str(exc)[:160]}")
        return with_market_ai_cache_meta(
            {
                "items": [
                    market_ai_source_item(
                        "Federal Reserve",
                        "FOMC meeting calendar",
                        calendar_url,
                        "Federal Reserve 官方日历暂不可用，AI 不会使用未验证的加息/降息事件。",
                        "fomc_schedule",
                        official=True,
                        warnings=[f"Fed 日历获取失败：{str(exc)[:160]}"],
                    ),
                    market_ai_source_item(
                        "Federal Reserve",
                        "Federal funds target range",
                        policy_url,
                        "政策利率官方页面来源保留；本次未能实时读取数值。",
                        "policy_rate",
                        official=True,
                    ),
                ],
                "warnings": [f"Fed 日历获取失败：{str(exc)[:160]}"],
            },
            "macro-unavailable",
            now_ms(),
        )


def load_market_expectation_evidence(force: bool = False) -> dict[str, Any]:
    return with_market_ai_cache_meta(
        {
            "items": [
                market_ai_source_item(
                    "Market expectation provider",
                    "利率预期扩展位",
                    "",
                    "第一版未启用市场隐含加息/降息概率源；如后续接入 CME FedWatch 等来源，必须标注为市场预期而非官方政策。",
                    "rate_expectation",
                    official=False,
                    warnings=["市场隐含利率概率源未启用。"],
                )
            ],
            "warnings": ["市场隐含利率概率源未启用。"],
        },
        "expectation-disabled",
        now_ms(),
    )


def build_market_ai_macro_snapshot(force: bool = False) -> dict[str, Any]:
    providers = [load_cpi_evidence, load_fed_evidence, load_market_expectation_evidence]
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    sources: list[str] = []
    for loader in providers:
        payload = loader(force)
        items.extend([item for item in payload.get("items", []) if isinstance(item, dict)])
        warnings.extend(str(item) for item in payload.get("warnings") or [] if str(item))
        source = str(payload.get("source") or "")
        if source:
            sources.append(source)
    return {
        "items": items,
        "warnings": list(dict.fromkeys(warnings)),
        "sources": list(dict.fromkeys(sources)),
        "generatedAt": now_ms(),
        "source": "macro-partial" if warnings else "macro-public",
    }


def us_event_timestamp(value: str, time_value: str = "") -> int | None:
    """Parse only dates/times explicitly supplied by an official U.S. source."""
    cleaned = re.sub(r"\s+", " ", re.sub(r"\bSept\.?\b", "Sep", value)).strip(" ,")
    for date_format in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(cleaned, date_format)
            if time_value:
                clock = datetime.strptime(time_value.strip().upper(), "%I:%M %p")
                parsed = parsed.replace(hour=clock.hour, minute=clock.minute)
            # Date-only records are intentionally stored at local noon for date-window browsing;
            # `timeKnown` remains false in the public representation.
            return int(parsed.replace(hour=parsed.hour if time_value else 12, tzinfo=ZoneInfo(US_EVENT_TIMEZONE)).timestamp() * 1000)
        except ValueError:
            continue
    return None


def us_event_candidate(provider: str, key: str, title: str, category: str, source_url: str, scheduled_at: int | None, *, time_known: bool, summary: str = "", importance: str = "high", state: str = "scheduled", actual: str = "", previous: str = "", unit: str = "", period_label: str = "") -> dict[str, Any]:
    fetched_at = now_ms()
    payload = {"provider": provider, "key": key, "title": title, "category": category, "scheduledAt": scheduled_at, "timeKnown": time_known, "state": state, "actual": actual, "previous": previous, "unit": unit, "periodLabel": period_label, "summary": summary}
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"okx-us-event:{provider}:{key}")), "provider": provider, "provider_event_key": key,
        "title": title, "category": category, "importance": importance, "state": state, "scheduled_at": scheduled_at,
        "source_timezone": US_EVENT_TIMEZONE, "published_at": fetched_at if state in {"released", "revised"} else None,
        "fetched_at": fetched_at, "actual": actual or None, "forecast": None, "previous_value": previous or None,
        "revision": None, "unit": unit or None, "period_label": period_label or None, "source_url": source_url,
        "source_summary": json.dumps({**payload, "timeKnown": time_known}, ensure_ascii=False), "official": True,
        "payload_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
    }


def parse_us_event_schedule(text: str, provider: str, source_url: str, patterns: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Normalize each official date/title entry without cross-date matching.

    The BLS calendar can render an entire calendar week inside one ``<tr>``.
    A row-wide scan then lets a later release title leak into an earlier day.
    Prefer individual table cells, fall back to a row only when it has one
    explicit date, and use date-bounded text segments only for plain fixtures.
    """
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    date_re = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*,?\s*((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+20\d{2})\s*(\d{1,2}:\d{2}\s*(?:AM|PM))?", re.I)

    def normalized(raw_entry: str) -> str:
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", raw_entry)).replace("\xa0", " ").replace("|", " ")).strip()

    def add_candidates(entry: str, *, allow_multiple_dates: bool) -> int:
        matches = list(date_re.finditer(entry))
        if not matches or (len(matches) > 1 and not allow_multiple_dates):
            return 0
        added = 0
        for index, match in enumerate(matches):
            next_start = matches[index + 1].start() if index + 1 < len(matches) else len(entry)
            # For a plain-text fixture, the next explicit date is a hard
            # boundary. For a table cell, the whole cell is one official item.
            excerpt = entry[match.start():next_start] if allow_multiple_dates else entry
            for needle, category in patterns:
                if needle.lower() not in excerpt.lower():
                    continue
                stamp = us_event_timestamp(match.group(1), match.group(2) or "")
                if stamp is None:
                    continue
                key = f"{needle.lower().replace(' ', '-')}-{datetime.fromtimestamp(stamp / 1000, tz=timezone.utc).date().isoformat()}"
                if key in seen:
                    continue
                found.append(us_event_candidate(provider, key, needle, category, source_url, stamp, time_known=bool(match.group(2)), summary=f"{provider} 官方日程。"))
                seen.add(key)
                added += 1
        return added

    raw_rows = re.findall(r"<tr\b[^>]*>(.*?)</tr\s*>", text, flags=re.I | re.S)
    if raw_rows:
        for raw_row in raw_rows:
            cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]\s*>", raw_row, flags=re.I | re.S)
            added = sum(add_candidates(normalized(cell), allow_multiple_dates=False) for cell in cells)
            # Some accessible tables put the date in one cell and the title in
            # another. A single-date row remains unambiguous; a calendar-week
            # row deliberately does not fall back to a cross-cell guess.
            if not added:
                add_candidates(normalized(raw_row), allow_multiple_dates=False)
    else:
        raw_entries = re.findall(r"<(?:li|article)\b[^>]*>(.*?)</(?:li|article)\s*>", text, flags=re.I | re.S)
        entries = raw_entries or [text]
        for raw_entry in entries:
            add_candidates(normalized(raw_entry), allow_multiple_dates=True)
    return found


def load_fed_timeline_events() -> list[dict[str, Any]]:
    url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    return parse_fed_timeline_events(http_text_request(url), url)


def parse_fed_timeline_events(text: str, source_url: str) -> list[dict[str, Any]]:
    """Extract only FOMC sub-events that the Fed calendar explicitly labels.

    The calendar is a date-oriented publication, so this deliberately emits
    date-only candidates. It must not imply an intraday release time merely
    because one is customary.
    """
    plain = re.sub(r"<[^>]+>", " ", text).replace("&nbsp;", " ")
    plain = re.sub(r"\s+", " ", plain)
    date_pattern = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:\s*[-–]\s*\d{1,2})?,\s+20\d{2}"
    date_matches = list(re.finditer(date_pattern, plain, flags=re.I))
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, match in enumerate(date_matches):
        item = match.group(0)
        next_start = date_matches[index + 1].start() if index + 1 < len(date_matches) else len(plain)
        context = plain[match.end():next_start]
        # A standalone minutes-release date is not a meeting. Treat a date as
        # a meeting only when its own calendar segment labels meeting material.
        if not re.search(r"\b(FOMC|meeting|statement|press conference|projection materials)\b", context, re.I):
            continue
        # The calendar gives meeting dates but not a stable universal timestamp, so keep date-only state.
        first_day = re.sub(r"\s*[-–]\s*\d{1,2}", "", item.split(",")[0]) + "," + item.split(",", 1)[1]
        stamp = us_event_timestamp(first_day)
        if not stamp:
            continue
        date_key = datetime.fromtimestamp(stamp / 1000, tz=timezone.utc).date().isoformat()
        has_statement = bool(re.search(r"\bstatement\b", context, re.I))
        candidates = [
            ("fomc-policy-decision", "美联储利率决策（美国）", "Federal Reserve 官方日历标注 FOMC Statement。")
        ] if has_statement else [
            ("fomc-meeting", "FOMC 会议（美国）", "Federal Reserve 官方 FOMC 日历。")
        ]
        if re.search(r"\bpress conference\b", context, re.I):
            candidates.append(("fomc-press-conference", "美联储新闻发布会（美国）", "Federal Reserve 官方日历标注 Press Conference。"))
        if re.search(r"\bprojection materials\b|\bSEP\b", context, re.I):
            candidates.append(("fomc-sep", "FOMC 经济预测（美国）", "Federal Reserve 官方日历标注 Projection Materials/SEP。"))
        for kind, title, summary in candidates:
            key = f"{kind}-{date_key}"
            if key not in seen:
                events.append(us_event_candidate("Federal Reserve", key, title, "monetary", source_url, stamp, time_known=False, summary=summary))
                seen.add(key)

    minutes_re = re.compile(r"\bMinutes\b.{0,180}?(?:released?|release date)\s*[:\-]?\s*(" + date_pattern + r")", re.I)
    for match in minutes_re.finditer(plain):
        stamp = us_event_timestamp(match.group(1))
        if not stamp:
            continue
        key = f"fomc-minutes-{datetime.fromtimestamp(stamp / 1000, tz=timezone.utc).date().isoformat()}"
        if key not in seen:
            events.append(us_event_candidate("Federal Reserve", key, "FOMC 会议纪要", "monetary", source_url, stamp, time_known=False, summary="Federal Reserve 官方日历标注 Minutes 发布日期。"))
            seen.add(key)
    return events


def load_bls_timeline_events() -> list[dict[str, Any]]:
    """Load an official BLS calendar plus its published historical values.

    The calendar is the authority for release *dates*.  The BLS series API is
    the authority for release *values*.  Keeping those roles separate lets us
    backfill an already-published calendar event without deriving a date from
    a data period.  The previous and current BLS calendars cover a rolling
    year boundary for users who browse backwards.
    """
    year = time.gmtime(now_ms() / 1000).tm_year
    urls = [f"https://www.bls.gov/schedule/{year - 1}/", f"https://www.bls.gov/schedule/{year}/"]
    patterns = [("Consumer Price Index", "inflation"), ("Producer Price Index", "inflation"), ("Employment Situation", "employment"), ("Job Openings and Labor Turnover", "employment")]
    executor = ThreadPoolExecutor(max_workers=3)
    schedule_futures = [
        (url, executor.submit(lambda source_url=url: parse_us_event_schedule(http_text_request(source_url), "BLS", source_url, patterns)))
        for url in urls
    ]
    series_future = executor.submit(load_bls_series_history)
    deadline = time.monotonic() + 6
    schedule_errors: list[Exception] = []
    series_error: Exception | None = None
    schedule_events: list[dict[str, Any]] = []
    for _url, future in schedule_futures:
        try:
            schedule_events.extend(future.result(timeout=max(0, deadline - time.monotonic())))
        except Exception as exc:
            # A WAF response from the human-facing calendar must not
            # discard persisted releases.  More importantly, it must not
            # let historical values attach to an unverified saved date.
            schedule_errors.append(exc)
    schedule_events = list({str(event["provider_event_key"]): event for event in schedule_events}.values())
    verified_snapshot = verified_bls_schedule_snapshot(year)
    if verified_snapshot:
        # This calendar year has a source-verified snapshot.  Prefer it over
        # old flattened entries so a partial live parse cannot reintroduce a
        # title/date leak while the official endpoint is intermittently 403.
        schedule_events = verified_snapshot
    elif not schedule_events:
        # The calendar endpoint is intermittently blocked in this deployment.
        # Use the bounded, source-attributed verified cache so historic pages
        # keep their official dates until a live calendar fetch succeeds.
        schedule_events = verified_bls_schedule_snapshot(year)
    try:
        observations = series_future.result(timeout=max(0, deadline - time.monotonic()))
    except Exception as exc:
        series_error = exc
        observations = {}
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    # Only a successfully parsed official calendar may bind historical values.
    # Saved rows can be malformed records written by an older parser, so using
    # them as a fallback here would recreate date/title mismatches.
    released_events = enrich_bls_released_events(schedule_events, observations)
    if not schedule_events and not released_events and schedule_errors:
        raise schedule_errors[0]
    if not schedule_events and not released_events and series_error:
        raise series_error
    return [*schedule_events, *released_events]


def verified_bls_schedule_snapshot(year: int) -> list[dict[str, Any]]:
    """Return a bounded official schedule cache when the live calendar is blocked."""
    if year != 2026:
        return []
    categories = {"Consumer Price Index": "inflation", "Producer Price Index": "inflation", "Employment Situation": "employment", "Job Openings and Labor Turnover": "employment"}
    slugs = {"Consumer Price Index": "cpi", "Producer Price Index": "ppi", "Employment Situation": "empsit", "Job Openings and Labor Turnover": "jolts"}
    events: list[dict[str, Any]] = []
    for title, releases in BLS_VERIFIED_SCHEDULE_2026.items():
        for date_value, time_value in releases:
            stamp = us_event_timestamp(date_value, time_value)
            if stamp is None:
                continue
            events.append(us_event_candidate(
                "BLS",
                f"{title.lower().replace(' ', '-')}-{date_value}",
                title,
                categories[title],
                f"https://www.bls.gov/schedule/news_release/{slugs[title]}.htm",
                stamp,
                time_known=True,
                summary="BLS 官方发布日程缓存；实时日历恢复后会自动校正。",
            ))
    return events


def uses_verified_bls_schedule_cache(events: list[dict[str, Any]]) -> bool:
    return any("BLS 官方发布日程缓存" in str(event.get("source_summary") or "") for event in events)


def bls_schedule_coverage_bounds(events: list[dict[str, Any]], fallback_now: int) -> tuple[int, int]:
    """Return the full official-calendar year coverage when it is explicit."""
    years = {
        int(match.group(1))
        for event in events
        for match in [re.search(r"/schedule/(20\d{2})/", str(event.get("source_url") or ""))]
        if match
    }
    if years:
        start_year, end_year = min(years), max(years)
        start = datetime(start_year, 1, 1, tzinfo=ZoneInfo(US_EVENT_TIMEZONE))
        end = datetime(end_year + 1, 1, 1, tzinfo=ZoneInfo(US_EVENT_TIMEZONE)) - timedelta(milliseconds=1)
        return int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    scheduled_at = [int(event["scheduled_at"]) for event in events if event.get("scheduled_at")]
    return min([fallback_now, *scheduled_at]), max(scheduled_at)


def bls_observation_month(row: dict[str, Any]) -> int | None:
    period = str(row.get("period") or "").strip().upper()
    matched = re.fullmatch(r"M(0[1-9]|1[0-2])", period)
    if matched:
        return int(matched.group(1))
    period_name = str(row.get("periodName") or "").strip()
    for month in range(1, 13):
        if period_name.lower() in {calendar.month_name[month].lower(), calendar.month_abbr[month].lower()}:
            return month
    return None


def load_bls_series_history() -> dict[str, list[dict[str, str]]]:
    """Read explicit monthly BLS observations in newest-first order.

    A record contains its actual row and the immediately preceding official
    row.  We intentionally discard annual/other aggregation periods so one
    calendar release is never paired with a non-monthly value.
    """
    year = time.gmtime(now_ms() / 1000).tm_year
    request_body = {
        "seriesid": [definition["series_id"] for definition in BLS_RELEASE_SERIES.values()],
        "startyear": str(year - 1),
        "endyear": str(year),
    }
    payload: dict[str, Any] | None = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            payload = http_json_request(BLS_RELEASE_DATA_URL, method="POST", body=request_body, timeout=5)
            break
        except (HTTPError, URLError, OSError, TimeoutError, IncompleteRead) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.2 * (attempt + 1))
    if payload is None:
        raise last_error or OfficialSourceError("BLS 数据服务暂时不可用", "no payload")
    results = payload.get("Results") if isinstance(payload.get("Results"), dict) else {}
    series_rows = results.get("series") if isinstance(results.get("series"), list) else []
    series_by_id = {
        str(item.get("seriesID") or ""): item.get("data")
        for item in series_rows
        if isinstance(item, dict) and isinstance(item.get("data"), list)
    }
    observed: dict[str, list[dict[str, str]]] = {}
    for title, definition in BLS_RELEASE_SERIES.items():
        rows = series_by_id.get(definition["series_id"], [])
        usable = [
            row for row in rows
            if isinstance(row, dict)
            and str(row.get("value") or "").strip() not in {"", "-"}
            and bls_observation_month(row) is not None
            and str(row.get("year") or "").isdigit()
        ]
        if not usable:
            continue
        usable.sort(key=lambda row: (int(str(row["year"])), int(bls_observation_month(row) or 0)), reverse=True)
        observed[title] = [
            {
                "actual": str(row.get("value") or "").strip(),
                "previous": str(usable[index + 1].get("value") or "").strip() if index + 1 < len(usable) else "",
                "period_label": bls_cpi_period_label(row),
                "unit": definition["unit"],
            }
            for index, row in enumerate(usable)
        ]
    return observed


def load_bls_latest_series() -> dict[str, dict[str, str]]:
    """Return the latest explicit observation for callers that only need it."""
    history = load_bls_series_history()
    return {title: rows[0] for title, rows in history.items() if rows}


def timeline_time_known(event: dict[str, Any]) -> bool:
    try:
        summary = json.loads(str(event.get("source_summary") or "{}"))
        return bool(summary.get("timeKnown")) if isinstance(summary, dict) else False
    except (TypeError, ValueError):
        return bool(event.get("timeKnown"))


def enrich_bls_released_events(events: list[dict[str, Any]], observations: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Attach published BLS rows to chronologically matching official releases.

    The calendar controls the date and title.  For each title, the most recent
    available monthly observations are aligned in chronological order with the
    same number of past calendar releases.  This safely backfills historical
    events while keeping values unavailable if either official source is
    incomplete; it never invents a release date or forecast.
    """
    observations = observations if observations is not None else load_bls_latest_series()
    now = now_ms()
    released: list[dict[str, Any]] = []
    for title, raw_observations in observations.items():
        if isinstance(raw_observations, dict):
            title_observations = [raw_observations]
        elif isinstance(raw_observations, list):
            title_observations = [item for item in raw_observations if isinstance(item, dict)]
        else:
            continue
        matches = [
            event for event in events
            if event.get("provider") == "BLS"
            and event.get("title") == title
            and isinstance(event.get("scheduled_at"), int)
            and int(event["scheduled_at"]) <= now
        ]
        if not matches or not title_observations:
            continue
        matches.sort(key=lambda event: int(event["scheduled_at"]))
        # The API is newest-first.  Keep the newest N observations for the N
        # official release dates in scope, then zip both oldest-first.
        matched_observations = list(reversed(title_observations[:len(matches)]))
        matched_events = matches[-len(matched_observations):]
        for event, observation in zip(matched_events, matched_observations):
            actual = str(observation.get("actual") or "").strip()
            if not actual:
                continue
            previous = str(observation.get("previous") or "").strip()
            summary = (
                f"BLS 官方数据 API：{observation.get('period_label') or ''} 实际值 {actual}"
                + (f"，前值 {previous}。" if previous else "。")
                + "发布日期以 BLS 官方日历记录为准。"
            )
            released.append(us_event_candidate(
                "BLS",
                str(event["provider_event_key"]),
                title,
                str(event["category"]),
                BLS_RELEASE_DATA_URL,
                int(event["scheduled_at"]),
                time_known=timeline_time_known(event),
                summary=summary,
                importance=str(event.get("importance") or "high"),
                state="released",
                actual=actual,
                previous=previous,
                unit=str(observation.get("unit") or ""),
                period_label=str(observation.get("period_label") or ""),
            ))
    return released


def load_bea_timeline_events() -> list[dict[str, Any]]:
    url = "https://www.bea.gov/news/schedule/full"
    return parse_us_event_schedule(http_text_request(url), "BEA", url, [("Gross Domestic Product", "growth"), ("Personal Income and Outlays", "consumption"), ("International Trade in Goods and Services", "trade")])


def parse_treasury_auction_schedule(text: str, source_url: str) -> list[dict[str, Any]]:
    """Normalize Treasury's pending-auctions XML without deriving calendar dates.

    An auction is omitted unless its announcement, auction, and issue/settlement
    dates are all present and parse cleanly in the official source.
    """
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return []
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for element in root.iter():
        fields = {
            re.sub(r"[^a-z]", "", child.tag.rsplit("}", 1)[-1].lower()): (child.text or "").strip()
            for child in list(element)
            if not list(child) and (child.text or "").strip()
        }
        announce = fields.get("announcementdate") or fields.get("announcedate")
        auction = fields.get("auctiondate")
        settlement = fields.get("issuedate") or fields.get("settlementdate") or fields.get("dateddate")
        security = " ".join(item for item in [fields.get("securityterm"), fields.get("securitytype") or fields.get("securitydescription")] if item)
        if not all([announce, auction, settlement, security]):
            continue
        announce_at, auction_at, settlement_at = (us_event_timestamp(value) for value in (announce, auction, settlement))
        if not all([announce_at, auction_at, settlement_at]):
            continue
        auction_date = datetime.fromtimestamp(int(auction_at) / 1000, tz=timezone.utc).date().isoformat()
        key = f"treasury-auction-{re.sub(r'[^a-z0-9]+', '-', security.lower()).strip('-')}-{auction_date}"
        if key in seen:
            continue
        summary = f"Treasury 官方待拍卖清单；公告日 {announce}，拍卖日 {auction}，结算/发行日 {settlement}。"
        events.append(us_event_candidate(
            "U.S. Treasury", key, f"美国国债拍卖：{security}", "treasury", source_url, auction_at,
            time_known=False, summary=summary, importance="medium", period_label=f"公告 {announce}；结算/发行 {settlement}",
        ))
        seen.add(key)
    return events


def load_treasury_timeline_events() -> list[dict[str, Any]]:
    url = "https://www.treasurydirect.gov/xml/PendingAuctions.xml"
    return parse_treasury_auction_schedule(http_text_request(url), url)


class UsEventProvider(Protocol):
    name: str
    def load(self) -> list[dict[str, Any]]: ...


class FunctionUsEventProvider:
    def __init__(self, name: str, loader: Any):
        self.name, self.loader = name, loader

    def load(self) -> list[dict[str, Any]]:
        return self.loader()


def us_event_providers() -> list[UsEventProvider]:
    return [
        FunctionUsEventProvider("Federal Reserve", load_fed_timeline_events),
        FunctionUsEventProvider("BLS", load_bls_timeline_events),
        FunctionUsEventProvider("BEA", load_bea_timeline_events),
        FunctionUsEventProvider("U.S. Treasury", load_treasury_timeline_events),
    ]


def refresh_us_market_events(force: bool = False) -> dict[str, Any]:
    with us_event_refresh_lock:
        now = now_ms()
        with us_event_cache_lock:
            ttl_seconds = int(us_event_refresh_cache.get("ttlSeconds") or US_EVENT_CACHE_SECONDS)
            if not force and us_event_refresh_cache["ts"] and now - int(us_event_refresh_cache["ts"]) <= ttl_seconds * 1000:
                return deepcopy(us_event_refresh_cache)
        warnings, providers, provider_statuses = [], [], []
        source_providers = us_event_providers()
        # Official sites are independent. Loading them one after another can
        # turn four bounded 20-second retries into an upstream timeout, even
        # when retained events could already be rendered. Start the reads
        # together and retain the stable provider-order for persistence/status.
        executor = ThreadPoolExecutor(max_workers=len(source_providers))
        loads = [(provider, executor.submit(provider.load)) for provider in source_providers]
        loaded: list[tuple[UsEventProvider, list[dict[str, Any]] | Exception]] = []
        refresh_deadline = time.monotonic() + 8
        try:
            for provider, future in loads:
                try:
                    remaining = max(0, refresh_deadline - time.monotonic())
                    loaded.append((provider, future.result(timeout=remaining)))
                except FutureTimeout:
                    loaded.append((provider, OfficialSourceError("官方站点响应超时，继续使用已保存日历", "refresh budget exceeded")))
                except Exception as exc:
                    loaded.append((provider, exc))
        finally:
            # Do not let an upstream socket that ignores its own read timeout
            # keep this read-only page behind the frontend proxy deadline.
            executor.shutdown(wait=False, cancel_futures=True)
        for provider, outcome in loaded:
            try:
                if isinstance(outcome, Exception):
                    raise outcome
                events = outcome
                for event in events:
                    database.upsert_market_event(event)
                if provider.name == "BLS":
                    scheduled = [event for event in events if event.get("state") == "scheduled" and event.get("scheduled_at")]
                    if scheduled:
                        coverage_start, coverage_end = bls_schedule_coverage_bounds(scheduled, now)
                        database.prune_unmatched_scheduled_market_events(
                            provider.name,
                            [str(event["provider_event_key"]) for event in scheduled],
                            coverage_start,
                            coverage_end,
                        )
                providers.append(provider.name)
                using_schedule_cache = provider.name == "BLS" and uses_verified_bls_schedule_cache(events)
                provider_statuses.append({
                    "provider": provider.name,
                    "status": "retained" if using_schedule_cache else "fresh",
                    "eventCount": len(events),
                    "retainedCount": database.count_market_events(provider.name),
                    **({"message": "BLS 公开日历暂不可读，正在使用已校验的官方日程缓存。"} if using_schedule_cache else {}),
                })
            except Exception as exc:
                source_error = official_source_error(exc)
                retained_count = database.count_market_events(provider.name)
                status = "retained" if retained_count else "unavailable"
                message = f"{provider.name} 暂时无法更新"
                if retained_count:
                    warnings.append(f"{message}，继续显示 {retained_count} 条已保存事件。")
                else:
                    warnings.append(f"{message}，当前没有可显示的已保存事件。")
                provider_statuses.append({"provider": provider.name, "status": status, "eventCount": 0, "retainedCount": retained_count, "message": source_error.public_message})
        near_events = database.list_market_events(now, now + US_EVENT_NEAR_WINDOW_MS, [], ["scheduled"])
        result = {
            "ts": now,
            "warnings": list(dict.fromkeys(warnings)),
            "providers": providers,
            "providerStatuses": provider_statuses,
            "ttlSeconds": US_EVENT_NEAR_CACHE_SECONDS if near_events else US_EVENT_CACHE_SECONDS,
        }
        with us_event_cache_lock:
            us_event_refresh_cache.update(result)
            return deepcopy(us_event_refresh_cache)


def us_event_refresh_due(now: int | None = None) -> bool:
    now = now if now is not None else now_ms()
    with us_event_cache_lock:
        cached_at = int(us_event_refresh_cache.get("ts") or 0)
        ttl_seconds = int(us_event_refresh_cache.get("ttlSeconds") or US_EVENT_CACHE_SECONDS)
    return not cached_at or now - cached_at > ttl_seconds * 1000


def refresh_us_market_events_in_background() -> bool:
    """Start at most one expired refresh without delaying a timeline read."""
    global us_event_refreshing
    if not us_event_refresh_due():
        return False
    with us_event_refresh_state_lock:
        if us_event_refreshing:
            return True
        us_event_refreshing = True

    def run() -> None:
        global us_event_refreshing
        try:
            refresh_us_market_events(force=True)
        finally:
            with us_event_refresh_state_lock:
                us_event_refreshing = False

    Thread(target=run, name="us-market-event-refresh", daemon=True).start()
    return True


def cached_us_event_refresh_state() -> tuple[dict[str, Any], bool]:
    with us_event_cache_lock:
        refresh = deepcopy(us_event_refresh_cache)
    with us_event_refresh_state_lock:
        return refresh, us_event_refreshing


def parse_us_event_date(value: str, field: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=8)))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field} 必须为 YYYY-MM-DD。") from exc


def market_us_events_view(from_date: str, to_date: str, categories: str = "", states: str = "") -> dict[str, Any]:
    start, end = parse_us_event_date(from_date, "from"), parse_us_event_date(to_date, "to")
    if end < start or (end - start).days > US_EVENT_MAX_DAYS:
        raise HTTPException(status_code=422, detail=f"日期范围必须在 0 到 {US_EVENT_MAX_DAYS} 天内。")
    category_values = [item.strip() for item in categories.split(",") if item.strip()]
    state_values = [item.strip() for item in states.split(",") if item.strip()]
    if not set(category_values).issubset(US_EVENT_CATEGORIES) or not set(state_values).issubset(US_EVENT_STATES):
        raise HTTPException(status_code=422, detail="事件分类或状态不受支持。")
    # The event list is a cache-first read. Official sites are slower and may
    # reject automated reads, so refresh them after the response has released
    # the persisted timeline rather than holding the page behind that work.
    refresh, refreshing = cached_us_event_refresh_state()
    refreshing = refresh_us_market_events_in_background() or refreshing
    rows = database.list_market_events(int(start.timestamp() * 1000), int((end + timedelta(days=1)).timestamp() * 1000), category_values, state_values)
    data = []
    for row in rows:
        summary = json.loads(row.pop("source_summary") or "{}")
        row["scheduledAt"] = row.pop("scheduled_at"); row["sourceTimezone"] = row.pop("source_timezone")
        row["publishedAt"] = row.pop("published_at"); row["fetchedAt"] = row.pop("fetched_at")
        row["previousValue"] = row.pop("previous_value"); row["sourceUrl"] = row.pop("source_url")
        row["sourceSummary"] = summary.get("summary", ""); row["timeKnown"] = bool(summary.get("timeKnown")); row["official"] = bool(row["official"])
        data.append(row)
    return {"data": data, "generatedAt": now_ms(), "source": "official-us-event-calendar", "cacheAgeMs": max(0, now_ms() - int(refresh["ts"] or now_ms())), "refreshing": refreshing, "warnings": refresh["warnings"], "providers": refresh["providers"], "providerStatuses": refresh.get("providerStatuses", [])}


def normalize_market_ai_inst_id(inst_id: str) -> str:
    return normalize_market_stats_inst_id(inst_id)


def normalize_market_ai_bar(bar: str) -> str:
    normalized = bar.strip() or "1m"
    if normalized not in SUPPORTED_BARS:
        raise HTTPException(status_code=400, detail="AI看行情 K线周期不受支持。")
    return normalized


def find_instrument(inst_id: str) -> dict[str, Any]:
    rows = database.list_instruments(query=inst_id, limit=20)
    for row in rows:
        if str(row.get("inst_id") or "").upper() == inst_id:
            return row
    return {"inst_id": inst_id, "inst_type": "SWAP", "inst_family": "-".join(inst_id.split("-")[:2]), "state": ""}


def ticker_snapshot_for_inst(inst_id: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    payload = cached_tickers(force=False)
    rows = payload.get("data") if isinstance(payload.get("data"), list) else []
    ticker = next((item for item in rows if isinstance(item, dict) and str(item.get("instId") or "").upper() == inst_id), None)
    meta = {
        "source": payload.get("source") or "",
        "ts": payload.get("ts") or 0,
        "cacheAgeMs": payload.get("cacheAgeMs"),
        "warning": payload.get("warning") or "",
    }
    quote_ts = int(safe_decimal((ticker or {}).get("ts") or meta["ts"]) or 0)
    bid = safe_decimal((ticker or {}).get("bidPx"))
    ask = safe_decimal((ticker or {}).get("askPx"))
    quote_valid = bid is not None and ask is not None and bid > 0 and ask >= bid
    if not quote_valid or quote_ts <= 0 or now_ms() - quote_ts > 30_000:
        try:
            fresh = client.get_ticker(inst_id)
            if fresh and str(fresh.get("instId") or "").upper() == inst_id:
                ticker = fresh
                meta = {"source": "okx-single-ticker", "ts": int(safe_decimal(fresh.get("ts")) or 0), "cacheAgeMs": 0, "warning": ""}
        except OkxError:
            pass
    return ticker, meta


def candle_snapshot_for_inst(inst_id: str, bar: str, limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        rows = client.get_candles(inst_id, bar, limit)
        database.upsert_candles(inst_id, bar, rows)
        return rows, {"source": "okx", "ts": now_ms(), "cacheAgeMs": 0, "warning": ""}
    except OkxError as exc:
        cached = database.latest_candles(inst_id, bar, limit)
        if cached:
            return cached, {"source": "database-cache", "ts": now_ms(), "cacheAgeMs": None, "warning": str(exc)}
        return [], {"source": "okx-unavailable", "ts": now_ms(), "cacheAgeMs": None, "warning": str(exc)}


def decimal_or_zero(value: Any) -> Decimal:
    return safe_decimal(value) or Decimal("0")


def market_ai_volume_context(candles: list[dict[str, Any]]) -> dict[str, Any]:
    volumes = [decimal_or_zero(item.get("volumeQuote") or item.get("volume")) for item in candles]
    recent = volumes[-5:]
    previous = volumes[-10:-5]
    recent_avg = sum(recent, Decimal("0")) / Decimal(len(recent)) if recent else Decimal("0")
    previous_avg = sum(previous, Decimal("0")) / Decimal(len(previous)) if previous else Decimal("0")
    change_pct = (recent_avg - previous_avg) / previous_avg * Decimal("100") if previous_avg > 0 else Decimal("0")
    return {
        "recentAverage": decimal_display(recent_avg),
        "previousAverage": decimal_display(previous_avg),
        "changePct": decimal_display(change_pct),
        "context": "expanding" if change_pct >= Decimal("25") else "contracting" if change_pct <= Decimal("-25") else "normal",
    }


def market_ai_last_candle_shape(candles: list[dict[str, Any]]) -> dict[str, Any]:
    if not candles:
        return {"bodyPct": "", "upperWickPct": "", "lowerWickPct": "", "direction": "unknown"}
    item = candles[-1]
    open_price = safe_decimal(item.get("open"))
    high = safe_decimal(item.get("high"))
    low = safe_decimal(item.get("low"))
    close = safe_decimal(item.get("close"))
    if open_price is None or high is None or low is None or close is None or close <= 0:
        return {"bodyPct": "", "upperWickPct": "", "lowerWickPct": "", "direction": "unknown"}
    body_pct = abs(close - open_price) / close * Decimal("100")
    upper_wick = max(high - max(open_price, close), Decimal("0")) / close * Decimal("100")
    lower_wick = max(min(open_price, close) - low, Decimal("0")) / close * Decimal("100")
    return {
        "bodyPct": decimal_display(body_pct),
        "upperWickPct": decimal_display(upper_wick),
        "lowerWickPct": decimal_display(lower_wick),
        "direction": "up" if close >= open_price else "down",
    }


def market_ai_trend_label(summary: dict[str, Any]) -> str:
    change = safe_decimal(summary.get("changePct")) or Decimal("0")
    range_pct = safe_decimal(summary.get("recent20RangePct")) or Decimal("0")
    ma5 = safe_decimal(summary.get("ma5"))
    ma20 = safe_decimal(summary.get("ma20"))
    if range_pct >= Decimal("6"):
        return "volatile"
    if change >= Decimal("1.5") and ma5 is not None and ma20 is not None and ma5 >= ma20:
        return "up"
    if change <= Decimal("-1.5") and ma5 is not None and ma20 is not None and ma5 <= ma20:
        return "down"
    return "range"


def market_ai_report_bias(trend: str, has_warnings: bool = False) -> str:
    if has_warnings:
        return "谨慎观望"
    if trend in {"up", "bullish"}:
        return "偏多参考"
    if trend in {"down", "bearish"}:
        return "偏空参考"
    if trend == "volatile":
        return "波动加大"
    if trend == "wait":
        return "暂时观望"
    return "震荡观察"


def market_ai_horizon_label(key: str) -> str:
    if key == "15m":
        return "未来15分钟"
    if key == "1h":
        return "未来1小时"
    if key == "today":
        return "今天走势"
    return key


def market_ai_horizon_bar_evidence(inst_id: str, bar: str, limit: int) -> dict[str, Any]:
    candles, meta = candle_snapshot_for_inst(inst_id, bar, limit)
    summary = candle_market_summary(candles)
    trend = market_ai_trend_label(summary)
    return {
        "bar": bar,
        "source": meta.get("source") or "",
        "cacheAgeMs": meta.get("cacheAgeMs"),
        "warning": meta.get("warning") or "",
        "summary": {
            **summary,
            "trend": trend,
            "lastCandle": market_ai_last_candle_shape(candles),
            "volume": market_ai_volume_context(candles),
        },
        "recentCandles": [compact_candle_for_llm(item) for item in candles[-MARKET_AI_HORIZON_DETAIL_LIMIT:]],
    }


def build_market_ai_horizon_evidence(inst_id: str, selected_bar: str, limit: int) -> dict[str, Any]:
    bars = []
    for candidate in [selected_bar, "1m", "5m", "15m", "1H", "4H"]:
        if candidate in SUPPORTED_BARS and candidate not in bars:
            bars.append(candidate)
    bar_payloads = {
        bar: market_ai_horizon_bar_evidence(inst_id, bar, min(max(limit, 60), MARKET_AI_HORIZON_CANDLE_LIMIT))
        for bar in bars
    }
    warnings = [
        f"{bar} K线刷新提示：{payload.get('warning')}"
        for bar, payload in bar_payloads.items()
        if payload.get("warning")
    ]
    return {
        "targets": [
            {
                "key": key,
                "label": market_ai_horizon_label(key),
                "bars": [bar for bar in target_bars if bar in bar_payloads],
                "purpose": "短线噪音与即时突破" if key == "15m" else "小时级结构与量能延续" if key == "1h" else "日内趋势、24h状态与宏观影响",
            }
            for key, target_bars in MARKET_AI_HORIZON_BARS.items()
        ],
        "bars": bar_payloads,
        "warnings": warnings,
    }


def market_ai_fixed_trend_label(trend: str) -> str:
    return {
        "up": "偏强",
        "down": "偏弱",
        "volatile": "波动较大",
        "range": "震荡整理",
    }.get(trend, "等待确认")


def market_ai_fixed_trend_evidence(bar: str, label: str, candles: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    """Create a compact, independently verifiable reading for one fixed K-line period."""
    summary = candle_market_summary(candles)
    source = str(meta.get("source") or "okx-unavailable")
    warning = str(meta.get("warning") or "")
    last_ts = coerce_int(summary.get("lastTs"), 0, 0, 9_999_999_999_999)
    cache_age_ms = max(0, now_ms() - last_ts) if last_ts else None
    stale_cache = source in {"database-cache", "cache", "chart-snapshot"} and (
        not last_ts or cache_age_ms is None or cache_age_ms > CANDLE_BAR_MILLISECONDS[bar] * CANDLE_CACHE_FRESHNESS_BARS
    )
    if len(candles) < 20:
        reason = "该周期 K线不足 20 根，暂不能形成可核对的趋势读取。" if candles else "该周期 K线暂未获取，等待数据恢复后再读取。"
        return {
            "key": bar,
            "bar": bar,
            "label": label,
            "available": False,
            "status": "unavailable",
            "trend": "unavailable",
            "trendLabel": "数据待获取",
            "evidence": [],
            "condition": f"等待 {label} K线数据完整后重新读取。",
            "invalidation": "当前周期数据恢复或生成新 K线后重新阅读。",
            "source": source,
            "cacheAgeMs": meta.get("cacheAgeMs"),
            "lastCandleTs": summary.get("lastTs") or 0,
            "warning": "该周期数据不足，未使用其他周期替代。" if warning else reason,
        }
    if stale_cache:
        return {
            "key": bar,
            "bar": bar,
            "label": label,
            "available": False,
            "status": "unavailable",
            "trend": "unavailable",
            "trendLabel": "数据待获取",
            "evidence": [],
            "condition": f"等待 {label} K线刷新后重新读取。",
            "invalidation": "该周期缓存已过期，不作为当前趋势依据。",
            "source": source,
            "cacheAgeMs": cache_age_ms,
            "lastCandleTs": summary.get("lastTs") or 0,
            "warning": f"{label} K线缓存已过期，未使用其他周期替代。",
        }

    trend = market_ai_trend_label(summary)
    last_close = str(summary.get("lastClose") or "--")
    ma5 = str(summary.get("ma5") or "")
    ma20 = str(summary.get("ma20") or "")
    high = str(summary.get("recent20High") or "")
    low = str(summary.get("recent20Low") or "")
    change = str(summary.get("changePct") or "0")
    volume = market_ai_volume_context(candles)
    volume_context = str(volume.get("context") or "normal")
    volume_label = {"expanding": "量能较前段放大", "contracting": "量能较前段缩减", "normal": "量能变化不明显"}.get(volume_context, "量能待确认")
    evidence = [item for item in [
        f"MA5 {ma5} {'高于' if trend == 'up' else '低于' if trend == 'down' else '接近'} MA20 {ma20}" if ma5 and ma20 else "均线数据待确认",
        f"近20根涨跌 {change}% · {volume_label}",
    ] if item][:2]
    if trend == "up" and high:
        condition = f"等待完整一根 {label} K线收在近20根高点 {high} 上方后，再确认偏强延续。"
        invalidation = f"若完整一根 {label} K线回到近20根高点 {high} 下方，重新阅读该周期。"
    elif trend == "down" and low:
        condition = f"等待完整一根 {label} K线收在近20根低点 {low} 下方后，再确认偏弱延续。"
        invalidation = f"若完整一根 {label} K线重新站回近20根低点 {low} 上方，重新阅读该周期。"
    elif high and low:
        condition = f"完整一根 {label} K线收在 {high} 上方或 {low} 下方后，再重新判断方向。"
        invalidation = f"价格仍在 {low} – {high} 区间内时，维持震荡读取。"
    else:
        condition = f"等待完整一根 {label} K线和近20根区间数据后重新读取。"
        invalidation = "当前周期新 K线形成后重新阅读。"
    return {
        "key": bar,
        "bar": bar,
        "label": label,
        "available": True,
        "status": "available",
        "trend": trend,
        "trendLabel": market_ai_fixed_trend_label(trend),
        "evidence": evidence,
        "condition": condition,
        "invalidation": invalidation,
        "source": source,
        "cacheAgeMs": cache_age_ms if source in {"database-cache", "cache", "chart-snapshot"} else meta.get("cacheAgeMs"),
        "lastCandleTs": summary.get("lastTs") or 0,
        "warning": "使用缓存快照，刷新后请重新核对。" if source == "database-cache" else "",
        "summary": {
            "lastClose": last_close,
            "ma5": ma5,
            "ma20": ma20,
            "recent20High": high,
            "recent20Low": low,
            "changePct": change,
            "volumeContext": volume_context,
        },
    }


def build_market_ai_fixed_trends(
    inst_id: str,
    selected_bar: str,
    chart_snapshot: dict[str, Any] | None = None,
    plan_candles: tuple[list[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Read 15m, 1H and 1D separately; never derive one period from another."""
    rows: list[dict[str, Any]] = []
    snapshot_metadata = chart_snapshot.get("metadata") if isinstance(chart_snapshot, dict) and isinstance(chart_snapshot.get("metadata"), dict) else {}
    for key, bar, label in MARKET_AI_FIXED_TREND_PERIODS:
        if bar == "15m" and plan_candles is not None:
            candles, meta = plan_candles
        elif chart_snapshot and selected_bar == bar:
            candles = deepcopy(chart_snapshot.get("candles") or [])
            meta = {
                "source": snapshot_metadata.get("source") or "chart-snapshot",
                "ts": snapshot_metadata.get("snapshotTs") or now_ms(),
                "cacheAgeMs": max(0, now_ms() - int(snapshot_metadata.get("snapshotTs") or now_ms())),
                "warning": snapshot_metadata.get("warning") or "",
            }
        else:
            candles, meta = candle_snapshot_for_inst(inst_id, bar, MARKET_AI_HORIZON_CANDLE_LIMIT)
        reading = market_ai_fixed_trend_evidence(bar, label, candles, meta)
        if not reading["available"] and meta.get("source") in {"database-cache", "okx-unavailable"}:
            # A single transient OKX failure should not leave a period marked
            # unavailable when a second independent read can recover it.
            retry_candles, retry_meta = candle_snapshot_for_inst(inst_id, bar, MARKET_AI_HORIZON_CANDLE_LIMIT)
            reading = market_ai_fixed_trend_evidence(bar, label, retry_candles, retry_meta)
        reading["key"] = key
        rows.append(reading)

    available_directions = [str(item.get("trend") or "") for item in rows if item.get("available") and item.get("trend") in {"up", "down"}]
    unavailable_count = sum(1 for item in rows if not item.get("available"))
    if unavailable_count:
        alignment = "部分周期数据待获取；仅阅读已可用周期，不将其替代为其他周期结论。"
        alignment_state = "incomplete"
    elif len(available_directions) == 3 and len(set(available_directions)) == 1:
        alignment = f"15分钟、1小时和日线均{market_ai_fixed_trend_label(available_directions[0])}，周期方向一致。"
        alignment_state = "aligned"
    elif len(set(available_directions)) > 1:
        alignment = "短线与更大周期存在分歧，先以各周期确认条件为准。"
        alignment_state = "split"
    else:
        alignment = "各周期尚未同时形成明确方向，等待完整 K线确认。"
        alignment_state = "mixed"
    return {"version": 1, "periods": rows, "alignment": alignment, "alignmentState": alignment_state}


def market_ai_plan_candles(
    inst_id: str, selected_bar: str, chart_snapshot: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reuse the selected chart only if it is the independent 15m source."""
    if selected_bar == "15m":
        metadata = chart_snapshot.get("metadata") if isinstance(chart_snapshot.get("metadata"), dict) else {}
        candles, meta = deepcopy(chart_snapshot.get("candles") or []), {
            "source": metadata.get("source") or "chart-snapshot",
            "ts": metadata.get("snapshotTs") or 0,
            "warning": metadata.get("warning") or "",
        }
    else:
        candles, meta = candle_snapshot_for_inst(inst_id, "15m", MARKET_AI_HORIZON_CANDLE_LIMIT)
    if candle_batch_issue(candles, "15m") or meta.get("source") in {"database-cache", "okx-unavailable"}:
        # A transient stale 15m read must not hide an otherwise current price
        # plan. Retry the same independent period, without using the chart bar.
        retry_candles, retry_meta = candle_snapshot_for_inst(inst_id, "15m", MARKET_AI_HORIZON_CANDLE_LIMIT)
        if not candle_batch_issue(retry_candles, "15m"):
            return retry_candles, retry_meta
    return candles, meta


def build_market_ai_price_plan(
    market: dict[str, Any], candles: list[dict[str, Any]], meta: dict[str, Any], current_ms: int | None = None
) -> dict[str, Any]:
    """Calculate a read-only 15m price plan; LLM output cannot set these prices."""
    current_ms = now_ms() if current_ms is None else current_ms
    instrument = market.get("instrument") if isinstance(market.get("instrument"), dict) else {}
    ticker = market.get("ticker") if isinstance(market.get("ticker"), dict) else {}
    ticker_freshness = (market.get("freshness") or {}).get("ticker") if isinstance(market.get("freshness"), dict) else {}
    quote_ts = int(safe_decimal(ticker.get("ts")) or 0)
    structure = market.get("pricePlanStructure") if isinstance(market.get("pricePlanStructure"), dict) else {}
    periods = ((market.get("multiTimeframeTrend") or {}).get("periods") or []) if isinstance(market.get("multiTimeframeTrend"), dict) else []
    normalized = normalize_candle_batch(candles)
    closed = [item for item in normalized if str(item.get("confirm") or "") == "1"]
    tick = safe_decimal(instrument.get("tickSize"))
    base = {
        "version": 3,
        "entryBasis": "quote_snapshot",
        "instId": str(instrument.get("instId") or ""),
        "bar": "15m",
        "source": str(meta.get("source") or ""),
        "sourceTs": int(meta.get("ts") or 0),
        "lastClosedTs": int(closed[-1]["ts"]) if closed else 0,
        "validUntil": int(closed[-1]["ts"]) + 2 * CANDLE_BAR_MILLISECONDS["15m"] if closed else 0,
        "readOnly": True,
        "priceMeaning": "预计入场价取分析时可见的做多卖一价或做空买一价；止盈是预测参考价，止损是触发价，均不保证实际成交。",
        "costNote": "价格未扣除个人费率、资金费和实际滑点。",
    }

    def unavailable(reason: str) -> dict[str, Any]:
        return {**base, "status": "unavailable", "direction": "none", "reason": reason, "entryPrice": "", "stopPrice": "", "targetPrice": "", "upperReassess": "", "lowerReassess": "", "evidence": []}

    if tick is None or tick <= 0:
        return unavailable("合约报价单位未获取，暂不能计算可核对的买卖价。")
    if len(closed) < 21:
        return unavailable("15分钟已收盘 K线不足 21 根，暂不能计算价格计划。")
    if candle_batch_issue(normalized, "15m", current_ms):
        return unavailable("15分钟 K线快照不完整或已过期，请刷新后重新分析。")

    def rounded(value: Decimal, mode: str) -> Decimal:
        direction = ROUND_CEILING if mode == "up" else ROUND_FLOOR
        return (value / tick).to_integral_value(rounding=direction) * tick

    prior = closed[-21:-1]
    signal = closed[-1]
    highs = [safe_decimal(row.get("high")) for row in prior]
    lows = [safe_decimal(row.get("low")) for row in prior]
    close = safe_decimal(signal.get("close"))
    recent_lows = [safe_decimal(row.get("low")) for row in closed[-5:]]
    recent_highs = [safe_decimal(row.get("high")) for row in closed[-5:]]
    if close is None or any(value is None for value in [*highs, *lows, *recent_lows, *recent_highs]):
        return unavailable("15分钟 K线价格字段不完整，暂不能计算价格计划。")
    high = max(highs)
    low = min(lows)
    if low <= 0 or high <= low:
        return unavailable("15分钟历史区间无效，暂不能计算价格计划。")
    upper = rounded(high, "up") + tick
    lower = rounded(low, "down") - tick
    if lower <= 0:
        return unavailable("下方重评价不合法，暂不能计算价格计划。")

    closes = [safe_decimal(row.get("close")) for row in closed[-20:]]
    if any(value is None for value in closes):
        return unavailable("15分钟收盘价不完整，暂不能判断方向。")
    ma5 = sum(closes[-5:], Decimal("0")) / Decimal("5")
    ma20 = sum(closes, Decimal("0")) / Decimal("20")
    score = (1 if close > ma20 else -1 if close < ma20 else 0) + (1 if ma5 > ma20 else -1 if ma5 < ma20 else 0)
    evidence = [f"15分钟已收盘价 {'高于' if close > ma20 else '低于' if close < ma20 else '等于'} MA20", f"15分钟 MA5 {'高于' if ma5 > ma20 else '低于' if ma5 < ma20 else '等于'} MA20"]
    for bar, label in (("1H", "1小时"), ("1D", "日线")):
        item = next((row for row in periods if isinstance(row, dict) and row.get("bar") == bar), {})
        trend = str(item.get("trend") or "") if item.get("available") else ""
        if trend in {"up", "down"}:
            score += 1 if trend == "up" else -1
            evidence.append(f"{label}{'偏强' if trend == 'up' else '偏弱'}")
    for item in structure.get("items") or []:
        if isinstance(item, dict) and item.get("available") and item.get("key") in {"longShortAccountRatio", "takerVolume"} and item.get("signal") in {"up", "down"}:
            score += 1 if item["signal"] == "up" else -1
            evidence.append(f"{item.get('label') or '交易统计'}{'偏多' if item['signal'] == 'up' else '偏空'}")
    common = {
        **base,
        "upperReassess": decimal_display(upper),
        "lowerReassess": decimal_display(lower),
        "rangeHigh": decimal_display(high),
        "rangeLow": decimal_display(low),
        "evidence": evidence,
        "basis": "预计入场价取分析时可见的卖一价（做多）或买一价（做空）；止损取最近5根完整15分钟 K线极值，预测止盈价按入场到止损的2倍价差计算。此前20根完整 K线的上下沿只用于重新评估，不作为入场价。",
        "structurePeriod": str(structure.get("period") or ""),
        "score": score,
    }
    if score == 0:
        return {**common, "status": "no_plan", "direction": "none", "reason": "多空证据打平；上方和下方重评价可用于下一次分析。", "entryPrice": "", "stopPrice": "", "targetPrice": ""}

    is_long = score > 0
    if current_ms >= base["validUntil"]:
        return {**common, "status": "expired", "direction": "long" if is_long else "short", "reason": "15分钟观察时段已经结束，请刷新后重新分析。", "entryPrice": "", "stopPrice": "", "targetPrice": ""}
    bid = safe_decimal(ticker.get("bidPx"))
    ask = safe_decimal(ticker.get("askPx"))
    quote_ok = bid is not None and ask is not None and bid > 0 and ask >= bid
    quote_fresh = quote_ok and quote_ts > 0 and -5_000 <= current_ms - quote_ts <= 30_000
    if not quote_fresh:
        return {**common, "status": "unavailable", "direction": "long" if is_long else "short", "reason": "分析时买一卖一报价缺失或超过30秒，无法冻结预计入场价；请刷新后重新分析。", "entryPrice": "", "stopPrice": "", "targetPrice": ""}
    entry = ask if is_long else bid
    if entry % tick != 0:
        return {**common, "status": "unavailable", "direction": "long" if is_long else "short", "reason": "当前买一卖一报价与合约最小报价单位不一致，暂不生成预计入场价。", "entryPrice": "", "stopPrice": "", "targetPrice": ""}
    stop = rounded(min(recent_lows), "down") - tick if is_long else rounded(max(recent_highs), "up") + tick
    risk = entry - stop if is_long else stop - entry
    if risk <= 0:
        return {**common, "status": "unavailable", "direction": "none", "reason": "入场与止损价格关系无效，暂不能生成主计划。", "entryPrice": "", "stopPrice": "", "targetPrice": ""}
    target = rounded(entry + risk * 2, "up") if is_long else rounded(entry - risk * 2, "down")
    if target <= 0:
        return {**common, "status": "unavailable", "direction": "none", "reason": "止盈参考价超出有效价格范围，暂不能生成主计划。", "entryPrice": "", "stopPrice": "", "targetPrice": ""}

    spread = ask - bid if quote_ok else None
    spread_wide = bool(spread is not None and spread > risk / 10)
    risk_pct = (risk / entry * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    target_pct = (abs(target - entry) / entry * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    def relation(left: Decimal, right: Decimal) -> str:
        return "高于" if left > right else "低于" if left < right else "等于"
    direction_evidence = [
        f"最近完整15分钟收盘 {decimal_display(close)} {relation(close, ma20)} MA20 {decimal_display(ma20)}",
        f"MA5 {decimal_display(ma5)} {relation(ma5, ma20)} MA20 {decimal_display(ma20)}",
        *evidence[2:],
    ]
    price_logic = {
        "direction": f"{'；'.join(direction_evidence)}。每项偏强 +1、偏弱 -1、相等 0，合计 {score:+d} 分，因此选择{'做多' if is_long else '做空'}。这是规则方向，不是成交信号。",
        "entry": f"预计{'买入' if is_long else '卖出'}价 {decimal_display(entry)} 取自分析时{'卖一' if is_long else '买一'}报价；当时买一 {decimal_display(bid)}、卖一 {decimal_display(ask)}，价差 {decimal_display(spread)}。报价时间另行保存，报价不等于成交。",
        "stop": f"最近5根完整15分钟 K线{'最低价' if is_long else '最高价'} {decimal_display(min(recent_lows) if is_long else max(recent_highs))}，按最小报价单位 {decimal_display(tick)} 向{'下' if is_long else '上'}取整后再外移一个单位，得止损参考价 {decimal_display(stop)}。从预计入手价到止损相差 {decimal_display(risk)}（{risk_pct}%）。",
        "target": f"按固定 2 倍风险价差计算：{decimal_display(entry)} {'+' if is_long else '−'} 2 × {decimal_display(risk)}，再按报价单位向目标方向取整，得预测止盈价 {decimal_display(target)}；相对预计入手价为 +{target_pct}%。这是预设目标，不是 AI 已验证的盈利预测。",
        "validity": "只核验报告生成后的完整1分钟 K线，截止于本轮下一根15分钟 K线收盘；报价超过30秒或计划过期后须重新分析。价格触及不代表委托成交或实际收益。",
    }
    status, reason = (
        ("watch", "已记录分析时的买一卖一报价，但价差较宽；预计入场价仅供比较，不能视为实际成交。")
        if spread_wide else
        ("ready", "已记录分析时可见的报价作为预计入场价；后续核验预测止盈价是否到达，不代表已经成交。")
    )
    return {
        **common,
        "status": status,
        "direction": "long" if is_long else "short",
        "reason": reason,
        "entryPrice": decimal_display(entry),
        "stopPrice": decimal_display(stop),
        "targetPrice": decimal_display(target),
        "priceConditionMet": not spread_wide,
        "bidPx": decimal_display(bid) if quote_ok else "",
        "askPx": decimal_display(ask) if quote_ok else "",
        "spread": decimal_display(spread) if spread is not None else "",
        "quoteTs": quote_ts,
        "entryQuoteTs": quote_ts,
        "quoteSource": str(ticker_freshness.get("source") or ""),
        "quoteFresh": quote_fresh,
        "priceLogic": price_logic,
        "condition": f"以分析时{'卖一' if is_long else '买一'}报价 {decimal_display(entry)} 作预计入场价；预测止盈价需在本轮15分钟截止前由后续完整行情核对。报价不保证成交。",
    }


def build_market_ai_market_evidence(
    inst_id: str,
    bar: str,
    limit: int,
    chart_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    instrument = find_instrument(inst_id)
    ticker, ticker_meta = ticker_snapshot_for_inst(inst_id)
    snapshot_metadata = chart_snapshot.get("metadata") if isinstance(chart_snapshot, dict) and isinstance(chart_snapshot.get("metadata"), dict) else {}
    if chart_snapshot:
        candles = deepcopy(chart_snapshot.get("candles") or [])
        candle_meta = {
            "source": snapshot_metadata.get("source") or "chart-snapshot",
            "ts": snapshot_metadata.get("snapshotTs") or 0,
            "cacheAgeMs": max(0, now_ms() - int(snapshot_metadata.get("snapshotTs") or now_ms())),
            "warning": snapshot_metadata.get("warning") or "",
        }
    else:
        candles, candle_meta = candle_snapshot_for_inst(inst_id, bar, limit)
        chart_snapshot = create_chart_snapshot(inst_id, bar, candles, str(candle_meta.get("source") or "okx"), warning=str(candle_meta.get("warning") or ""))
        snapshot_metadata = chart_snapshot["metadata"]
    bounded_candles = candles[-MARKET_AI_PROMPT_CANDLES:]
    summary = candle_market_summary(candles)
    liquidity = radar_liquidity(ticker, str(instrument.get("settle_ccy") or instrument.get("settleCcy") or ""))
    last = ticker_decimal(ticker, ["last", "lastPx", "close"]) or safe_decimal(summary.get("lastClose"))
    open24h = ticker_decimal(ticker, ["open24h", "sodUtc0", "sodUtc8"])
    high24h = ticker_decimal(ticker, ["high24h"])
    low24h = ticker_decimal(ticker, ["low24h"])
    warnings = []
    if not ticker:
        warnings.append("Ticker 快照缺失，AI 仅参考 K线。")
    if not candles:
        warnings.append("K线数据缺失，AI 只能给出数据不足提示。")
    elif len(candles) < 30:
        warnings.append("K线数量不足 30 根，技术判断可信度较低。")
    if ticker_meta.get("warning"):
        warnings.append(f"Ticker 刷新提示：{ticker_meta['warning']}")
    if candle_meta.get("warning"):
        warnings.append(f"K线刷新提示：{candle_meta['warning']}")
    return {
        "instrument": {
            "instId": inst_id,
            "instFamily": instrument.get("inst_family") or instrument.get("instFamily") or "",
            "settleCcy": instrument.get("settle_ccy") or instrument.get("settleCcy") or "",
            "contractValue": instrument.get("ct_val") or instrument.get("ctVal") or "",
            "contractValueCcy": instrument.get("ct_val_ccy") or instrument.get("ctValCcy") or "",
            "tickSize": instrument.get("tick_sz") or instrument.get("tickSz") or "",
            "lotSize": instrument.get("lot_sz") or instrument.get("lotSz") or "",
            "state": instrument.get("state") or "",
        },
        "ticker": {
            "last": decimal_display(last) if last is not None else "",
            "ts": str(ticker.get("ts") or "") if ticker else "",
            "bidPx": str(ticker.get("bidPx") or "") if ticker else "",
            "askPx": str(ticker.get("askPx") or "") if ticker else "",
            "open24h": decimal_display(open24h) if open24h is not None else "",
            "high24h": decimal_display(high24h) if high24h is not None else "",
            "low24h": decimal_display(low24h) if low24h is not None else "",
            "change24hPct": percent_change(open24h, last),
            "volume24h": decimal_display(liquidity.get("value")) if isinstance(liquidity.get("value"), Decimal) else "",
            "volumeBasis": liquidity.get("basis") or "missing",
            "volumeUnit": liquidity.get("unit") or "",
        },
        "candles": [compact_candle_for_llm(item) for item in bounded_candles],
        "technical": {
            **summary,
            "bar": bar,
            "trend": market_ai_trend_label(summary),
            "range24hPct": decimal_display(pct_from_values(low24h, high24h, last)),
            "lastCandle": market_ai_last_candle_shape(candles),
            "volume": market_ai_volume_context(candles),
            "detailLimit": MARKET_AI_PROMPT_CANDLES,
        },
        "chartSnapshot": snapshot_metadata,
        "freshness": {
            "ticker": ticker_meta,
            "candles": candle_meta,
        },
        "warnings": warnings,
    }


def market_ai_trading_structure_period(bar: str) -> str:
    return normalize_market_stats_period(bar)


def market_ai_trading_structure_evidence(inst_id: str, bar: str) -> dict[str, Any]:
    requested_period = bar.strip() or MARKET_STATS_DEFAULT_PERIOD
    period = market_ai_trading_structure_period(requested_period)
    payload = cached_market_stats(inst_id, requested_period, period, 20)
    warnings = [str(item) for item in payload.get("warnings") or [] if str(item).strip()]
    source = str(payload.get("source") or "okx-market-stats-unavailable")
    long_short = payload.get("longShortAccountRatio") if isinstance(payload.get("longShortAccountRatio"), dict) else {}
    taker = payload.get("takerVolume") if isinstance(payload.get("takerVolume"), dict) else {}
    open_interest = payload.get("openInterest") if isinstance(payload.get("openInterest"), dict) else {}
    long_short_bias = str(long_short.get("bias") or "unavailable")
    taker_dominance_value = str(taker.get("dominance") or "unavailable")
    oi_trend = str(open_interest.get("trend") or "unavailable")
    items = [
        {
            "key": "longShortAccountRatio",
            "label": "多空账户",
            "value": str(long_short.get("latest") or ""),
            "state": long_short_bias,
            "signal": "up" if long_short_bias == "more_long_accounts" else "down" if long_short_bias == "more_short_accounts" else "neutral",
            "available": bool(long_short.get("latest")),
        },
        {
            "key": "takerVolume",
            "label": "主动买卖",
            "value": str(taker.get("buySharePct") or ""),
            "state": taker_dominance_value,
            "signal": "up" if taker_dominance_value == "active_buying_stronger" else "down" if taker_dominance_value == "active_selling_stronger" else "neutral",
            "available": bool(taker.get("buySharePct")),
        },
        {
            "key": "openInterest",
            "label": "持仓变化",
            "value": str(open_interest.get("changePct") or ""),
            "state": oi_trend,
            "signal": "participation" if oi_trend == "increasing" else "neutral",
            "available": bool(open_interest.get("changePct")),
        },
    ]
    available_count = sum(1 for item in items if item["available"])
    quality = "complete" if available_count == len(items) and not warnings and "partial" not in source and "stale" not in source else "partial" if available_count else "unavailable"
    return {
        "instId": inst_id,
        "requestedPeriod": requested_period,
        "period": str(payload.get("period") or period),
        "periodFallback": requested_period != str(payload.get("period") or period),
        "source": source,
        "ts": int(payload.get("ts") or 0),
        "cacheAgeMs": payload.get("cacheAgeMs"),
        "quality": quality,
        "warnings": warnings,
        "items": items,
    }


def market_ai_chart_bias(technical: dict[str, Any], stance: str) -> dict[str, str]:
    """Keep strict direction separate from a readable, non-executable weak bias."""
    strict = "up" if stance == "bullish" or technical.get("trend") == "up" else "down" if stance == "bearish" or technical.get("trend") == "down" else "neutral"
    if strict in {"up", "down"}:
        return {"signal": strict, "strength": "confirmed", "label": "图表已形成明确偏多方向" if strict == "up" else "图表已形成明确偏空方向", "gap": "图表方向已达到完整确认门槛。"}

    change = safe_decimal(technical.get("changePct"))
    ma5 = safe_decimal(technical.get("ma5"))
    ma20 = safe_decimal(technical.get("ma20"))
    last_close = safe_decimal(technical.get("lastClose"))
    if ma5 is not None and ma20 is not None and last_close is not None:
        if ma5 > ma20 and last_close >= ma5:
            remaining = max(Decimal("0"), Decimal("1.5") - max(change or Decimal("0"), Decimal("0")))
            return {"signal": "up", "strength": "weak", "label": "图表呈轻微偏多排列", "gap": f"近20根涨幅距 +1.5% 完整确认门槛还差 {decimal_display(remaining)}pct。"}
        if ma5 < ma20 and last_close <= ma5:
            remaining = max(Decimal("0"), Decimal("1.5") - max(-(change or Decimal("0")), Decimal("0")))
            return {"signal": "down", "strength": "weak", "label": "图表呈轻微偏空排列", "gap": f"近20根跌幅距 -1.5% 完整确认门槛还差 {decimal_display(remaining)}pct。"}
    return {"signal": "neutral", "strength": "neutral", "label": "图表暂未形成偏向", "gap": "均线与近20根涨跌幅未同时达到明确方向条件。"}


def market_ai_gap_text(value: Decimal | None) -> str:
    return f"{decimal_display(value)}pct" if value is not None else "--"


def market_ai_evidence_gap(item: dict[str, Any], chart_signal: str) -> dict[str, Any]:
    key = str(item.get("key") or "")
    available = bool(item.get("available"))
    value = safe_decimal(item.get("value"))
    signal = str(item.get("signal") or "neutral")
    state = str(item.get("state") or "unavailable")
    label = str(item.get("label") or "交易结构数据")
    if not available or value is None:
        return {"key": key, "label": label, "value": str(item.get("value") or ""), "available": False, "state": state, "signal": signal, "statusLabel": "数据未获取", "threshold": "需要可用数据", "gap": "本次不参与方向确认", "contribution": "未获取，不参与本次判断", "upReady": False, "downReady": False}

    if key == "longShortAccountRatio":
        up_gap, down_gap = max(Decimal("0"), Decimal("1.05") - value), max(Decimal("0"), value - Decimal("0.95"))
        status = "偏多账户已确认" if signal == "up" else "偏空账户已确认" if signal == "down" else "多空账户接近平衡"
        gap = "已达到偏多账户门槛。" if signal == "up" else "已达到偏空账户门槛。" if signal == "down" else f"距偏多还差 {decimal_display(up_gap)}；距偏空还差 {decimal_display(down_gap)}。"
        threshold = "偏多 ≥ 1.05；偏空 ≤ 0.95"
        up_ready, down_ready = signal == "up", signal == "down"
    elif key == "takerVolume":
        up_gap, down_gap = max(Decimal("0"), Decimal("55") - value), max(Decimal("0"), value - Decimal("45"))
        status = "主动买入占优" if signal == "up" else "主动卖出占优" if signal == "down" else "主动买卖接近平衡"
        gap = "已达到主动买入门槛。" if signal == "up" else "已达到主动卖出门槛。" if signal == "down" else f"距买方确认还差 {market_ai_gap_text(up_gap)}；距卖方确认还差 {market_ai_gap_text(down_gap)}。"
        threshold = "偏多 ≥ 55%；偏空 ≤ 45%"
        up_ready, down_ready = signal == "up", signal == "down"
    elif key == "openInterest":
        participation_gap = max(Decimal("0"), Decimal("1") - value)
        status = "市场参与度增加" if state == "increasing" else "市场参与度减少" if state == "decreasing" else "市场参与度未确认"
        gap = "已达到参与度增加门槛，仅辅助确认。" if state == "increasing" else f"距参与度增加还差 {market_ai_gap_text(participation_gap)}；该项不单独决定方向。"
        threshold = "参与度增加 ≥ +1%（不单独决定方向）"
        up_ready = down_ready = state == "increasing"
    else:
        status, gap, threshold, up_ready, down_ready = "待确认", "当前无可用阈值说明。", "仅辅助判断", False, False

    if signal in {"up", "down"} and chart_signal in {"up", "down"}:
        contribution = "与图表方向同向" if signal == chart_signal else "与图表方向相反"
    elif signal in {"up", "down"}:
        contribution = "有方向，但图表尚未确认"
    elif key == "openInterest" and state == "increasing":
        contribution = "参与度增加，仅辅助确认"
    else:
        contribution = "当前不提供方向确认"
    return {"key": key, "label": label, "value": str(item.get("value") or ""), "available": True, "state": state, "signal": signal, "statusLabel": status, "threshold": threshold, "gap": gap, "contribution": contribution, "upReady": up_ready, "downReady": down_ready}


def market_ai_candidate_missing_evidence(evidence_gaps: list[dict[str, Any]], direction: str) -> list[dict[str, str]]:
    ready_key = "upReady" if direction == "up" else "downReady"
    return [
        {"key": str(item.get("key") or ""), "label": str(item.get("label") or "交易结构"), "detail": str(item.get("gap") or "等待该项确认。")}
        for item in evidence_gaps
        if isinstance(item, dict) and not bool(item.get(ready_key))
    ]


def market_ai_decision_reference(market: dict[str, Any], suggestion: dict[str, Any], stance: str, confidence: int) -> dict[str, Any]:
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    structure = market.get("tradingStructure") if isinstance(market.get("tradingStructure"), dict) else {}
    items = structure.get("items") if isinstance(structure.get("items"), list) else []
    chart_bias = market_ai_chart_bias(technical, stance)
    chart_signal = chart_bias["signal"] if chart_bias["strength"] == "confirmed" else "neutral"
    observed_signal = chart_bias["signal"]
    directional = [item for item in items if isinstance(item, dict) and item.get("available") and item.get("signal") in {"up", "down"}]
    aligned = [item for item in directional if item.get("signal") == chart_signal]
    conflicting = [item for item in directional if observed_signal in {"up", "down"} and item.get("signal") != observed_signal]
    participation = next((item for item in items if isinstance(item, dict) and item.get("key") == "openInterest" and item.get("state") == "increasing"), None)
    quality = str(structure.get("quality") or "unavailable")
    evidence_gaps = [market_ai_evidence_gap(item, observed_signal) for item in items if isinstance(item, dict)]
    if chart_signal in {"up", "down"} and len(aligned) >= 2 and quality == "complete":
        assessment = "confirmed"
        direction_layer = "confirmed"
        action = market_ai_suggestion_action(str(suggestion.get("action") or ""))
        if action not in {"consider_long", "consider_short"}:
            action = "consider_long" if chart_signal == "up" else "consider_short"
        evidence = [str(item.get("label") or "") for item in aligned]
        if participation:
            evidence.append("持仓增加")
        summary = f"图表方向与{'、'.join(evidence[:3])}同向，结构得到确认。"
    elif observed_signal in {"up", "down"} and conflicting:
        assessment = "conflict"
        direction_layer = "conflict"
        action = "wait_release"
        evidence = [str(item.get("label") or "") for item in conflicting]
        summary = f"{chart_bias['label']}，但与{'、'.join(evidence[:2])}出现分歧，等待更多确认。"
    elif observed_signal in {"up", "down"}:
        assessment = "weak_bias"
        direction_layer = "weak_bias"
        action = "wait_release"
        required = 2 - len(aligned) if chart_signal in {"up", "down"} else 2
        summary = f"{chart_bias['label']}，但尚缺 {max(required, 1)} 项同向交易结构确认；当前仅作观察，不作为买卖信号。"
    else:
        assessment = "insufficient"
        direction_layer = "neutral"
        action = "wait_release" if quality != "complete" or chart_signal == "neutral" else market_ai_suggestion_action(str(suggestion.get("action") or "observe"))
        if action in {"consider_long", "consider_short"}:
            action = "wait_release"
        summary = "当前图表与交易结构均处在中性或临界区；数据已获取，但尚未形成可确认的方向。"
    confidence_cap = 100 if assessment == "confirmed" else 55 if assessment == "weak_bias" else 50 if assessment == "conflict" else 45
    return {
        "action": action,
        "assessment": assessment,
        "directionLayer": direction_layer,
        "direction": observed_signal,
        "confidence": max(0, min(100, confidence if assessment == "confirmed" else min(confidence, confidence_cap))),
        "summary": summary,
        "condition": market_ai_safe_text(suggestion.get("condition"), 500) or "等待价格、量能与交易结构同步确认。",
        "invalidation": market_ai_safe_text(suggestion.get("invalidation"), 500) or "图表结构或交易统计出现明显变化后重新阅读。",
        "dataQuality": quality,
        "evidence": [item for item in items if isinstance(item, dict)],
        "chart": chart_bias,
        "evidenceGaps": evidence_gaps,
        "periods": {
            "chart": str(technical.get("bar") or ""),
            "structureRequested": str(structure.get("requestedPeriod") or ""),
            "structureEffective": str(structure.get("period") or ""),
            "structureFallback": bool(structure.get("periodFallback")),
        },
    }


def market_ai_safe_fallback_reason(reason: str) -> str:
    """Return an end-user explanation without exposing provider exception text."""
    if "LLM 未启用" in str(reason):
        return "LLM 未启用，已使用规则化指标解读。"
    if "LLM 分析失败" in str(reason):
        return "LLM 分析失败，已使用规则化指标解读。"
    if "行情读取规则无效" in str(reason):
        return "行情读取规则无效，已使用规则化指标解读。"
    return "本次报告使用规则化指标解读。"


def market_ai_confidence_explanation(
    market: dict[str, Any],
    source: str,
    confidence: int,
    decision: dict[str, Any],
    fallback_reason: str = "",
) -> dict[str, Any]:
    """Explain the existing confidence and decision rules without recalculating them."""
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    structure = market.get("tradingStructure") if isinstance(market.get("tradingStructure"), dict) else {}
    chart = decision.get("chart") if isinstance(decision.get("chart"), dict) else {}
    chart_signal = str(chart.get("signal") or ("up" if technical.get("trend") == "up" else "down" if technical.get("trend") == "down" else "neutral"))
    assessment = str(decision.get("assessment") or "insufficient")
    quality = str(decision.get("dataQuality") or structure.get("quality") or "unavailable")
    source_is_fallback = source == "metric-fallback"
    source_label = "指标降级" if source_is_fallback else "AI 分析"
    source_reason = market_ai_safe_fallback_reason(fallback_reason) if source_is_fallback else "本次报告由当前图表快照与交易结构证据生成。"
    direction_label = str(chart.get("label") or ("图表方向偏多" if chart_signal == "up" else "图表方向偏空" if chart_signal == "down" else "图表暂未形成明确方向"))
    confirmation_label = "结构确认" if assessment == "confirmed" else "短线弱偏向" if assessment == "weak_bias" else "信号分歧" if assessment == "conflict" else "证据待确认"
    availability_label = "交易数据已获取" if quality == "complete" else "交易数据部分可用" if quality == "partial" else "交易数据待确认"
    thresholds = {
        "longShortAccountRatio": "1.05 以上才视为多空账户偏多，0.95 以下才视为偏空。",
        "takerVolume": "主动买入占比 55% 以上才视为买入较强，45% 以下才视为卖出较强。",
        "openInterest": "持仓增减在 ±1% 内视为平稳；持仓增加只辅助确认参与度，不单独判断方向。",
    }
    raw_evidence = decision.get("evidenceGaps") if isinstance(decision.get("evidenceGaps"), list) else []
    evidence: list[dict[str, Any]] = []
    for item in raw_evidence:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "")
        evidence.append({
            "key": key,
            "label": str(item.get("label") or "交易结构数据"),
            "value": str(item.get("value") or ""),
            "state": str(item.get("state") or "unavailable"),
            "available": bool(item.get("available")),
            "contribution": str(item.get("contribution") or "当前不提供方向确认"),
            "rule": thresholds.get(key, "仅作为本次图表快照的辅助证据。"),
            "threshold": str(item.get("threshold") or ""),
            "gap": str(item.get("gap") or ""),
            "statusLabel": str(item.get("statusLabel") or "待确认"),
        })
    return {
        "referenceValue": max(0, min(100, confidence)),
        "referenceMeaning": "表示本次行情阅读的证据充分程度，不代表价格涨跌概率或收益结果。",
        "source": source,
        "sourceLabel": source_label,
        "sourceReason": source_reason,
        "chartDirection": {"signal": chart_signal, "label": direction_label, "gap": str(chart.get("gap") or "")},
        "confirmation": {"assessment": assessment, "label": confirmation_label, "summary": str(decision.get("summary") or "")},
        "dataAvailability": {"quality": quality, "label": availability_label},
        "periods": decision.get("periods") if isinstance(decision.get("periods"), dict) else {},
        "evidence": evidence[:3],
    }


def market_ai_observation_levels(market: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    structure = market.get("tradingStructure") if isinstance(market.get("tradingStructure"), dict) else {}
    snapshot = market.get("chartSnapshot") if isinstance(market.get("chartSnapshot"), dict) else {}
    instrument = market.get("instrument") if isinstance(market.get("instrument"), dict) else {}
    low = safe_decimal(technical.get("recent20Low"))
    high = safe_decimal(technical.get("recent20High"))
    bar = str(technical.get("bar") or snapshot.get("bar") or "当前")
    base = {
        "instId": str(instrument.get("instId") or ""),
        "bar": bar,
        "snapshotId": str(snapshot.get("snapshotId") or ""),
        "snapshotTs": int(snapshot.get("snapshotTs") or 0),
        "dataQuality": str(structure.get("quality") or "unavailable"),
    }
    if low is None or high is None or low <= 0 or high <= low:
        return {
            **base,
            "available": False,
            "status": "unavailable",
            "reason": "本次图表快照缺少可用的近20根价格区间，暂不显示条件水位。",
        }
    if str(decision.get("action") or "") != "wait_release":
        return {
            **base,
            "available": False,
            "status": "not_needed",
            "reason": "当前报告已有方向参考，无需额外显示观望水位。",
        }

    items = structure.get("items") if isinstance(structure.get("items"), list) else []
    evidence_gaps = decision.get("evidenceGaps") if isinstance(decision.get("evidenceGaps"), list) else []
    by_key = {str(item.get("key") or ""): item for item in items if isinstance(item, dict)}
    taker = by_key.get("takerVolume") or {}
    open_interest = by_key.get("openInterest") or {}
    volume_context = str((technical.get("volume") or {}).get("context") or "unknown") if isinstance(technical.get("volume"), dict) else "unknown"
    volume_note = (
        "近期量能较前期放大"
        if volume_context == "expanding"
        else "当前量能平稳，突破后仍需确认"
        if volume_context == "normal"
        else "当前量能缩减，突破后需先改善"
    )
    taker_state = str(taker.get("state") or "unavailable")
    taker_available = bool(taker.get("available"))
    upper_taker_note = (
        "主动买卖数据暂未获取，不形成完整确认"
        if not taker_available
        else "主动买入保持占优"
        if taker_state == "active_buying_stronger"
        else "主动买卖需转为买入不弱势"
    )
    lower_taker_note = (
        "主动买卖数据暂未获取，不形成完整确认"
        if not taker_available
        else "主动卖出保持占优"
        if taker_state == "active_selling_stronger"
        else "主动买卖需转为卖出不弱势"
    )
    oi_state = str(open_interest.get("state") or "unavailable")
    participation_note = (
        "市场参与度增加，仅作参与确认，不决定方向"
        if oi_state == "increasing"
        else "市场参与度减少，突破后需继续确认"
        if oi_state == "decreasing"
        else "市场参与度暂未确认，不作为方向依据"
    )
    low_text = decimal_display(low)
    high_text = decimal_display(high)
    partial = str(structure.get("quality") or "unavailable") != "complete"
    last_close = safe_decimal(technical.get("lastClose"))
    current_range_note = (
        f"本次 {bar} 图表收盘价 {decimal_display(last_close)} 仍在 {low_text} – {high_text} 区间内，当前保持观望。"
        if last_close is not None and low <= last_close <= high
        else f"本次 {bar} 图表尚未给出可确认的区间外收盘，当前保持观望。"
    )
    confirmation_status = "awaiting_confirmation"
    confirmation_status_label = "缺少完整确认" if partial else "等待条件确认"
    confirmation_status_detail = (
        "交易结构部分可用；价格到达确认价后仍需补齐可用数据。"
        if partial
        else "确认价被触及不等于成立，仍需等待完整 K线、量能与交易结构共同确认。"
    )
    return_to_range = f"若突破后重新回到 {low_text} – {high_text} 区间，候选方向失效，恢复观望。"
    common_close_requirement = "盘中触及或影线越过不算确认。"
    bullish_missing = market_ai_candidate_missing_evidence(evidence_gaps, "up")
    bearish_missing = market_ai_candidate_missing_evidence(evidence_gaps, "down")
    bullish_gap_note = "；".join(f"{item['label']}：{item['detail']}" for item in bullish_missing[:3]) or "交易结构已满足当前候选方向的辅助条件。"
    bearish_gap_note = "；".join(f"{item['label']}：{item['detail']}" for item in bearish_missing[:3]) or "交易结构已满足当前候选方向的辅助条件。"
    return {
        **base,
        "available": True,
        "status": "watch",
        "partialConfirmation": partial,
        "neutralRange": {
            "label": "观望区",
            "low": low_text,
            "high": high_text,
            "condition": f"价格仍在 {low_text} – {high_text} 区间内，暂不形成方向。",
        },
        "currentState": {
            "status": "watch",
            "label": "当前：保持观望",
            "summary": current_range_note,
        },
        "candidates": [
            {
                "key": "bullish",
                "tone": "bullish",
                "label": "偏多候选",
                "confirmationPrice": high_text,
                "priceMeaning": "条件确认价，不是直接成交价。",
                "requirements": [
                    {"label": "K线确认", "detail": f"等待完整一根 {bar} K线收在 {high_text} 上方。{common_close_requirement}"},
                    {"label": "量能要求", "detail": volume_note},
                    {"label": "交易结构", "detail": upper_taker_note},
                    {"label": "尚缺确认", "detail": bullish_gap_note},
                ],
                "missingEvidence": bullish_missing,
                "status": confirmation_status,
                "statusLabel": confirmation_status_label,
                "statusDetail": confirmation_status_detail,
                "invalidationStatus": "return_to_range_invalidates",
                "invalidation": return_to_range,
            },
            {
                "key": "bearish",
                "tone": "bearish",
                "label": "偏空候选",
                "confirmationPrice": low_text,
                "priceMeaning": "条件确认价，不是直接成交价。",
                "requirements": [
                    {"label": "K线确认", "detail": f"等待完整一根 {bar} K线收在 {low_text} 下方。{common_close_requirement}"},
                    {"label": "量能要求", "detail": volume_note},
                    {"label": "交易结构", "detail": lower_taker_note},
                    {"label": "尚缺确认", "detail": bearish_gap_note},
                ],
                "missingEvidence": bearish_missing,
                "status": confirmation_status,
                "statusLabel": confirmation_status_label,
                "statusDetail": confirmation_status_detail,
                "invalidationStatus": "return_to_range_invalidates",
                "invalidation": return_to_range,
            },
        ],
        "upper": {
            "label": "上方偏多观察线",
            "price": high_text,
            "condition": f"完成一根 {bar} K线收在 {high_text} 上方；{volume_note}；{upper_taker_note}。",
        },
        "lower": {
            "label": "下方偏空观察线",
            "price": low_text,
            "condition": f"完成一根 {bar} K线收在 {low_text} 下方；{volume_note}；{lower_taker_note}。",
        },
        "returnToRange": {
            "label": "回到区间",
            "condition": f"突破后重新回到 {low_text} – {high_text} 区间，恢复观望。",
        },
        "participationNote": participation_note,
    }


def market_ai_scenario_board(market: dict[str, Any], decision: dict[str, Any], observation_levels: dict[str, Any]) -> dict[str, Any]:
    """Turn a report snapshot into one readable state and two non-executable scenarios."""
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    bar = str(technical.get("bar") or observation_levels.get("bar") or "当前")
    last_close = safe_decimal(technical.get("lastClose"))
    low = safe_decimal(technical.get("recent20Low"))
    high = safe_decimal(technical.get("recent20High"))
    evidence_gaps = decision.get("evidenceGaps") if isinstance(decision.get("evidenceGaps"), list) else []
    unavailable = [item for item in evidence_gaps if isinstance(item, dict) and not bool(item.get("available"))]
    available_directional = [item for item in evidence_gaps if isinstance(item, dict) and bool(item.get("available")) and str(item.get("signal") or "") in {"up", "down"}]
    strongest_clue = available_directional[0] if available_directional else None
    range_available = low is not None and high is not None and low > 0 and high > low
    position_pct = None
    if range_available and last_close is not None:
        position_pct = max(Decimal("0"), min(Decimal("100"), ((last_close - low) / (high - low)) * Decimal("100")))
    position_label = "区间中部"
    if position_pct is not None and position_pct <= Decimal("33"):
        position_label = "靠近下沿"
    elif position_pct is not None and position_pct >= Decimal("67"):
        position_label = "靠近上沿"

    def candidate(direction: str, level: Decimal | None, label: str) -> dict[str, Any]:
        missing = market_ai_candidate_missing_evidence(evidence_gaps, direction)
        limited = bool(unavailable)
        is_confirmed = str(decision.get("directionLayer") or "") == "confirmed" and str(decision.get("direction") or "") == direction
        price = decimal_display(level) if level is not None else "--"
        gap_value = abs((level or Decimal("0")) - last_close) if level is not None and last_close is not None else None
        return {
            "key": "bullish" if direction == "up" else "bearish",
            "label": label,
            "tone": "bullish" if direction == "up" else "bearish",
            "status": "confirmed" if is_confirmed else "limited" if limited else "watch",
            "statusLabel": "方向已确认" if is_confirmed else "关键数据缺失" if limited else "等待条件确认",
            "confirmationPrice": price,
            "priceCondition": f"等待完整一根 {bar} K线收在 {price} {'上方' if direction == 'up' else '下方'}；盘中触及不算确认。" if level is not None else "本次快照缺少条件确认价。",
            "distance": decimal_display(gap_value) if gap_value is not None else "--",
            "distanceLabel": f"距{'上' if direction == 'up' else '下'}方确认线",
            "missingEvidence": missing,
            "limitations": [
                {
                    "label": str(item.get("label") or "交易结构数据"),
                    "detail": "数据未获取；即使价格条件达成，也不能形成完整方向确认。",
                }
                for item in unavailable
            ],
            "invalidation": f"突破后重新回到 {decimal_display(low)} – {decimal_display(high)} 区间，恢复观望。" if range_available else "图表结构变化后需要重新阅读。",
        }

    direction_layer = str(decision.get("directionLayer") or "neutral")
    if direction_layer == "confirmed":
        state_label = "方向已确认"
    elif range_available and last_close is not None and low <= last_close <= high:
        state_label = "价格仍在观察区"
    elif direction_layer == "weak_bias":
        state_label = "出现短线偏向，等待结构确认"
    elif direction_layer == "conflict":
        state_label = "图表与结构信号分歧"
    else:
        state_label = "尚未形成可确认方向"
    return {
        "version": 1,
        "evidenceScore": coerce_int(decision.get("confidence"), 0, 0, 100),
        "scoreMeaning": "规则化场景证据度，仅衡量本次快照对当前场景的支持程度，不是价格概率或收益预期。",
        "marketState": {
            "label": state_label,
            "summary": str(decision.get("summary") or "等待图表与交易结构共同确认。"),
            "price": decimal_display(last_close) if last_close is not None else "--",
            "rangeLow": decimal_display(low) if low is not None else "--",
            "rangeHigh": decimal_display(high) if high is not None else "--",
            "positionPct": decimal_display(position_pct) if position_pct is not None else "--",
            "positionLabel": position_label if position_pct is not None else "区间位置待确认",
            "strongestClue": {
                "label": str(strongest_clue.get("label") or ""),
                "detail": f"{strongest_clue.get('statusLabel') or '出现方向线索'}；{strongest_clue.get('contribution') or '尚未形成完整确认。'}",
            } if strongest_clue else None,
        },
        "dataLimitations": [
            {
                "label": str(item.get("label") or "交易结构数据"),
                "detail": "本次数据未获取，不能参与完整多空确认。",
            }
            for item in unavailable
        ],
        "candidates": [
            candidate("up", high, "偏多条件观察"),
            candidate("down", low, "偏空条件观察"),
        ],
        "snapshot": {"bar": bar, "snapshotId": str(observation_levels.get("snapshotId") or "")},
    }


def market_ai_direction_summary(market: dict[str, Any], decision: dict[str, Any], scenario_board: dict[str, Any]) -> dict[str, Any]:
    """Return the single, direction-first reading outcome for a report snapshot."""
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    snapshot = scenario_board.get("snapshot") if isinstance(scenario_board.get("snapshot"), dict) else {}
    market_state = scenario_board.get("marketState") if isinstance(scenario_board.get("marketState"), dict) else {}
    candidates = scenario_board.get("candidates") if isinstance(scenario_board.get("candidates"), list) else []
    limitations = scenario_board.get("dataLimitations") if isinstance(scenario_board.get("dataLimitations"), list) else []
    bar = str(snapshot.get("bar") or technical.get("bar") or "当前")
    direction = str(decision.get("direction") or "neutral")
    confirmed = str(decision.get("directionLayer") or "") == "confirmed" and direction in {"up", "down"}
    by_direction = {
        "up": next((item for item in candidates if isinstance(item, dict) and str(item.get("key") or "") == "bullish"), {}),
        "down": next((item for item in candidates if isinstance(item, dict) and str(item.get("key") or "") == "bearish"), {}),
    }
    strongest_clue = market_state.get("strongestClue") if isinstance(market_state.get("strongestClue"), dict) else {}
    clue_text = str(strongest_clue.get("detail") or "")
    evidence_gaps = decision.get("evidenceGaps") if isinstance(decision.get("evidenceGaps"), list) else []
    matching_evidence = [
        item for item in evidence_gaps
        if isinstance(item, dict) and bool(item.get("available")) and str(item.get("signal") or "") == direction
    ]
    conflicting_evidence = [
        item for item in evidence_gaps
        if isinstance(item, dict) and bool(item.get("available")) and str(item.get("signal") or "") in {"up", "down"} and str(item.get("signal") or "") != direction
    ]

    if confirmed:
        headline = "偏多观察" if direction == "up" else "偏空观察"
        return {
            "version": 1,
            "headline": headline,
            "state": "confirmed",
            "statusLabel": "方向已确认",
            "direction": direction,
            "tone": "bullish" if direction == "up" else "bearish",
            "reason": str(decision.get("summary") or "图表与交易结构已满足当前方向确认条件。"),
            "metLabel": "已满足",
            "metCondition": "图表方向与至少两项同向交易结构已完成确认。",
            "missingLabel": "维持条件",
            "missingCondition": f"后续完整 {bar} K线与交易结构仍需保持同向；结构变化后重新阅读。",
            "nextCondition": f"继续以完整 {bar} K线与交易结构是否保持同向作为后续确认；结构变化后重新阅读。",
            "confirmationPrice": str(market_state.get("price") or "--"),
            "confirmationPriceLabel": "当前确认快照价",
            "snapshot": {"bar": bar, "snapshotId": str(snapshot.get("snapshotId") or "")},
            "readOnly": "基于当前行情快照的方向观察，不构成下单指令。",
        }

    preferred_direction = direction if direction in {"up", "down"} else ""
    if not preferred_direction:
        clue_label = str(strongest_clue.get("label") or "")
        preferred_direction = "down" if "卖" in clue_label else "up" if "买" in clue_label else ""
    candidate = by_direction.get(preferred_direction) if preferred_direction else None
    if not isinstance(candidate, dict) or not candidate:
        candidate = next((item for item in candidates if isinstance(item, dict)), {})
    candidate_direction = "up" if str(candidate.get("key") or "") == "bullish" else "down" if str(candidate.get("key") or "") == "bearish" else "neutral"
    condition = str(candidate.get("priceCondition") or "等待完整 K线与交易结构共同确认。")
    limitation_details = list(dict.fromkeys(
        f"{item.get('label') or '交易数据'}：{item.get('detail') or '关键数据未获取，不能完成方向确认。'}"
        for item in limitations
        if isinstance(item, dict)
    ))
    limitation_text = "；".join(limitation_details[:2])
    reason = clue_text or str(market_state.get("summary") or decision.get("summary") or "当前尚未形成可确认方向。")
    matching_labels = "、".join(str(item.get("statusLabel") or item.get("label") or "同向结构") for item in matching_evidence[:2])
    missing_items = market_ai_candidate_missing_evidence(evidence_gaps, candidate_direction) if candidate_direction in {"up", "down"} else []
    missing_structure = f"还缺 {len(missing_items)} 项同向交易结构确认。" if missing_items else "交易结构仍需与图表保持同向。"
    if limitation_text:
        headline, state, status_label = "方向暂不可判定", "limited", "缺关键数据"
        met_condition = matching_labels or "图表行情快照已就绪，但方向确认所需交易结构不完整。"
        missing_condition = f"{condition}；{limitation_text}"
    elif str(decision.get("assessment") or "") == "conflict" or conflicting_evidence:
        headline, state, status_label = "无明确方向", "conflict", "信号分歧"
        met_condition = "图表与交易结构出现相反方向的线索。"
        missing_condition = "等待图表与至少两项交易结构重新形成同向确认。"
    elif candidate_direction in {"up", "down"} and matching_evidence:
        headline = "短线偏多（未确认）" if candidate_direction == "up" else "短线偏空（未确认）"
        state, status_label = "weak_bias", "仍需确认"
        met_condition = matching_labels
        missing_condition = f"{condition}；{missing_structure}"
    else:
        headline, state, status_label = "无明确方向", "neutral", "暂无同向证据"
        met_condition = "当前图表与交易结构均未形成可核对的同向线索。"
        missing_condition = "等待价格脱离观察区，并出现至少两项同向交易结构确认。"
    return {
        "version": 1,
        "headline": headline,
        "state": state,
        "statusLabel": status_label,
        "direction": candidate_direction,
        "tone": "bearish" if candidate_direction == "down" else "bullish" if candidate_direction == "up" else "neutral",
        "reason": reason,
        "metLabel": "已满足",
        "metCondition": met_condition,
        "missingLabel": "还差" if state in {"weak_bias", "limited"} else "等待",
        "missingCondition": missing_condition,
        "nextCondition": missing_condition,
        "confirmationPrice": str(candidate.get("confirmationPrice") or "--"),
        "confirmationPriceLabel": "待验证价" if state == "limited" else "下方确认价" if candidate_direction == "down" else "上方确认价" if candidate_direction == "up" else "下一确认价",
        "snapshot": {"bar": bar, "snapshotId": str(snapshot.get("snapshotId") or "")},
        "readOnly": "基于当前行情快照的方向观察，不构成下单指令。",
    }


def market_ai_macro_hash(snapshot: dict[str, Any]) -> str:
    material = {
        "items": [
            {
                "source": item.get("source"),
                "kind": item.get("kind"),
                "title": item.get("title"),
                "publishedAt": item.get("publishedAt"),
                "scheduledAt": item.get("scheduledAt"),
                "value": item.get("value"),
                "previousValue": item.get("previousValue"),
            }
            for item in snapshot.get("items", [])
            if isinstance(item, dict)
        ],
        "warnings": snapshot.get("warnings") or [],
    }
    return hashlib.sha256(json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]


def market_ai_outlook_cache_key(
    market: dict[str, Any], macro: dict[str, Any], analysis_profile: dict[str, Any] | None = None
) -> str:
    freshness = market.get("freshness") if isinstance(market.get("freshness"), dict) else {}
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    instrument = market.get("instrument") if isinstance(market.get("instrument"), dict) else {}
    chart_snapshot = market.get("chartSnapshot") if isinstance(market.get("chartSnapshot"), dict) else {}
    trading_structure = market.get("tradingStructure") if isinstance(market.get("tradingStructure"), dict) else {}
    price_plan = market.get("pricePlan") if isinstance(market.get("pricePlan"), dict) else {}
    multi_timeframe = market.get("multiTimeframeTrend") if isinstance(market.get("multiTimeframeTrend"), dict) else {}
    multi_periods = multi_timeframe.get("periods") if isinstance(multi_timeframe.get("periods"), list) else []
    profile = analysis_profile or compile_okx_market_reading_context()["metadata"]
    return json.dumps(
        {
            "instId": instrument.get("instId"),
            "bar": technical.get("bar"),
            "snapshotId": chart_snapshot.get("snapshotId"),
            "lastCandleTs": technical.get("lastTs"),
            "tickerTs": (freshness.get("ticker") or {}).get("ts") if isinstance(freshness.get("ticker"), dict) else 0,
            "macroHash": market_ai_macro_hash(macro),
            "tradingStructure": {
                "period": trading_structure.get("period"),
                "ts": trading_structure.get("ts"),
                "quality": trading_structure.get("quality"),
                "items": trading_structure.get("items"),
            },
            "pricePlan": {
                "version": price_plan.get("version"),
                "entryBasis": price_plan.get("entryBasis"),
                "entryQuoteTs": price_plan.get("entryQuoteTs"),
                "lastClosedTs": price_plan.get("lastClosedTs"),
                "source": price_plan.get("source"),
                "status": price_plan.get("status"),
                "direction": price_plan.get("direction"),
                "entryPrice": price_plan.get("entryPrice"),
                "stopPrice": price_plan.get("stopPrice"),
                "targetPrice": price_plan.get("targetPrice"),
                "bidPx": price_plan.get("bidPx"),
                "askPx": price_plan.get("askPx"),
            },
            "multiTimeframe": [
                {
                    "key": item.get("key"),
                    "bar": item.get("bar"),
                    "status": item.get("status"),
                    "source": item.get("source"),
                    "lastCandleTs": item.get("lastCandleTs"),
                }
                for item in multi_periods
                if isinstance(item, dict)
            ],
            "analysisProfile": {
                "id": profile.get("id"),
                "profileVersion": profile.get("profileVersion"),
                "contentHash": profile.get("contentHash"),
            },
            "evaluationSamples": market.get("evaluationSamples") or {},
            "evaluationContextVersion": 2,
            "promptVersion": MARKET_AI_OUTLOOK_PROMPT_VERSION,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def market_ai_safe_text(value: Any, limit: int = 800) -> str:
    text = str(value or "").strip()
    blocked_patterns = [
        "必须买入",
        "必须卖出",
        "必须做多",
        "必须做空",
        "保证盈利",
        "稳赚",
        "立即下单",
        "已经下单",
        "立即开仓",
        "立即平仓",
        "入场做多",
        "入场做空",
        "guaranteed profit",
        "must buy",
        "must sell",
    ]
    lowered = text.lower()
    if any(pattern in lowered for pattern in blocked_patterns):
        return "原始输出包含过度确定或交易执行措辞，已改为保守观察。"
    return text[:limit]


def market_ai_safe_list(value: Any, limit: int = 6, item_limit: int = 260) -> list[str]:
    if not isinstance(value, list):
        return []
    return [market_ai_safe_text(item, item_limit) for item in value[:limit] if market_ai_safe_text(item, item_limit)]


def market_ai_stance_label(value: str) -> str:
    return value if value in {"bullish", "bearish", "neutral", "wait"} else "neutral"


def market_ai_suggestion_action(value: str) -> str:
    return value if value in {"observe", "wait_release", "consider_long", "consider_short", "avoid"} else "observe"


def market_ai_report_horizon_from_evidence(target: dict[str, Any], horizon_evidence: dict[str, Any], macro: dict[str, Any]) -> dict[str, Any]:
    key = str(target.get("key") or "")
    label = str(target.get("label") or market_ai_horizon_label(key))
    bars = horizon_evidence.get("bars") if isinstance(horizon_evidence.get("bars"), dict) else {}
    target_bars = [str(item) for item in target.get("bars") or [] if str(item) in bars]
    selected_bar = target_bars[-1] if target_bars else ""
    selected_payload = bars.get(selected_bar) if selected_bar and isinstance(bars.get(selected_bar), dict) else {}
    summary = selected_payload.get("summary") if isinstance(selected_payload.get("summary"), dict) else {}
    trend = str(summary.get("trend") or "range")
    last_close = str(summary.get("lastClose") or "--")
    high = str(summary.get("recent20High") or "")
    low = str(summary.get("recent20Low") or "")
    range_pct = str(summary.get("recent20RangePct") or "--")
    has_warnings = bool(macro.get("warnings") or horizon_evidence.get("warnings"))
    watch = [item for item in [f"关注 {selected_bar or '当前周期'} 近20根高点 {high}" if high else "", f"关注 {selected_bar or '当前周期'} 近20根低点 {low}" if low else ""] if item]
    if key == "today":
        watch.append("关注美股时段、美元利率预期及宏观数据发布时间。")
    return {
        "key": key,
        "label": label,
        "bias": market_ai_report_bias(trend, has_warnings),
        "confidence": 35 if has_warnings else 48 if trend in {"up", "down"} else 42,
        "summary": f"{label}参考 {selected_bar or '当前'} K线，最新价 {last_close}，近20根区间约 {range_pct}%，整体偏{trend}。",
        "watch": watch[:4] or ["等待更多价格与量能数据后再重评。"],
        "risk": "短周期价格噪音较大，本段只作为行情阅读参考。" if key == "15m" else "宏观消息和成交量变化可能快速改变日内结构。" if key == "today" else "小时级走势需要结合后续 K线收盘与量能延续观察。",
    }


def fallback_market_ai_report(market: dict[str, Any], macro: dict[str, Any], stance: str, confidence: int, summary: str, warning_lines: list[str]) -> dict[str, Any]:
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    ticker = market.get("ticker") if isinstance(market.get("ticker"), dict) else {}
    trend = str(technical.get("trend") or "range")
    high = str(technical.get("recent20High") or "")
    low = str(technical.get("recent20Low") or "")
    return {
        "overall": {
            "view": market_ai_report_bias(trend, bool(warning_lines)),
            "confidence": confidence,
            "summary": summary,
        },
        "horizons": [],
        "report": {
            "keyFactors": [
                f"当前 {technical.get('bar') or '--'} K线结构：{trend}",
                f"近20根区间：{technical.get('recent20Low') or '--'} - {technical.get('recent20High') or '--'}",
                f"量能状态：{(technical.get('volume') or {}).get('context', 'unknown') if isinstance(technical.get('volume'), dict) else 'unknown'}",
            ],
            "focus": [item for item in [f"上方关注近20根高点 {high}" if high else "", f"下方关注近20根低点 {low}" if low else "", "等待当前周期 K线收线与量能确认。"] if item],
            "reassess": [item for item in [f"价格有效脱离 {low}-{high} 区间" if high and low else "", "当前图表出现新 K线后手动刷新分析"] if item] or ["当前图表 K线结构变化后重评。"],
            "riskNotes": warning_lines[:6] or ["仅供用户阅读参考，不构成投资建议。"],
        },
    }


def fallback_market_ai_outlook(
    market: dict[str, Any], macro: dict[str, Any], reason: str = "", analysis_profile: dict[str, Any] | None = None
) -> dict[str, Any]:
    technical = market.get("technical") if isinstance(market.get("technical"), dict) else {}
    ticker = market.get("ticker") if isinstance(market.get("ticker"), dict) else {}
    trend = str(technical.get("trend") or "range")
    stance = "neutral"
    if trend == "up":
        stance = "bullish"
    elif trend == "down":
        stance = "bearish"
    elif market.get("warnings") or macro.get("warnings"):
        stance = "wait"
    last = str(ticker.get("last") or technical.get("lastClose") or "")
    high = str(technical.get("recent20High") or "")
    low = str(technical.get("recent20Low") or "")
    safe_reason = market_ai_safe_fallback_reason(reason) if reason else ""
    warning_lines = list(dict.fromkeys(str(item) for item in [*(macro.get("warnings") or []), *(market.get("warnings") or []), safe_reason] if str(item).strip()))
    summary = f"基于当前 {technical.get('bar') or ''} K线，价格处于{trend}结构，最新价 {last or '--'}。"
    if macro.get("warnings"):
        summary += " 宏观数据存在缺口，本次只适合作为保守观察。"
    confidence = 45 if trend in {"up", "down"} and not warning_lines else 35
    report_payload = fallback_market_ai_report(market, macro, stance, confidence, summary, warning_lines)
    suggestion = {
        "action": "observe" if stance != "wait" else "wait_release",
        "condition": "只在价格与成交量继续确认时观察，不把本结果视为下单指令。",
        "invalidation": f"跌破近20根低点 {low} 或突破失败后回落则观点失效。" if stance == "bullish" and low else f"重新站回近20根高点 {high} 后需要重评。" if stance == "bearish" and high else "宏观事件发布或 K线结构改变后需要重新分析。",
        "riskNotes": warning_lines[:6] or ["本功能只提供行情观察，不会提交订单。"],
    }
    decision = market_ai_decision_reference(market, suggestion, stance, confidence)
    observation_levels = market_ai_observation_levels(market, decision)
    scenario_board = market_ai_scenario_board(market, decision, observation_levels)
    confidence_explanation = market_ai_confidence_explanation(market, "metric-fallback", int(decision.get("confidence") or 0), decision, reason)
    return {
        "status": "fallback",
        "source": "metric-fallback",
        "promptVersion": MARKET_AI_OUTLOOK_PROMPT_VERSION,
        "analysisProfile": analysis_profile or compile_okx_market_reading_context()["metadata"],
        "generatedAt": now_ms(),
        "stance": stance,
        "confidence": confidence,
        "summary": summary,
        **report_payload,
        "macro": {
            "bias": "unknown" if macro.get("warnings") else "neutral",
            "drivers": [market_ai_safe_text(item.get("summary"), 220) for item in macro.get("items", [])[:4] if isinstance(item, dict)],
            "uncertainty": "宏观数据仅来自可获取的公开来源；缺失项不会由模型补齐。",
        },
        "technical": {
            "trend": trend,
            "keyLevels": [item for item in [f"近20根高点 {high}" if high else "", f"近20根低点 {low}" if low else ""] if item],
            "volumeRead": f"近期成交量状态：{(technical.get('volume') or {}).get('context', 'unknown')}" if isinstance(technical.get("volume"), dict) else "成交量数据不足。",
            "notes": [f"近20根区间 {technical.get('recent20RangePct') or '--'}%", f"24h 涨跌 {ticker.get('change24hPct') or '--'}%"],
        },
        "suggestion": suggestion,
        "tradingStructure": market.get("tradingStructure") or {},
        "multiTimeframeTrend": market.get("multiTimeframeTrend") or {},
        "pricePlan": market.get("pricePlan") or {},
        "decision": decision,
        "confidenceExplanation": confidence_explanation,
        "observationLevels": observation_levels,
        "scenarioBoard": scenario_board,
        "directionSummary": market_ai_direction_summary(market, decision, scenario_board),
        "sources": market_ai_outlook_sources(macro, market),
        "warnings": warning_lines[:8],
    }


def market_ai_outlook_sources(macro: dict[str, Any], market: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for item in macro.get("items", [])[:8]:
        if not isinstance(item, dict):
            continue
        sources.append(
            {
                "source": item.get("source") or "",
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "publishedAt": item.get("publishedAt") or "",
                "scheduledAt": item.get("scheduledAt") or "",
                "cacheAgeMs": item.get("cacheAgeMs"),
                "official": bool(item.get("official")),
            }
        )
    freshness = market.get("freshness") if isinstance(market.get("freshness"), dict) else {}
    for key, label in [("ticker", "OKX Ticker"), ("candles", "OKX K线")]:
        meta = freshness.get(key) if isinstance(freshness.get(key), dict) else {}
        sources.append({"source": meta.get("source") or "", "title": label, "url": "https://www.okx.com/docs-v5/zh/#order-book-trading-market-data", "cacheAgeMs": meta.get("cacheAgeMs")})
    structure = market.get("tradingStructure") if isinstance(market.get("tradingStructure"), dict) else {}
    if structure:
        sources.append({"source": structure.get("source") or "", "title": "OKX 合约交易统计", "url": "https://www.okx.com/docs-v5/zh/#trading-statistics", "cacheAgeMs": structure.get("cacheAgeMs")})
    return sources


def normalize_market_ai_horizon_list(value: Any, market: dict[str, Any], macro: dict[str, Any]) -> list[dict[str, Any]]:
    rows_by_key: dict[str, dict[str, Any]] = {}
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if key not in MARKET_AI_HORIZON_BARS:
                continue
            rows_by_key[key] = {
                "key": key,
                "label": market_ai_horizon_label(key),
                "bias": market_ai_safe_text(item.get("bias"), 80) or "震荡观察",
                "confidence": coerce_int(item.get("confidence"), 0, 0, 100),
                "summary": market_ai_safe_text(item.get("summary"), 500),
                "watch": market_ai_safe_list(item.get("watch"), 5, 180),
                "risk": market_ai_safe_text(item.get("risk"), 300),
            }
    # 预测区只呈现模型依据本次图表快照实际给出的周期；缺失周期不补写，避免把
    # 指标兜底包装成确定的未来判断。
    return [rows_by_key[key] for key in ("15m", "1h", "today") if key in rows_by_key]


def normalize_market_ai_report_payload(value: Any, market: dict[str, Any], macro: dict[str, Any], fallback_report: dict[str, Any]) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "keyFactors": market_ai_safe_list(raw.get("keyFactors"), 8, 220) or fallback_report.get("keyFactors") or [],
        "focus": market_ai_safe_list(raw.get("focus"), 8, 220) or fallback_report.get("focus") or [],
        "reassess": market_ai_safe_list(raw.get("reassess"), 8, 220) or fallback_report.get("reassess") or [],
        "riskNotes": market_ai_safe_list(raw.get("riskNotes"), 8, 220) or fallback_report.get("riskNotes") or ["仅供用户阅读参考，不构成投资建议。"],
    }


def normalize_market_ai_outlook(
    parsed: dict[str, Any],
    market: dict[str, Any],
    macro: dict[str, Any],
    config: dict[str, Any],
    completion: dict[str, Any],
    analysis_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    confidence = coerce_int(parsed.get("confidence"), 0, 0, 100)
    suggestion = parsed.get("suggestion") if isinstance(parsed.get("suggestion"), dict) else {}
    macro_payload = parsed.get("macro") if isinstance(parsed.get("macro"), dict) else {}
    technical_payload = parsed.get("technical") if isinstance(parsed.get("technical"), dict) else {}
    stance = market_ai_stance_label(str(parsed.get("stance") or ""))
    summary = market_ai_safe_text(parsed.get("summary"), 900)
    fallback_report = fallback_market_ai_report(market, macro, stance, confidence, summary, [*(macro.get("warnings") or []), *(market.get("warnings") or [])])
    overall_payload = parsed.get("overall") if isinstance(parsed.get("overall"), dict) else {}
    normalized_suggestion = {
        "action": market_ai_suggestion_action(str(suggestion.get("action") or "")),
        "condition": market_ai_safe_text(suggestion.get("condition"), 500),
        "invalidation": market_ai_safe_text(suggestion.get("invalidation"), 500),
        "riskNotes": market_ai_safe_list(suggestion.get("riskNotes"), 8, 260),
    }
    decision = market_ai_decision_reference(market, normalized_suggestion, stance, confidence)
    observation_levels = market_ai_observation_levels(market, decision)
    scenario_board = market_ai_scenario_board(market, decision, observation_levels)
    result = {
        "status": "ok",
        "source": "llm-market-ai-outlook",
        "provider": config.get("provider"),
        "model": config.get("model"),
        "promptVersion": MARKET_AI_OUTLOOK_PROMPT_VERSION,
        "analysisProfile": analysis_profile or compile_okx_market_reading_context()["metadata"],
        "generatedAt": now_ms(),
        "stance": stance,
        "confidence": confidence,
        "summary": summary,
        "overall": {
            "view": market_ai_safe_text(overall_payload.get("view"), 80) or (fallback_report.get("overall") or {}).get("view") or market_ai_report_bias(stance),
            "confidence": coerce_int(overall_payload.get("confidence"), confidence, 0, 100),
            "summary": market_ai_safe_text(overall_payload.get("summary"), 900) or summary or (fallback_report.get("overall") or {}).get("summary") or "",
        },
        "horizons": normalize_market_ai_horizon_list(parsed.get("horizons"), market, macro),
        "report": normalize_market_ai_report_payload(parsed.get("report"), market, macro, fallback_report.get("report") or {}),
        "macro": {
            "bias": market_ai_safe_text(macro_payload.get("bias"), 80),
            "drivers": market_ai_safe_list(macro_payload.get("drivers"), 6, 260),
            "uncertainty": market_ai_safe_text(macro_payload.get("uncertainty"), 500),
        },
        "technical": {
            "trend": market_ai_safe_text(technical_payload.get("trend"), 80),
            "keyLevels": market_ai_safe_list(technical_payload.get("keyLevels"), 6, 160),
            "volumeRead": market_ai_safe_text(technical_payload.get("volumeRead"), 260),
            "notes": market_ai_safe_list(technical_payload.get("notes"), 6, 220),
        },
        "suggestion": normalized_suggestion,
        "tradingStructure": market.get("tradingStructure") or {},
        "multiTimeframeTrend": market.get("multiTimeframeTrend") or {},
        "pricePlan": market.get("pricePlan") or {},
        "decision": decision,
        "confidenceExplanation": market_ai_confidence_explanation(market, "llm-market-ai-outlook", int(decision.get("confidence") or 0), decision),
        "observationLevels": observation_levels,
        "scenarioBoard": scenario_board,
        "directionSummary": market_ai_direction_summary(market, decision, scenario_board),
        "sources": market_ai_outlook_sources(macro, market),
        "warnings": list(dict.fromkeys([*(macro.get("warnings") or []), *(market.get("warnings") or []), *market_ai_safe_list(parsed.get("warnings"), 8, 260)])),
    }
    return attach_llm_completion_meta(result, completion)


def market_ai_outlook_prompt(market: dict[str, Any], macro: dict[str, Any], skill_context: dict[str, Any] | None = None) -> str:
    skill_context = skill_context or compile_okx_market_reading_context()
    payload = {
        "task": "write_okx_perpetual_market_reading_report",
        "promptVersion": MARKET_AI_OUTLOOK_PROMPT_VERSION,
        "skillProfile": {
            **skill_context["metadata"],
            "allowedEvidence": skill_context["allowedEvidence"],
            "prohibitedCapabilities": skill_context["prohibitedCapabilities"],
        },
        "skillRules": skill_context["rules"],
        "constraints": [
            "只基于输入的 macro_evidence 和 market_evidence，不要补充、猜测或编造最新宏观事实。",
            "这是给用户自己阅读的行情参考报告，不是自动交易信号，不是个性化投资顾问服务。",
            "不得编造买卖价、个人化仓位或保证收益；可以解释服务端 pricePlan 的入场参考价、止损触发价和止盈参考价，但不能称其为实际成交价。",
            "不得提交订单、不得建议绕过风控、不得声称已经执行交易。",
            "如果宏观证据不完整，明确说明不确定性，并降低 confidence。",
            "主结论只解读 market_evidence 中所标识的当前图表周期与快照，不得把其他周期历史数据包装成未来价格预测。",
            "market_evidence.pricePlan 是服务端计算的15分钟价格计划；可以解释其条件与风险，不得修改其中的价格、方向、状态或有效期。",
            "market_evidence.evaluationSamples 仅是同合约同版本历史方向与价格路径核验；旧突破价和新版报价入场口径应区分。只有达到最小样本数时才可引用方向符合率；不得称为模型训练、成交结果、实际收益率或未来保证。",
            "可选的 horizons 仅可依据同一份 market_evidence 做短周期条件推演：说明方向观察、置信度、可核对的图表条件或重读线索；不得给出目标价、保证式涨跌或下单建议。证据不足时省略该周期。",
            "输出 JSON 对象，不要 Markdown。",
        ],
        "expected_json_schema": {
            "stance": "bullish|bearish|neutral|wait",
            "confidence": "0-100 integer",
            "summary": "一句短结论",
            "overall": {"view": "偏多参考|偏空参考|震荡观察|暂时观望|波动加大", "confidence": "0-100 integer", "summary": "报告总览"},
            "horizons": [{"key": "15m|1h|today", "bias": "条件方向观察", "confidence": "0-100 integer", "summary": "基于当前图表快照的短周期推演", "watch": ["图表确认或重读线索"], "risk": "不确定性或重读风险"}],
            "report": {
                "keyFactors": ["不超过三项、可回到当前图表核对的证据"],
                "focus": ["用户可继续观察的当前图表变化"],
                "reassess": ["当前图表出现何种变化后需要重新阅读"],
                "riskNotes": ["仅供参考的风险提示"],
            },
            "macro": {"bias": "宏观偏向", "drivers": ["宏观依据"], "uncertainty": "宏观不确定性"},
            "technical": {"trend": "K线结构", "keyLevels": ["关键价位"], "volumeRead": "量能判断", "notes": ["技术备注"]},
            "suggestion": {
                "action": "observe|wait_release|consider_long|consider_short|avoid",
                "condition": "用户可关注的变化，不是下单条件",
                "invalidation": "需要重新阅读报告的变化",
                "riskNotes": ["风险提示"],
            },
            "warnings": ["额外限制"],
        },
        "macro_evidence": macro,
        "market_evidence": market,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def run_market_ai_outlook(market: dict[str, Any], macro: dict[str, Any], skill_context: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        skill_context = skill_context or compile_okx_market_reading_context()
        analysis_profile = skill_context["metadata"]
    except ValueError:
        return fallback_market_ai_outlook(
            market,
            macro,
            "行情读取规则无效，已使用指标降级分析。",
            unavailable_okx_market_reading_metadata(),
        )
    config = stored_llm_config()
    if not config.get("enabled"):
        return fallback_market_ai_outlook(market, macro, "LLM 未启用，已使用指标降级分析。", analysis_profile)
    config = {**config, "maxTokens": max(coerce_int(config.get("maxTokens"), 800, 128, 4000), 1600)}
    try:
        completion = llm_chat_completion(
            config,
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个谨慎的宏观与永续合约行情分析助手。"
                        "你只能基于用户提供的结构化证据输出 JSON，不能编造实时宏观事实，不能下单。"
                    ),
                },
                {"role": "user", "content": market_ai_outlook_prompt(market, macro, skill_context)},
            ],
            request_type="market_ai_outlook",
            context={
                "inst_id": (market.get("instrument") or {}).get("instId") if isinstance(market.get("instrument"), dict) else None,
                "bar": (market.get("technical") or {}).get("bar") if isinstance(market.get("technical"), dict) else None,
                "analysis_profile": analysis_profile,
            },
        )
        raw_text = str(completion["content"])
        return normalize_market_ai_outlook(extract_json_object(raw_text), market, macro, config, completion, analysis_profile)
    except Exception as exc:
        usage_log = llm_usage_log_view(exc.usage_log) if isinstance(exc, LlmCompletionError) else None
        result = fallback_market_ai_outlook(market, macro, "LLM 分析失败，已使用指标降级分析。", analysis_profile)
        if usage_log:
            result["usage"] = usage_log
            result["usage_log_id"] = usage_log.get("id")
        return result


def market_ai_verified_sample_context(inst_id: str) -> dict[str, Any]:
    if not hasattr(database, "ai_outlook_sample_counts"):
        return prompt_sample_context(sample_summary([]), [])
    counts = database.ai_outlook_sample_counts(inst_id, MARKET_AI_OUTLOOK_PROMPT_VERSION)
    recent = database.list_ai_outlook_samples(inst_id, MARKET_AI_OUTLOOK_PROMPT_VERSION, 12, verified_only=True)
    return prompt_sample_context(sample_summary(counts), recent)


def record_market_ai_outlook_samples(
    result: dict[str, Any], market: dict[str, Any], chart_snapshot: dict[str, Any],
    plan_candles: list[dict[str, Any]],
) -> None:
    if not hasattr(database, "insert_ai_outlook_sample"):
        return
    samples = samples_for_report(
        result, market, chart_snapshot.get("candles") or [], plan_candles,
        CANDLE_BAR_MILLISECONDS, int(result.get("generatedAt") or now_ms()),
    )
    inserted = 0
    for sample in samples:
        inserted += int(database.insert_ai_outlook_sample(sample))
    result["verificationSampleCount"] = inserted


def reconcile_due_market_ai_samples(current_ms: int | None = None, limit: int = 100) -> int:
    current_ms = now_ms() if current_ms is None else current_ms
    due = database.due_ai_outlook_samples(current_ms, limit)
    snapshots: dict[tuple[str, str], tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    minute_snapshots: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    settled = 0
    for sample in due:
        inst_id, bar = str(sample["inst_id"]), str(sample["bar"])
        key = (inst_id, bar)
        if key not in snapshots:
            snapshots[key] = candle_snapshot_for_inst(inst_id, bar, 300)
        candles, meta = snapshots[key]
        target = next((row for row in candles if int(row.get("ts") or 0) == int(sample["target_ts"])), None)
        minute_candles = None
        minute_source = ""
        if sample.get("kind") == "price_plan_15m" and target is not None:
            if inst_id not in minute_snapshots:
                minute_snapshots[inst_id] = candle_snapshot_for_inst(inst_id, "1m", 300)
            minute_candles, minute_meta = minute_snapshots[inst_id]
            minute_source = str(minute_meta.get("source") or "")
        outcome = grade_sample(
            sample, target, str(meta.get("source") or ""), current_ms, CANDLE_BAR_MILLISECONDS[bar],
            minute_candles, minute_source,
        )
        if outcome and database.settle_ai_outlook_sample(str(sample["sample_id"]), outcome):
            settled += 1
    return settled


def market_ai_sample_verification_loop() -> None:
    while True:
        try:
            reconcile_due_market_ai_samples()
        except Exception:
            logger.exception("AI outlook sample verification failed; will retry")
        time.sleep(60)


def market_ai_sample_history(inst_id: str, limit: int = 20) -> dict[str, Any]:
    rows = database.list_ai_outlook_samples(inst_id, MARKET_AI_OUTLOOK_PROMPT_VERSION, limit)
    counts = database.ai_outlook_sample_counts(inst_id, MARKET_AI_OUTLOOK_PROMPT_VERSION)
    return {
        "instId": inst_id,
        "promptVersion": MARKET_AI_OUTLOOK_PROMPT_VERSION,
        "criterionVersion": 1,
        "summary": sample_summary(counts),
        "samples": [public_sample(row) for row in rows],
        "generatedAt": now_ms(),
        "readOnly": True,
        "scope": "行情方向只比较两根完整 K 线的收盘价；新价格计划用报告之后的完整 1 分钟 K 线核对入场价、止盈价与可辨认的先后顺序。报告生成所在分钟不计入；到价不代表实际成交或交易收益。",
    }


def cached_market_ai_outlook(request: MarketAiOutlookRequest) -> dict[str, Any]:
    inst_id = normalize_market_ai_inst_id(request.instId)
    bar = normalize_market_ai_bar(request.bar)
    limit = coerce_int(request.limit, MARKET_AI_CANDLE_LIMIT, 30, 300)
    chart_snapshot, snapshot_error = chart_snapshot_for_request(str(request.snapshotId or ""), inst_id, bar)
    if not chart_snapshot:
        return {
            "status": "snapshot_required",
            "source": "chart-snapshot",
            "readOnly": True,
            "snapshotRequired": True,
            "detail": snapshot_error,
        }
    try:
        skill_context = compile_okx_market_reading_context()
        analysis_profile = skill_context["metadata"]
    except ValueError:
        macro = build_market_ai_macro_snapshot(force=request.forceMacro)
        market = build_market_ai_market_evidence(inst_id, bar, limit, chart_snapshot)
        market["tradingStructure"] = market_ai_trading_structure_evidence(inst_id, bar)
        plan_candles = market_ai_plan_candles(inst_id, bar, chart_snapshot)
        market["multiTimeframeTrend"] = build_market_ai_fixed_trends(inst_id, bar, chart_snapshot, plan_candles)
        market["pricePlanStructure"] = market["tradingStructure"] if bar == "15m" else market_ai_trading_structure_evidence(inst_id, "15m")
        market["pricePlan"] = build_market_ai_price_plan(market, *plan_candles)
        market["evaluationSamples"] = market_ai_verified_sample_context(inst_id)
        result = fallback_market_ai_outlook(
            market,
            macro,
            "行情读取规则无效，已使用指标降级分析。",
            unavailable_okx_market_reading_metadata(),
        )
        result.update({"cached": False, "cacheAgeMs": 0, "marketEvidence": market, "macroEvidence": macro, "chartSnapshot": market.get("chartSnapshot"), "readOnly": True})
        record_market_ai_outlook_samples(result, market, chart_snapshot, plan_candles[0])
        return result
    macro = build_market_ai_macro_snapshot(force=request.forceMacro)
    market = build_market_ai_market_evidence(inst_id, bar, limit, chart_snapshot)
    market["tradingStructure"] = market_ai_trading_structure_evidence(inst_id, bar)
    plan_candles = market_ai_plan_candles(inst_id, bar, chart_snapshot)
    market["multiTimeframeTrend"] = build_market_ai_fixed_trends(inst_id, bar, chart_snapshot, plan_candles)
    market["pricePlanStructure"] = market["tradingStructure"] if bar == "15m" else market_ai_trading_structure_evidence(inst_id, "15m")
    market["pricePlan"] = build_market_ai_price_plan(market, *plan_candles)
    market["evaluationSamples"] = market_ai_verified_sample_context(inst_id)
    cache_key = market_ai_outlook_cache_key(market, macro, analysis_profile)
    now = now_ms()
    with market_ai_outlook_cache_lock:
        cached = market_ai_outlook_cache.get(cache_key)
        if cached and not request.forceAnalysis:
            ts = int(cached.get("ts") or 0)
            if ts and now - ts <= MARKET_AI_OUTLOOK_CACHE_SECONDS * 1000:
                result = deepcopy(cached.get("payload") or {})
                result["cached"] = True
                result["cacheAgeMs"] = now - ts
                result["marketEvidence"] = market
                result["macroEvidence"] = macro
                result["chartSnapshot"] = market.get("chartSnapshot")
                result["multiTimeframeTrend"] = market.get("multiTimeframeTrend") or {}
                result["pricePlan"] = market.get("pricePlan") or {}
                return result
    result = run_market_ai_outlook(market, macro)
    result["analysisProfile"] = analysis_profile
    result["cached"] = False
    result["cacheAgeMs"] = 0
    result["marketEvidence"] = market
    result["macroEvidence"] = macro
    result["chartSnapshot"] = market.get("chartSnapshot")
    result["multiTimeframeTrend"] = market.get("multiTimeframeTrend") or {}
    result["pricePlan"] = market.get("pricePlan") or {}
    result["readOnly"] = True
    record_market_ai_outlook_samples(result, market, chart_snapshot, plan_candles[0])
    with market_ai_outlook_cache_lock:
        market_ai_outlook_cache[cache_key] = {"payload": deepcopy(result), "ts": now_ms()}
    return result


def normalize_earn_upper(value: str, field_name: str, max_length: int = 40) -> str:
    normalized = value.strip().upper()
    if not normalized:
        return ""
    if len(normalized) > max_length or not normalized.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail=f"{field_name}格式不受支持。")
    return normalized


def normalize_earn_token(value: str, field_name: str, max_length: int = 80) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    if len(normalized) > max_length or not normalized.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail=f"{field_name}格式不受支持。")
    return normalized


def normalize_earn_protocol_type(protocol_type: str) -> str:
    normalized = protocol_type.strip().lower()
    if normalized not in EARN_PROTOCOL_TYPES:
        raise HTTPException(status_code=400, detail="链上赚币 protocolType 仅支持 staking 或 defi。")
    return normalized


def normalize_earn_active_state(state: str) -> str:
    normalized = state.strip()
    if normalized not in EARN_ACTIVE_ORDER_STATES:
        raise HTTPException(status_code=400, detail="链上赚币活跃订单状态不受支持。")
    return normalized


def normalize_earn_staking_history_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in EARN_STAKING_HISTORY_TYPES:
        raise HTTPException(status_code=400, detail="质押记录类型仅支持 purchase 或 redeem。")
    return normalized


def normalize_earn_staking_history_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in EARN_STAKING_HISTORY_STATUSES:
        raise HTTPException(status_code=400, detail="质押记录状态不受支持。")
    return normalized


def normalize_earn_days(days: int) -> int:
    return coerce_int(days, EARN_APY_DEFAULT_DAYS, 1, 365)


def earn_active_state_label(state: str) -> str:
    labels = {
        "8": "待上车",
        "13": "取消中",
        "9": "上链中",
        "1": "收益中",
        "2": "赎回中",
    }
    return labels.get(str(state or ""), str(state or "--"))


def earn_history_state_label(state: str) -> str:
    if str(state or "") == "3":
        return "已完成"
    return str(state or "--")


def earn_product_state_label(state: str) -> str:
    labels = {
        "purchasable": "可申购",
        "sold_out": "售罄",
        "stop": "暂停申购",
    }
    return labels.get(str(state or ""), str(state or "--"))


def earn_staking_status_label(status: str) -> str:
    labels = {
        "pending": "处理中",
        "success": "成功",
        "failed": "失败",
        "cancelled": "已取消",
    }
    return labels.get(str(status or ""), str(status or "--"))


def normalize_earn_data_items(items: Any, amount_keys: list[str]) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        row: dict[str, Any] = {"ccy": str(item.get("ccy") or "").upper(), "raw": item}
        for key in amount_keys:
            row[key] = str(item.get(key) or "")
        if item.get("earningType") is not None:
            row["earningType"] = str(item.get("earningType") or "")
            row["earningTypeLabel"] = "实际到账收益" if row["earningType"] == "1" else "预估收益"
        normalized.append(row)
    return normalized


def normalize_earn_product(row: dict[str, Any]) -> dict[str, Any]:
    state = str(row.get("state") or "")
    return {
        "productId": str(row.get("productId") or ""),
        "ccy": str(row.get("ccy") or "").upper(),
        "protocol": str(row.get("protocol") or ""),
        "protocolType": str(row.get("protocolType") or ""),
        "term": str(row.get("term") or ""),
        "apy": str(row.get("apy") or ""),
        "earlyRedeem": bool(row.get("earlyRedeem")),
        "state": state,
        "stateLabel": earn_product_state_label(state),
        "investData": normalize_earn_data_items(row.get("investData"), ["bal", "minAmt", "maxAmt", "amt"]),
        "earningData": normalize_earn_data_items(row.get("earningData"), ["earnings", "realizedEarnings"]),
        "redeemPeriod": row.get("redeemPeriod") if isinstance(row.get("redeemPeriod"), list) else [],
        "fastRedemptionDailyLimit": str(row.get("fastRedemptionDailyLimit") or ""),
        "raw": row,
    }


def normalize_earn_order(row: dict[str, Any], historical: bool = False) -> dict[str, Any]:
    state = str(row.get("state") or "")
    return {
        "ordId": str(row.get("ordId") or ""),
        "ccy": str(row.get("ccy") or "").upper(),
        "productId": str(row.get("productId") or ""),
        "state": state,
        "stateLabel": earn_history_state_label(state) if historical else earn_active_state_label(state),
        "protocol": str(row.get("protocol") or ""),
        "protocolType": str(row.get("protocolType") or ""),
        "term": str(row.get("term") or ""),
        "apy": str(row.get("apy") or ""),
        "investData": normalize_earn_data_items(row.get("investData"), ["amt", "bal", "minAmt", "maxAmt"]),
        "earningData": normalize_earn_data_items(row.get("earningData"), ["earnings", "realizedEarnings"]),
        "fastRedemptionData": normalize_earn_data_items(row.get("fastRedemptionData"), ["redeemingAmt"]),
        "purchasedTime": str(row.get("purchasedTime") or ""),
        "redeemedTime": str(row.get("redeemedTime") or ""),
        "estSettlementTime": str(row.get("estSettlementTime") or ""),
        "cancelRedemptionDeadline": str(row.get("cancelRedemptionDeadline") or ""),
        "tag": str(row.get("tag") or ""),
        "raw": row,
    }


def normalize_earn_staking_product_info(row: dict[str, Any], asset: str) -> dict[str, Any]:
    return {
        "asset": asset,
        "receiptCcy": "BETH" if asset == "ETH" else "OKSOL",
        "rate": str(row.get("rate") or ""),
        "redemptDays": str(row.get("redemptDays") or ""),
        "minAmt": str(row.get("minAmt") or ""),
        "fastRedemptionDailyLimit": str(row.get("fastRedemptionDailyLimit") or ""),
        "fastRedemptionAvail": str(row.get("fastRedemptionAvail") or ""),
        "raw": row,
    }


def normalize_earn_staking_balance(rows: list[dict[str, Any]], asset: str) -> list[dict[str, Any]]:
    receipt_ccy = "BETH" if asset == "ETH" else "OKSOL"
    normalized = []
    for row in rows:
        normalized.append(
            {
                "asset": asset,
                "ccy": str(row.get("ccy") or receipt_ccy),
                "amt": str(row.get("amt") or ""),
                "latestInterestAccrual": str(row.get("latestInterestAccrual") or ""),
                "totalInterestAccrual": str(row.get("totalInterestAccrual") or ""),
                "ts": str(row.get("ts") or ""),
                "raw": row,
            }
        )
    return normalized


def normalize_earn_staking_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        status = str(row.get("status") or "")
        normalized.append(
            {
                "type": str(row.get("type") or ""),
                "amt": str(row.get("amt") or ""),
                "redeemingAmt": str(row.get("redeemingAmt") or ""),
                "status": status,
                "statusLabel": earn_staking_status_label(status),
                "ordId": str(row.get("ordId") or ""),
                "requestTime": str(row.get("requestTime") or ""),
                "completedTime": str(row.get("completedTime") or ""),
                "estCompletedTime": str(row.get("estCompletedTime") or ""),
                "raw": row,
            }
        )
    return normalized


def normalize_earn_apy_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points = []
    for row in rows:
        ts = coerce_int(row.get("ts"), 0, 0, 9_999_999_999_999)
        if not ts:
            continue
        points.append({"ts": ts, "rate": str(row.get("rate") or ""), "raw": row})
    return sorted(points, key=lambda item: item["ts"])


def earn_request_key(source: str, environment: str, params: dict[str, Any]) -> str:
    return json.dumps(
        {"source": source, "environment": environment, "params": params, "schemaVersion": 1},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def earn_with_cache_meta(payload: dict[str, Any], source: str, ts: int, warning: str = "") -> dict[str, Any]:
    result = dict(payload)
    result["source"] = source
    result["ts"] = ts
    result["cacheAgeMs"] = max(0, now_ms() - ts)
    warnings = [str(item) for item in result.get("warnings") or [] if str(item)]
    if warning:
        warnings.insert(0, warning)
    result["warnings"] = list(dict.fromkeys(warnings))
    return result


def cached_earn_payload(
    cache_key: str,
    live_source: str,
    cache_source: str,
    stale_source: str,
    unavailable_source: str,
    empty_payload: dict[str, Any],
    loader: Any,
    ttl_seconds: int,
    force: bool = False,
) -> dict[str, Any]:
    now = now_ms()
    with earn_cache_lock:
        cached = earn_cache.get(cache_key)
        if not force and cached:
            cached_ts = int(cached.get("ts") or 0)
            if cached_ts and now - cached_ts <= ttl_seconds * 1000:
                return earn_with_cache_meta(deepcopy(cached.get("payload") or empty_payload), cache_source, cached_ts)
    try:
        payload = loader()
        ts = now_ms()
        with earn_cache_lock:
            earn_cache[cache_key] = {"payload": deepcopy(payload), "ts": ts}
        source = f"{live_source}-partial" if payload.get("warnings") else live_source
        return earn_with_cache_meta(payload, source, ts)
    except (OkxError, ValueError) as exc:
        with earn_cache_lock:
            cached = earn_cache.get(cache_key)
            if cached:
                cached_ts = int(cached.get("ts") or 0)
                if cached_ts:
                    return earn_with_cache_meta(
                        deepcopy(cached.get("payload") or empty_payload),
                        stale_source,
                        cached_ts,
                        f"链上赚币刷新失败，显示缓存：{str(exc)}",
                    )
        return earn_with_cache_meta(
            {**empty_payload, "warnings": [f"链上赚币数据不可用：{str(exc)}"]},
            unavailable_source,
            now_ms(),
        )


def earn_unconfigured_response(section: str, environment: str) -> dict[str, Any]:
    return {
        "configured": False,
        "environment": environment,
        "section": section,
        "data": [],
        "message": f"{environment_label(environment)} API Key 未配置，无法读取该链上赚币数据。",
        "source": "not-configured",
        "ts": now_ms(),
        "cacheAgeMs": 0,
        "warnings": [],
    }


def current_earn_environment() -> str:
    return "live"


def earn_client_for_environment(environment: str) -> OkxClient:
    return client_for_environment(environment)


def build_earn_offers(product_id: str, protocol_type: str, ccy: str, force: bool = False) -> dict[str, Any]:
    environment = current_earn_environment()
    if not settings.has_credentials_for_environment(environment):
        return earn_unconfigured_response("offers", environment)
    params = {"productId": product_id, "protocolType": protocol_type, "ccy": ccy}
    cache_key = earn_request_key("offers", environment, params)

    def load() -> dict[str, Any]:
        rows = earn_client_for_environment(environment).get_staking_defi_offers(product_id, protocol_type, ccy)
        return {"configured": True, "environment": environment, "data": [normalize_earn_product(row) for row in rows], "warnings": []}

    return cached_earn_payload(
        cache_key,
        "okx-earn-offers",
        "earn-offers-cache",
        "earn-offers-stale-cache",
        "earn-offers-unavailable",
        {"configured": True, "environment": environment, "data": [], "warnings": []},
        load,
        EARN_CACHE_SECONDS,
        force=force,
    )


def build_earn_active_orders(product_id: str, protocol_type: str, ccy: str, state: str, force: bool = False) -> dict[str, Any]:
    environment = current_earn_environment()
    if not settings.has_credentials_for_environment(environment):
        return earn_unconfigured_response("active-orders", environment)
    params = {"productId": product_id, "protocolType": protocol_type, "ccy": ccy, "state": state}
    cache_key = earn_request_key("active-orders", environment, params)

    def load() -> dict[str, Any]:
        rows = earn_client_for_environment(environment).get_staking_defi_active_orders(product_id, protocol_type, ccy, state)
        return {"configured": True, "environment": environment, "data": [normalize_earn_order(row) for row in rows], "warnings": []}

    return cached_earn_payload(
        cache_key,
        "okx-earn-active-orders",
        "earn-active-orders-cache",
        "earn-active-orders-stale-cache",
        "earn-active-orders-unavailable",
        {"configured": True, "environment": environment, "data": [], "warnings": []},
        load,
        EARN_CACHE_SECONDS,
        force=force,
    )


def build_earn_order_history(
    product_id: str,
    protocol_type: str,
    ccy: str,
    after: str,
    before: str,
    limit: int,
    force: bool = False,
) -> dict[str, Any]:
    environment = current_earn_environment()
    if not settings.has_credentials_for_environment(environment):
        return earn_unconfigured_response("history", environment)
    params = {"productId": product_id, "protocolType": protocol_type, "ccy": ccy, "after": after, "before": before, "limit": limit}
    cache_key = earn_request_key("history", environment, params)

    def load() -> dict[str, Any]:
        rows = earn_client_for_environment(environment).get_staking_defi_order_history(product_id, protocol_type, ccy, after, before, limit)
        data = [normalize_earn_order(row, historical=True) for row in rows]
        return {
            "configured": True,
            "environment": environment,
            "data": data,
            "paging": {"limit": limit, "hasMore": len(data) == limit, "after": after, "before": before},
            "warnings": [],
        }

    return cached_earn_payload(
        cache_key,
        "okx-earn-history",
        "earn-history-cache",
        "earn-history-stale-cache",
        "earn-history-unavailable",
        {"configured": True, "environment": environment, "data": [], "paging": {"limit": limit, "hasMore": False}, "warnings": []},
        load,
        EARN_CACHE_SECONDS,
        force=force,
    )


def build_earn_staking_overview(
    asset: str,
    request_type: str,
    status: str,
    after: str,
    before: str,
    limit: int,
    days: int,
    force: bool = False,
) -> dict[str, Any]:
    asset = asset.upper()
    environment = current_earn_environment()
    params = {"type": request_type, "status": status, "after": after, "before": before, "limit": limit, "days": days}
    cache_key = earn_request_key(f"{asset.lower()}-staking", environment, params)

    def load() -> dict[str, Any]:
        staking_client = earn_client_for_environment(environment)
        configured = settings.has_credentials_for_environment(environment)
        warnings: list[str] = []
        product_info: dict[str, Any] = {}
        balances: list[dict[str, Any]] = []
        history: list[dict[str, Any]] = []
        apy_points: list[dict[str, Any]] = []

        try:
            raw_apy = staking_client.get_eth_staking_apy_history(days) if asset == "ETH" else staking_client.get_sol_staking_apy_history(days)
            apy_points = normalize_earn_apy_history(raw_apy)
        except OkxError as exc:
            warnings.append(f"{asset} 质押历史年化不可用：{str(exc)}")

        if configured:
            try:
                raw_product = staking_client.get_eth_staking_product_info() if asset == "ETH" else staking_client.get_sol_staking_product_info()
                product_info = normalize_earn_staking_product_info(raw_product, asset)
            except OkxError as exc:
                warnings.append(f"{asset} 质押产品信息不可用：{str(exc)}")
            try:
                raw_balance = staking_client.get_eth_staking_balance() if asset == "ETH" else staking_client.get_sol_staking_balance()
                balances = normalize_earn_staking_balance(raw_balance, asset)
            except OkxError as exc:
                warnings.append(f"{asset} 质押余额不可用：{str(exc)}")
            try:
                raw_history = (
                    staking_client.get_eth_staking_history(request_type, status, after, before, limit)
                    if asset == "ETH"
                    else staking_client.get_sol_staking_history(request_type, status, after, before, limit)
                )
                history = normalize_earn_staking_history(raw_history)
            except OkxError as exc:
                warnings.append(f"{asset} 质押申购赎回记录不可用：{str(exc)}")
        else:
            warnings.append(f"{environment_label(environment)} API Key 未配置，产品信息、余额和申购赎回记录不可用。")

        return {
            "configured": configured,
            "environment": environment,
            "asset": asset,
            "receiptCcy": "BETH" if asset == "ETH" else "OKSOL",
            "productInfo": product_info,
            "balances": balances,
            "history": history,
            "apyPoints": apy_points,
            "paging": {"limit": limit, "hasMore": len(history) == limit, "after": after, "before": before},
            "days": days,
            "warnings": warnings,
        }

    return cached_earn_payload(
        cache_key,
        f"okx-earn-{asset.lower()}",
        f"earn-{asset.lower()}-cache",
        f"earn-{asset.lower()}-stale-cache",
        f"earn-{asset.lower()}-unavailable",
        {
            "configured": settings.has_credentials_for_environment(environment),
            "environment": environment,
            "asset": asset,
            "receiptCcy": "BETH" if asset == "ETH" else "OKSOL",
            "productInfo": {},
            "balances": [],
            "history": [],
            "apyPoints": [],
            "paging": {"limit": limit, "hasMore": False},
            "days": days,
            "warnings": [],
        },
        load,
        EARN_STAKING_CACHE_SECONDS if settings.has_credentials_for_environment(environment) else EARN_APY_CACHE_SECONDS,
        force=force,
    )


def radar_market_analysis_key(request: RadarScanRequest, radar_payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "radarRequest": radar_request_key(request),
            "sortBy": request.sortBy,
            "scanTs": coerce_int(radar_payload.get("ts"), 0, 0, 9_999_999_999_999),
            "returned": coerce_int((radar_payload.get("summary") or {}).get("returned"), 0, 0, 10_000),
            "leaders": [str(item.get("instId") or "") for item in (radar_payload.get("data") or [])[:RADAR_MARKET_LEADER_LIMIT]],
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def save_radar_analysis_snapshot(cache_key: str, payload: dict[str, Any], ts: int) -> None:
    snapshot = {"cacheKey": cache_key, "ts": ts, "payload": payload}
    database.set_app_setting(RADAR_ANALYSIS_CACHE_KEY, json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), ts)
    with radar_analysis_cache_lock:
        radar_analysis_cache["cacheKey"] = cache_key
        radar_analysis_cache["payload"] = payload
        radar_analysis_cache["ts"] = ts


def load_radar_analysis_snapshot(cache_key: str) -> dict[str, Any] | None:
    with radar_analysis_cache_lock:
        cached_payload = radar_analysis_cache.get("payload")
        cached_ts = int(radar_analysis_cache.get("ts") or 0)
        cached_key = str(radar_analysis_cache.get("cacheKey") or "")
        if cached_payload and cached_ts and cached_key == cache_key:
            return {"cacheKey": cached_key, "ts": cached_ts, "payload": cached_payload}

    raw = database.get_app_setting(RADAR_ANALYSIS_CACHE_KEY)
    if not raw:
        return None
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(snapshot, dict) or str(snapshot.get("cacheKey") or "") != cache_key:
        return None
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        return None
    ts = coerce_int(snapshot.get("ts"), 0, 0, 9_999_999_999_999)
    with radar_analysis_cache_lock:
        radar_analysis_cache["cacheKey"] = cache_key
        radar_analysis_cache["payload"] = payload
        radar_analysis_cache["ts"] = ts
    return {"cacheKey": cache_key, "ts": ts, "payload": payload}


def radar_analysis_payload_with_cache_meta(payload: dict[str, Any], source: str, ts: int) -> dict[str, Any]:
    result = dict(payload)
    result["source"] = source
    result["cacheAgeMs"] = max(0, now_ms() - ts)
    return result


def radar_summary_inst_ids(market_summary: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("leaders", "topTurnover", "topVolatility", "volumeSpikes"):
        for item in market_summary.get(key) or []:
            if isinstance(item, dict) and item.get("instId"):
                ids.add(str(item["instId"]).upper())
    return ids


def radar_clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text[:500] if text else fallback


def radar_string_list(value: Any, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [radar_clean_text(item) for item in value if radar_clean_text(item)][:limit]


def fallback_radar_market_analysis(market_summary: dict[str, Any], warning: str = "") -> dict[str, Any]:
    breadth = market_summary.get("breadth") if isinstance(market_summary.get("breadth"), dict) else {}
    liquidity = market_summary.get("liquidity") if isinstance(market_summary.get("liquidity"), dict) else {}
    volatility = market_summary.get("volatility") if isinstance(market_summary.get("volatility"), dict) else {}
    risk = market_summary.get("risk") if isinstance(market_summary.get("risk"), dict) else {}
    scan = market_summary.get("scan") if isinstance(market_summary.get("scan"), dict) else {}
    rising = coerce_int(breadth.get("rising"), 0, 0, 10_000)
    falling = coerce_int(breadth.get("falling"), 0, 0, 10_000)
    high_risk = coerce_int(risk.get("high"), 0, 0, 10_000)
    analyzed = max(1, coerce_int(scan.get("analyzed"), 0, 0, 10_000))
    high_volatility = coerce_int(volatility.get("high"), 0, 0, 10_000)

    if high_risk / analyzed >= 0.35:
        regime = "risk-off"
        regime_text = "高风险合约占比较高，优先降低频率并缩小筛选范围。"
    elif rising > falling * 1.4 or falling > rising * 1.4:
        regime = "trend"
        regime_text = "涨跌方向出现明显倾斜，适合先看成交额靠前且风险较低的合约。"
    elif high_volatility / analyzed >= 0.35:
        regime = "mixed"
        regime_text = "波动扩散较明显，但需要用流动性和风险标签过滤噪音。"
    else:
        regime = "range"
        regime_text = "大盘活跃度偏均衡，适合等待放量或振幅扩大的合约。"

    leaders = [item for item in market_summary.get("leaders") or [] if isinstance(item, dict)]
    watchlist = [
        {
            "instId": str(item.get("instId") or ""),
            "reason": str((item.get("entryAssessment") or {}).get("summary") or f"机会分 {item.get('score', 0)}，{item.get('volatilityLevel') or 'unknown'} 波动，{item.get('tradabilityStatus') or 'unknown'}。"),
            "riskNote": "仍需检查盘口深度、止损空间和是否出现异常单边波动。",
        }
        for item in leaders[:3]
        if item.get("instId")
    ]
    warnings = [warning] if warning else []
    if not warning:
        warnings.append("LLM 未参与，本分析由雷达指标自动生成。")
    return {
        "marketRegime": regime,
        "confidence": 58 if leaders else 35,
        "summary": regime_text,
        "highlights": [
            f"上涨 {rising} 个，下跌 {falling} 个，24h 涨跌中位数 {decimal_display_fixed(breadth.get('medianChange24hPct'), 2)}%。",
            f"可玩 {liquidity.get('playable', 0)} 个，低流动性 {liquidity.get('lowLiquidity', 0)} 个，统一成交额样本 {liquidity.get('comparableCount', 0)} 个。",
            f"高波动 {high_volatility} 个，高风险 {high_risk} 个，异常振幅 {risk.get('abnormalMoves', 0)} 个。",
        ],
        "watchlist": watchlist,
        "riskWarnings": [
            "不要只按振幅选择合约，成交量不足、浮动过大和高风险标签需要优先排除。",
            "该分析不构成交易指令，开仓前仍需确认盘口、杠杆和止损。",
        ],
        "suggestedFilters": ["优先查看可玩 + 低风险", "成交额使用 USDT 口径", "选择中高浮动但不过热的结果"],
        "generatedAt": now_ms(),
        "source": "metric-fallback",
        "warnings": warnings,
        "scanTs": coerce_int(scan.get("ts"), 0, 0, 9_999_999_999_999),
        "cacheAgeMs": 0,
        "marketSummary": market_summary,
    }


def parse_radar_market_llm_analysis(parsed: dict[str, Any], market_summary: dict[str, Any]) -> dict[str, Any]:
    allowed_regimes = {"trend", "range", "mixed", "risk-off"}
    regime = radar_clean_text(parsed.get("marketRegime") or parsed.get("regime"), "mixed").lower()
    if regime not in allowed_regimes:
        regime = "mixed"
    allowed_ids = radar_summary_inst_ids(market_summary)
    watchlist: list[dict[str, str]] = []
    raw_watchlist = parsed.get("watchlist")
    if isinstance(raw_watchlist, list):
        for item in raw_watchlist:
            if not isinstance(item, dict):
                continue
            inst_id = radar_clean_text(item.get("instId") or item.get("inst_id")).upper()
            if not inst_id or inst_id not in allowed_ids:
                continue
            watchlist.append(
                {
                    "instId": inst_id,
                    "reason": radar_clean_text(item.get("reason"), "指标处于候选池前列，值得进一步查看。"),
                    "riskNote": radar_clean_text(item.get("riskNote") or item.get("risk"), "需要复核流动性、盘口和止损空间。"),
                }
            )
            if len(watchlist) >= 5:
                break
    if not watchlist:
        watchlist = fallback_radar_market_analysis(market_summary)["watchlist"]

    scan = market_summary.get("scan") if isinstance(market_summary.get("scan"), dict) else {}
    return {
        "marketRegime": regime,
        "confidence": coerce_int(parsed.get("confidence"), 60, 0, 100),
        "summary": radar_clean_text(parsed.get("summary"), "AI 已基于雷达摘要完成大盘分析。"),
        "highlights": radar_string_list(parsed.get("highlights"), 6),
        "watchlist": watchlist,
        "riskWarnings": radar_string_list(parsed.get("riskWarnings") or parsed.get("risks"), 6),
        "suggestedFilters": radar_string_list(parsed.get("suggestedFilters"), 5),
        "generatedAt": now_ms(),
        "source": "llm-market-analysis",
        "warnings": radar_string_list(parsed.get("warnings"), 4),
        "scanTs": coerce_int(scan.get("ts"), 0, 0, 9_999_999_999_999),
        "cacheAgeMs": 0,
        "marketSummary": market_summary,
    }


def run_radar_market_llm_analysis(market_summary: dict[str, Any]) -> dict[str, Any]:
    config = stored_llm_config()
    if not config.get("enabled") or not config.get("baseUrl") or not config.get("model") or not config.get("apiKey"):
        return fallback_radar_market_analysis(market_summary, "AI 大盘分析不可用：LLM 配置未启用或不完整。")

    try:
        completion = llm_chat_completion(
            config,
            [
                {
                    "role": "system",
                    "content": (
                        "你是谨慎的永续合约大盘雷达分析助手。只基于输入 JSON 摘要分析市场状态。"
                        "重点根据合约成交量、24h 振幅、近期 K 线浮动和量能脉冲判断是否适合入手观察。"
                        "不得输出做多、做空、保证盈利、必须交易、已经下单等措辞。"
                        "不得修改排名或分数。只返回紧凑 JSON 对象，不要 Markdown，不要代码块，不要解释 JSON 之外的文字。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "instruction": (
                                "根据 marketSummary 输出：marketRegime(trend/range/mixed/risk-off)、confidence(0-100)、"
                                "summary、highlights、watchlist[{instId,reason,riskNote}]、riskWarnings、suggestedFilters、warnings。"
                                "watchlist 只能使用 marketSummary 中出现的 instId。reason 必须解释成交量与浮动是否支持入手观察。"
                                "所有字符串保持短句，summary 不超过 60 字，数组最多 3 项。严格使用双引号 JSON，禁止尾随逗号。"
                            ),
                            "outputExample": {
                                "marketRegime": "mixed",
                                "confidence": 65,
                                "summary": "成交量集中但浮动分化，优先观察可玩且不过热的合约。",
                                "highlights": ["可玩合约占比偏高", "部分合约浮动过大"],
                                "watchlist": [{"instId": "BTC-USDT-SWAP", "reason": "成交量充足且浮动适中", "riskNote": "确认盘口和止损空间"}],
                                "riskWarnings": ["规避低成交量高浮动合约"],
                                "suggestedFilters": ["可玩", "低风险"],
                                "warnings": [],
                            },
                            "marketSummary": market_summary,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            request_type="contract_radar_market_analysis",
            context={"mode": "contract_radar_market_analysis", "inst_id": "MARKET", "bar": market_summary.get("scan", {}).get("bar")},
        )
        parsed = extract_json_object(str(completion["content"]))
        return parse_radar_market_llm_analysis(parsed, market_summary)
    except ValueError as exc:
        return fallback_radar_market_analysis(market_summary, f"{str(exc)}已使用指标分析，可稍后重试刷新 AI。")
    except Exception as exc:
        if isinstance(exc, LlmCompletionError):
            return fallback_radar_market_analysis(market_summary, f"AI 大盘分析暂不可用，已使用指标分析：{str(exc)[:160]}")
        return fallback_radar_market_analysis(market_summary, "AI 大盘分析暂不可用，已使用指标分析。")


def cached_radar_market_analysis(request: RadarScanRequest, radar_payload: dict[str, Any], force: bool = False) -> dict[str, Any]:
    market_summary = radar_payload.get("marketSummary") if isinstance(radar_payload.get("marketSummary"), dict) else None
    if market_summary is None:
        market_summary = build_radar_market_summary(radar_payload)
    cache_key = radar_market_analysis_key(request, radar_payload)
    now = now_ms()
    snapshot = None if force else load_radar_analysis_snapshot(cache_key)
    if snapshot:
        age_ms = now - int(snapshot["ts"])
        if age_ms <= RADAR_ANALYSIS_CACHE_SECONDS * 1000:
            return radar_analysis_payload_with_cache_meta(snapshot["payload"], "radar-analysis-cache", int(snapshot["ts"]))

    payload = run_radar_market_llm_analysis(market_summary)
    ts = now_ms()
    save_radar_analysis_snapshot(cache_key, payload, ts)
    return radar_analysis_payload_with_cache_meta(payload, str(payload.get("source") or "radar-analysis"), ts)


def position_size(position: dict[str, Any]) -> Decimal:
    value = safe_decimal(position.get("pos"))
    return value if value is not None else Decimal("0")


def position_direction(position: dict[str, Any]) -> str:
    pos_side = str(position.get("posSide") or "net").lower()
    size = position_size(position)
    if size == 0:
        return "none"
    if pos_side == "long":
        return "long"
    if pos_side == "short":
        return "short"
    return "long" if size > 0 else "short"


def automation_position_state(account_payload: dict[str, Any], inst_id: str) -> dict[str, Any]:
    rows = [
        dict(position)
        for position in account_payload.get("positions", [])
        if str(position.get("instId") or "").upper() == inst_id.upper() and position_size(position) != 0
    ]
    long_rows = [row for row in rows if position_direction(row) == "long"]
    short_rows = [row for row in rows if position_direction(row) == "short"]
    long_contracts = sum((abs(position_size(row)) for row in long_rows), Decimal("0"))
    short_contracts = sum((abs(position_size(row)) for row in short_rows), Decimal("0"))
    side = "none"
    if long_contracts > 0 and short_contracts > 0:
        side = "both"
    elif long_contracts > 0:
        side = "long"
    elif short_contracts > 0:
        side = "short"
    return {
        "rows": rows,
        "longRows": long_rows,
        "shortRows": short_rows,
        "longContracts": long_contracts,
        "shortContracts": short_contracts,
        "totalContracts": long_contracts + short_contracts,
        "side": side,
    }


def strategy_percent_value(strategy: dict[str, Any], key: str) -> Decimal:
    try:
        value = Decimal(str(strategy.get(key) or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")
    return value if value > 0 else Decimal("0")


def position_profit_pct(position: dict[str, Any]) -> Decimal | None:
    avg_px = safe_decimal(position.get("avgPx"))
    mark_px = safe_decimal(position.get("markPx"))
    side = position_direction(position)
    if avg_px and avg_px > 0 and mark_px and mark_px > 0:
        if side == "long":
            return (mark_px - avg_px) / avg_px * Decimal("100")
        if side == "short":
            return (avg_px - mark_px) / avg_px * Decimal("100")

    upl_ratio = safe_decimal(position.get("uplRatio"))
    if upl_ratio is not None:
        return upl_ratio * Decimal("100")
    return None


def automation_exit_signal(strategy: dict[str, Any], account_payload: dict[str, Any]) -> dict[str, Any] | None:
    if str(strategy.get("execution_mode") or "") != "simulated_auto":
        return None
    take_profit_pct = strategy_percent_value(strategy, "take_profit_pct")
    stop_loss_pct = strategy_percent_value(strategy, "stop_loss_pct")
    if take_profit_pct <= 0 and stop_loss_pct <= 0:
        return None

    position_state = automation_position_state(account_payload, str(strategy["inst_id"]))
    for position in position_state["rows"]:
        profit_pct = position_profit_pct(position)
        if profit_pct is None:
            continue
        side = position_direction(position)
        size = abs(position_size(position))
        mark_px = str(position.get("markPx") or position.get("last") or position.get("avgPx") or "")
        common = {
            "side": None,
            "pos_side": side if side in {"long", "short"} else None,
            "price": mark_px or None,
            "candle_ts": now_ms(),
            "sz": decimal_display(size),
            "profit_pct": decimal_display(profit_pct),
            "position": position,
            "record_hold": True,
        }
        if stop_loss_pct > 0 and profit_pct <= -stop_loss_pct:
            return {
                **common,
                "action": "stop_loss",
                "reason": (
                    f"触发止损：当前浮动 {decimal_display(profit_pct)}%，"
                    f"已达到止损阈值 -{decimal_display(stop_loss_pct)}%。"
                ),
            }
        if take_profit_pct > 0 and profit_pct >= take_profit_pct:
            return {
                **common,
                "action": "take_profit",
                "reason": (
                    f"触发止盈：当前浮动 {decimal_display(profit_pct)}%，"
                    f"已达到止盈阈值 {decimal_display(take_profit_pct)}%。"
                ),
            }
    return None


def account_summary_for_llm(account_payload: dict[str, Any]) -> dict[str, Any]:
    summary = account_payload.get("summary") if isinstance(account_payload.get("summary"), dict) else {}
    positions = account_payload.get("positions") if isinstance(account_payload.get("positions"), list) else []
    return {
        "environment": account_payload.get("environment") or "simulated",
        "source": account_payload.get("source") or "",
        "totalEq": summary.get("totalEq") or summary.get("eqUsd") or "",
        "adjEq": summary.get("adjEq") or "",
        "availableEq": summary.get("availEq") or summary.get("availBal") or "",
        "positionCount": len([item for item in positions if position_size(item) != 0]),
    }


def recent_signals_for_llm(strategy_id: int, limit: int = 8) -> list[dict[str, Any]]:
    rows = database.list_automation_signals(strategy_id=strategy_id, limit=limit) if strategy_id else []
    return [
        {
            "ts": row.get("ts"),
            "action": row.get("action"),
            "decision": row.get("decision"),
            "price": row.get("price"),
            "message": row.get("message"),
        }
        for row in rows
    ]


def llm_direct_signal_prompt(
    strategy: dict[str, Any],
    candles: list[dict[str, Any]],
    account_payload: dict[str, Any],
    config: dict[str, Any],
) -> str:
    position_state = automation_position_state(account_payload, str(strategy["inst_id"]))
    payload = {
        "task": "generate_okx_perpetual_signal",
        "mode": "direct_signal",
        "constraints": [
            "只基于输入数据判断，不编造行情",
            "action 只能是 long、short、hold",
            f"confidence 必须是 0-100；低于 {AUTOMATION_LLM_MIN_CONFIDENCE} 系统不会自动交易",
            "不要输出 Markdown，只输出 JSON 对象",
            "LLM 不直接下单，系统会做风控并只在 OKX 模拟盘执行",
        ],
        "expected_json_schema": {
            "action": "long|short|hold",
            "confidence": "0-100 integer",
            "summary": "一句话交易判断",
            "reasons": ["判断依据"],
            "risks": ["主要风险"],
            "invalidation": "信号失效条件",
            "notes": "补充说明",
        },
        "strategy": {
            "id": strategy.get("id"),
            "name": strategy.get("name"),
            "inst_id": strategy.get("inst_id"),
            "bar": strategy.get("bar"),
            "execution_mode": strategy.get("execution_mode"),
            "td_mode": strategy.get("td_mode"),
            "ord_type": strategy.get("ord_type"),
            "sz": strategy.get("sz"),
            "max_order_contracts": strategy.get("max_order_contracts"),
            "max_position_contracts": strategy.get("max_position_contracts"),
            "min_confidence": AUTOMATION_LLM_MIN_CONFIDENCE,
        },
        "market_summary": candle_market_summary(candles),
        "recent_candles": [compact_candle_for_llm(item) for item in candles[-AUTOMATION_LLM_PROMPT_CANDLES:]],
        "history_scope": {
            "summary_candles": min(len(candles), AUTOMATION_LLM_LOOKBACK_CANDLES),
            "detail_candles": min(len(candles), AUTOMATION_LLM_PROMPT_CANDLES),
        },
        "current_position": {
            "side": position_state["side"],
            "longContracts": decimal_display(position_state["longContracts"]),
            "shortContracts": decimal_display(position_state["shortContracts"]),
            "totalContracts": decimal_display(position_state["totalContracts"]),
        },
        "recent_signals": recent_signals_for_llm(int(strategy.get("id") or 0)),
        "account_summary": account_summary_for_llm(account_payload),
        "llm_config": {"provider": config.get("provider"), "model": config.get("model")},
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def normalize_direct_llm_signal(
    parsed: dict[str, Any],
    config: dict[str, Any],
    raw_text: str,
    price: str,
    candle_ts: int,
    completion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action = str(parsed.get("action") or parsed.get("recommendation") or "hold").strip().lower()
    if action in {"buy", "bullish", "approve_long"}:
        action = "long"
    elif action in {"sell", "bearish", "approve_short"}:
        action = "short"
    elif action in {"observe", "reject"}:
        action = "hold"
    if action not in AUTOMATION_ACTIONS:
        raise ValueError("LLM action 必须是 long、short 或 hold。")

    direct_config = dict(config)
    direct_config["mode"] = "direct_signal"
    parsed_for_analysis = dict(parsed)
    parsed_for_analysis["recommendation"] = action
    analysis = normalize_llm_analysis(parsed_for_analysis, direct_config, raw_text)
    if completion:
        analysis = attach_llm_completion_meta(analysis, completion)
    summary = analysis.get("summary") or "LLM 已生成交易判断。"
    reasons = "；".join(analysis.get("reasons") or [])
    reason = f"{summary}{' ' + reasons if reasons else ''}"
    payload = {
        "action": action,
        "side": "buy" if action == "long" else "sell" if action == "short" else None,
        "pos_side": "long" if action == "long" else "short" if action == "short" else None,
        "price": price,
        "candle_ts": candle_ts,
        "reason": reason,
        "llm_analysis": analysis,
        "llm_confidence": analysis["confidence"],
        "record_hold": True,
    }
    if completion:
        usage_log = completion.get("usage_log") if isinstance(completion.get("usage_log"), dict) else None
        usage_view = llm_usage_log_view(usage_log)
        if usage_view:
            payload["llm_usage"] = usage_view
            payload["llm_usage_log_id"] = usage_view.get("id")
    return payload


def llm_direct_signal(strategy: dict[str, Any], candles: list[dict[str, Any]], account_payload: dict[str, Any]) -> dict[str, Any]:
    price = str(candles[-1].get("close") or "") if candles else ""
    candle_ts = int(candles[-1].get("ts") or 0) if candles else 0
    config = stored_llm_config()
    if not config.get("enabled"):
        return {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": price or None,
            "candle_ts": candle_ts,
            "reason": "LLM 未启用，无法生成直接交易信号。",
            "llm_error": "LLM 未启用",
            "llm_config_error": True,
            "record_hold": True,
        }
    try:
        prompt = llm_direct_signal_prompt(strategy, candles, account_payload, config)
        completion = llm_chat_completion(
            config,
            [
                {"role": "system", "content": str(config["systemPrompt"])},
                {"role": "user", "content": prompt},
            ],
            request_type="direct_signal",
            context={
                "strategy_id": int(strategy.get("id") or 0) or None,
                "inst_id": strategy.get("inst_id"),
                "bar": strategy.get("bar"),
            },
        )
        raw_text = str(completion["content"])
        return normalize_direct_llm_signal(extract_json_object(raw_text), config, raw_text, price, candle_ts, completion)
    except Exception as exc:
        timeout_seconds = llm_request_timeout_seconds(config)
        usage_log = llm_usage_log_view(exc.usage_log) if isinstance(exc, LlmCompletionError) else None
        return {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": price or None,
            "candle_ts": candle_ts,
            "reason": f"LLM 判断失败：{exc}",
            "llm_error": str(exc)[:1200],
            "llm_provider": config.get("provider"),
            "llm_model": config.get("model"),
            "llm_timeout_seconds": timeout_seconds,
            "llm_usage": usage_log,
            "llm_usage_log_id": usage_log.get("id") if usage_log else None,
            "record_hold": True,
        }


def closed_strategy_candles(inst_id: str, bar: str, limit: int) -> list[dict[str, Any]]:
    try:
        rows = client.get_candles(inst_id, bar, limit)
        database.upsert_candles(inst_id, bar, rows)
    except OkxError:
        rows = database.latest_candles(inst_id, bar, limit)
    closed = [dict(item) for item in rows if str(item.get("confirm", "1")) == "1"]
    return closed or [dict(item) for item in rows]


def average(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / Decimal(len(values))


def ma_cross_signal(strategy: dict[str, Any]) -> dict[str, Any]:
    inst_id = str(strategy["inst_id"])
    bar = str(strategy["bar"])
    fast = int(strategy["fast_window"])
    slow = int(strategy["slow_window"])
    limit = max(slow + 3, 80)
    candles = closed_strategy_candles(inst_id, bar, limit)
    if len(candles) < slow + 1:
        return {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": None,
            "candle_ts": 0,
            "reason": f"K线数量不足，需要至少 {slow + 1} 根已收盘K线。",
        }

    closes = [Decimal(str(item["close"])) for item in candles]
    previous_fast = average(closes[-fast - 1 : -1])
    previous_slow = average(closes[-slow - 1 : -1])
    current_fast = average(closes[-fast:])
    current_slow = average(closes[-slow:])
    price = Decimal(str(candles[-1]["close"]))
    candle_ts = int(candles[-1]["ts"])

    base_reason = (
        f"MA{fast}={decimal_display(current_fast)}，MA{slow}={decimal_display(current_slow)}，"
        f"上一根 MA{fast}={decimal_display(previous_fast)}，MA{slow}={decimal_display(previous_slow)}。"
    )
    if previous_fast <= previous_slow and current_fast > current_slow:
        return {
            "action": "long",
            "side": "buy",
            "pos_side": "long",
            "price": decimal_display(price),
            "candle_ts": candle_ts,
            "reason": f"快线上穿慢线，产生做多信号。{base_reason}",
        }
    if previous_fast >= previous_slow and current_fast < current_slow:
        return {
            "action": "short",
            "side": "sell",
            "pos_side": "short",
            "price": decimal_display(price),
            "candle_ts": candle_ts,
            "reason": f"快线下穿慢线，产生做空信号。{base_reason}",
        }
    return {
        "action": "hold",
        "side": None,
        "pos_side": None,
        "price": decimal_display(price),
        "candle_ts": candle_ts,
        "reason": f"均线未交叉，保持观望。{base_reason}",
    }


def current_position_contracts(account_payload: dict[str, Any], inst_id: str) -> Decimal:
    return automation_position_state(account_payload, inst_id)["totalContracts"]


def target_position_side(action: str) -> str:
    return "long" if action == "long" else "short" if action == "short" else "none"


def opposite_position_side(action: str) -> str:
    return "short" if action == "long" else "long" if action == "short" else "none"


def automation_execution_action(signal_action: str, position_state: dict[str, Any] | None) -> str:
    if signal_action not in {"long", "short"}:
        return "none"
    if not position_state:
        return "open"
    target_side = target_position_side(signal_action)
    opposite_side = opposite_position_side(signal_action)
    same_contracts = position_state[f"{target_side}Contracts"]
    opposite_contracts = position_state[f"{opposite_side}Contracts"]
    if opposite_contracts > 0 and same_contracts > 0:
        return "close_opposite"
    if opposite_contracts > 0:
        return "reverse"
    if same_contracts > 0:
        return "skip_same_direction"
    return "open"


def risk_check_item(key: str, label: str, status: str, message: str, value: str = "") -> dict[str, str]:
    return {"key": key, "label": label, "status": status, "message": message, "value": value}


def automation_risk_preview(strategy: dict[str, Any], signal: dict[str, Any] | None = None) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    blocked_messages: list[str] = []
    warning_messages: list[str] = []

    def add_check(key: str, label: str, status: str, message: str, value: str = "") -> None:
        checks.append(risk_check_item(key, label, status, message, value))
        if status == "block":
            blocked_messages.append(message)
        elif status == "warn":
            warning_messages.append(message)

    execution_mode = str(strategy.get("execution_mode") or "")
    template = str(strategy.get("template") or "")
    signal_action = str((signal or {}).get("action") or "unknown")
    llm_confidence_raw = (signal or {}).get("llm_confidence")
    llm_confidence = coerce_int(llm_confidence_raw, -1, -1, 100) if llm_confidence_raw is not None else -1
    if signal_action in {"long", "short"}:
        add_check("signal", "当前信号", "pass", f"当前策略产生{'做多' if signal_action == 'long' else '做空'}候选信号。", signal_action)
    elif signal_action == "hold":
        add_check("signal", "当前信号", "warn", "当前没有做多/做空候选信号，自动执行不会提交订单。", "观望")
    else:
        add_check("signal", "当前信号", "warn", "尚未计算当前策略信号。", "未知")

    if execution_mode == "signal_only":
        add_check("execution_mode", "执行模式", "warn", "当前为只生成信号模式，不会自动下单。", "只生成信号")
    elif execution_mode == "simulated_auto":
        add_check("execution_mode", "执行模式", "pass", "当前为虚拟盘自动模式，真实盘不会自动下单。", "虚拟盘自动")
    else:
        add_check("execution_mode", "执行模式", "block", "执行模式不受支持。", execution_mode)

    global_state = automation_global_state()
    if global_state.get("globalPaused"):
        add_check(
            "global_pause",
            "全局暂停",
            "block",
            global_state.get("pauseReason") or "自动交易当前处于全局暂停状态。",
            "已暂停",
        )
    if global_state.get("circuitBreakerActive"):
        add_check(
            "circuit_breaker",
            "熔断状态",
            "block",
            global_state.get("circuitReason") or "自动交易已触发熔断，需人工恢复后继续。",
            "已熔断",
        )

    llm_config = stored_llm_config() if template == "llm_direct" else {}
    if template == "llm_direct":
        if not llm_config.get("enabled"):
            add_check("llm", "LLM 信号", "block", "LLM 未启用，无法生成直接交易信号。", "未启用")
        elif signal and signal.get("llm_error"):
            add_check("llm", "LLM 信号", "block", f"LLM 判断失败：{signal.get('llm_error')}", "失败")
        elif signal_action in {"long", "short"} and llm_confidence < AUTOMATION_LLM_MIN_CONFIDENCE:
            add_check(
                "llm",
                "LLM 信号",
                "block",
                f"LLM 置信度 {llm_confidence} 低于 {AUTOMATION_LLM_MIN_CONFIDENCE}，不会自动交易。",
                f"{llm_confidence}/{AUTOMATION_LLM_MIN_CONFIDENCE}",
            )
        elif signal_action in {"long", "short"}:
            add_check(
                "llm",
                "LLM 信号",
                "pass",
                "LLM 置信度达到自动交易阈值。",
                f"{llm_confidence}/{AUTOMATION_LLM_MIN_CONFIDENCE}",
            )
        else:
            add_check("llm", "LLM 信号", "warn", "LLM 当前未给出做多或做空信号。", "观望")

    has_credentials = settings.has_credentials_for_environment("simulated")
    if has_credentials:
        add_check("credentials", "虚拟盘 API", "pass", "虚拟盘 API 已配置。", "已配置")
    elif execution_mode == "simulated_auto":
        add_check("credentials", "虚拟盘 API", "block", "虚拟盘 API 未配置，无法自动下单。", "未配置")
    else:
        add_check("credentials", "虚拟盘 API", "warn", "虚拟盘 API 未配置；只生成信号模式仍可使用。", "未配置")

    size = decimal_value(str(strategy["sz"]), "策略下单张数")
    max_order = decimal_value(str(strategy["max_order_contracts"]), "单笔最大张数")
    max_position = decimal_value(str(strategy["max_position_contracts"]), "单合约最大持仓")
    take_profit_pct = strategy_percent_value(strategy, "take_profit_pct")
    stop_loss_pct = strategy_percent_value(strategy, "stop_loss_pct")
    if size > max_order:
        add_check(
            "max_order",
            "单笔限制",
            "block",
            "策略下单张数超过单笔最大张数，风控会拦截。",
            f"{decimal_display(size)} / {decimal_display(max_order)} 张",
        )
    else:
        add_check(
            "max_order",
            "单笔限制",
            "pass",
            "下单张数未超过单笔最大张数。",
            f"{decimal_display(size)} / {decimal_display(max_order)} 张",
        )

    if size > max_position:
        add_check(
            "max_position",
            "持仓上限",
            "block",
            "策略下单张数超过单合约最大持仓。",
            f"{decimal_display(size)} / {decimal_display(max_position)} 张",
        )
    else:
        add_check(
            "max_position",
            "持仓上限",
            "pass",
            "单笔下单后理论上不会超过单合约持仓上限。",
            f"{decimal_display(size)} / {decimal_display(max_position)} 张",
        )

    cooldown_remaining = 0
    latest_signal = None
    strategy_id = int(strategy.get("id") or 0)
    cooldown_ms = int(strategy.get("cooldown_seconds") or 0) * 1000
    if strategy_id and hasattr(database, "latest_actionable_automation_signal"):
        latest_signal = database.latest_actionable_automation_signal(strategy_id)
    if latest_signal and cooldown_ms > 0:
        elapsed_ms = now_ms() - int(latest_signal.get("ts") or 0)
        if elapsed_ms < cooldown_ms:
            cooldown_remaining = max(1, int((cooldown_ms - elapsed_ms) / 1000))
            add_check("cooldown", "冷却期", "block", f"仍在冷却期，{cooldown_remaining} 秒后才允许下一次自动执行。", f"{cooldown_remaining} 秒")
        else:
            add_check("cooldown", "冷却期", "pass", "冷却期已结束。", "已结束")
    elif cooldown_ms > 0:
        add_check("cooldown", "冷却期", "pass", "当前没有需要等待的冷却记录。", f"{int(cooldown_ms / 1000)} 秒")
    else:
        add_check("cooldown", "冷却期", "pass", "策略未设置冷却时间。", "0 秒")

    if take_profit_pct > 0 or stop_loss_pct > 0:
        add_check(
            "exit_risk",
            "止盈止损",
            "pass",
            "已设置持仓浮动触发平仓；触发时会优先于新开仓信号执行。",
            f"止盈 {decimal_display(take_profit_pct)}% / 止损 {decimal_display(stop_loss_pct)}%",
        )
    else:
        add_check("exit_risk", "止盈止损", "pass", "未设置按幅度止盈止损。", "关闭")

    account_source = ""
    current_contracts: Decimal | None = None
    projected_contracts: Decimal | None = None
    execution_action = "none"
    position_side = "unknown"
    if has_credentials:
        try:
            account_payload = refresh_account_cache_sync("simulated")
        except Exception as exc:
            fallback = account_fallback_response("simulated", str(exc))
            if fallback:
                account_payload = fallback
                account_source = str(fallback.get("source") or "cache")
            else:
                account_payload = {}
                if execution_mode == "simulated_auto":
                    add_check("account", "账户持仓", "block", f"无法获取虚拟盘账户/持仓：{exc}", "获取失败")
                else:
                    add_check("account", "账户持仓", "warn", f"无法获取虚拟盘账户/持仓：{exc}", "获取失败")
        else:
            account_source = str(account_payload.get("source") or "okx")

        if account_payload:
            position_state = automation_position_state(account_payload, str(strategy["inst_id"]))
            current_contracts = position_state["totalContracts"]
            position_side = str(position_state["side"])
            execution_action = automation_execution_action(signal_action, position_state)
            projected_contracts = size if execution_action in {"open", "reverse"} else current_contracts
            if execution_action == "skip_same_direction":
                add_check(
                    "position",
                    "当前持仓",
                    "pass",
                    "当前已有同向持仓，系统会跳过重复开仓，只记录信号。",
                    f"{position_side} {decimal_display(current_contracts)} 张",
                )
            elif execution_action in {"reverse", "close_opposite"}:
                add_check(
                    "position",
                    "当前持仓",
                    "pass",
                    "当前有反向持仓，系统会先市价全平反向仓位，再按信号处理。",
                    f"{position_side} {decimal_display(current_contracts)} 张",
                )
            elif projected_contracts is not None and projected_contracts > max_position:
                add_check(
                    "position",
                    "当前持仓",
                    "block",
                    "自动下单后会超过单合约最大持仓。",
                    f"{decimal_display(projected_contracts)} / {decimal_display(max_position)} 张",
                )
            else:
                add_check(
                    "position",
                    "当前持仓",
                    "pass",
                    "当前该合约无持仓，满足自动开仓条件。",
                    f"{decimal_display(current_contracts)} 张",
                )
    else:
        add_check("position", "当前持仓", "warn", "未配置虚拟盘 API，暂不能读取真实持仓。", "未知")

    allowed = not blocked_messages and execution_mode == "simulated_auto" and signal_action in {"long", "short"}
    severity = "ok" if allowed else "blocked" if blocked_messages else "warning"
    if allowed:
        if execution_action == "skip_same_direction":
            message = "当前配置通过风控，但已有同向持仓，运行时会跳过重复开仓。"
        elif execution_action in {"reverse", "close_opposite"}:
            message = "当前配置通过风控，反向信号会先市价全平再开新方向。"
        else:
            message = "当前配置通过风控，可提交虚拟盘订单。"
    elif blocked_messages:
        message = blocked_messages[0]
    elif warning_messages:
        message = warning_messages[0]
    else:
        message = "当前配置不会自动提交订单。"

    return {
        "allowed": allowed,
        "severity": severity,
        "message": message,
        "checks": checks,
        "signalAction": signal_action,
        "llmConfidence": llm_confidence if llm_confidence >= 0 else None,
        "minConfidence": AUTOMATION_LLM_MIN_CONFIDENCE,
        "executionAction": execution_action,
        "positionSide": position_side,
        "currentPositionContracts": decimal_display(current_contracts) if current_contracts is not None else "",
        "projectedPositionContracts": decimal_display(projected_contracts) if projected_contracts is not None else "",
        "orderContracts": decimal_display(size),
        "maxOrderContracts": decimal_display(max_order),
        "maxPositionContracts": decimal_display(max_position),
        "takeProfitPct": decimal_display(take_profit_pct),
        "stopLossPct": decimal_display(stop_loss_pct),
        "cooldownRemainingSeconds": cooldown_remaining,
        "accountSource": account_source,
        "updatedAt": now_ms(),
    }


def automation_risk_check(strategy: dict[str, Any], signal: dict[str, Any]) -> tuple[bool, str]:
    preview = automation_risk_preview(strategy, signal)
    return bool(preview["allowed"]), str(preview["message"])


def record_automation_signal(
    strategy: dict[str, Any],
    signal: dict[str, Any],
    decision: str,
    message: str,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_json_payload = dict(signal)
    if raw_payload:
        raw_json_payload["execution_payload"] = raw_payload
    llm_analysis = signal.get("llm_analysis") if isinstance(signal.get("llm_analysis"), dict) else None
    if not llm_analysis and str(strategy.get("template") or "") != "llm_direct":
        llm_analysis = analyze_signal_with_llm(strategy, signal, decision, message)
    if llm_analysis:
        raw_json_payload["llm_analysis"] = llm_analysis
    payload = {
        "strategy_id": int(strategy["id"]),
        "ts": now_ms(),
        "environment": "simulated",
        "inst_id": strategy["inst_id"],
        "bar": strategy["bar"],
        "template": strategy["template"],
        "action": signal["action"],
        "side": signal.get("side"),
        "pos_side": signal.get("pos_side"),
        "price": signal.get("price"),
        "sz": signal.get("sz") or (strategy["sz"] if signal["action"] != "hold" else None),
        "decision": decision,
        "reason": signal.get("reason"),
        "message": message,
        "raw_json": json.dumps(raw_json_payload, ensure_ascii=False, separators=(",", ":")),
    }
    row = database.insert_automation_signal(payload)
    if row:
        attach_automation_audit_records(row, raw_json_payload)
        alert_context = automation_alert_from_record(strategy, signal, decision, message, raw_json_payload)
        if alert_context:
            severity, source, alert_message = alert_context
            create_automation_alert(
                severity,
                source,
                alert_message,
                strategy_id=int(strategy["id"]),
                signal_id=int(row["id"]),
                raw_payload={
                    "decision": decision,
                    "strategy_id": int(strategy["id"]),
                    "signal_id": int(row["id"]),
                    "message": message,
                    "signal": signal,
                    "execution_payload": raw_payload or {},
                },
            )
        broadcast_realtime_event(
            {
                "type": "automation.signal",
                "topic": "automation.signal",
                "source": "automation",
                "data": normalize_automation_signal_row(row),
                "refreshRequired": True,
            },
            topic="automation.signal",
        )
    return row


def normalize_automation_risk_snapshot_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    normalized = dict(row)
    normalized["allowed"] = bool(normalized.get("allowed"))
    try:
        checks = json.loads(str(normalized.get("checks_json") or "[]"))
    except json.JSONDecodeError:
        checks = []
    normalized["checks"] = checks if isinstance(checks, list) else []
    try:
        raw_payload = json.loads(str(normalized.get("raw_json") or "{}"))
    except json.JSONDecodeError:
        raw_payload = {}
    normalized["raw"] = raw_payload if isinstance(raw_payload, dict) else {}
    return normalized


def normalize_automation_execution_step_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    try:
        normalized["request"] = json.loads(str(normalized.get("request_json") or "{}"))
    except json.JSONDecodeError:
        normalized["request"] = {}
    try:
        normalized["response"] = json.loads(str(normalized.get("response_json") or "{}"))
    except json.JSONDecodeError:
        normalized["response"] = {}
    return normalized


def normalize_automation_alert_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["active"] = normalized.get("acknowledged_at") in (None, "", 0)
    try:
        raw_payload = json.loads(str(normalized.get("raw_json") or "{}"))
    except json.JSONDecodeError:
        raw_payload = {}
    normalized["raw"] = raw_payload if isinstance(raw_payload, dict) else {}
    return normalized


def enrich_automation_signal_detail(row: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_automation_signal_row(row)
    signal_id = int(normalized.get("id") or 0)
    if signal_id and hasattr(database, "get_automation_risk_snapshot"):
        risk_snapshot = normalize_automation_risk_snapshot_row(database.get_automation_risk_snapshot(signal_id))
        if risk_snapshot:
            normalized["riskSnapshot"] = risk_snapshot
        execution_steps = (
            [normalize_automation_execution_step_row(item) for item in database.list_automation_execution_steps(signal_id)]
            if hasattr(database, "list_automation_execution_steps")
            else []
        )
        if execution_steps:
            normalized["executionSteps"] = execution_steps
    raw_payload = signal_raw_payload(normalized) if isinstance(normalized, dict) else None
    if isinstance(raw_payload, dict):
        if "riskSnapshot" not in normalized and isinstance(raw_payload.get("risk_snapshot"), dict):
            normalized["riskSnapshot"] = raw_payload["risk_snapshot"]
        if "executionSteps" not in normalized and isinstance(raw_payload.get("execution_steps"), list):
            normalized["executionSteps"] = raw_payload["execution_steps"]
    return normalized


def open_order_request(strategy: dict[str, Any], signal: dict[str, Any]) -> PlaceSimOrderRequest:
    if not signal.get("side") or not signal.get("pos_side"):
        raise HTTPException(status_code=400, detail="信号缺少可执行的买卖方向。")
    return PlaceSimOrderRequest(
        instId=strategy["inst_id"],
        tdMode=strategy["td_mode"],
        side=str(signal["side"]),
        posSide=str(signal["pos_side"]),
        ordType=strategy["ord_type"],
        sz=strategy["sz"],
        px=signal.get("price") if strategy["ord_type"] in ORDER_TYPES_WITH_PRICE else None,
        reduceOnly=False,
    )


def close_request_for_position(strategy: dict[str, Any], position: dict[str, Any]) -> ClosePositionRequest:
    pos_side = str(position.get("posSide") or "net").lower()
    if pos_side not in {"long", "short"}:
        pos_side = "net"
    return ClosePositionRequest(
        instId=strategy["inst_id"],
        mgnMode=str(position.get("mgnMode") or strategy["td_mode"]),
        posSide=pos_side,
        autoCxl=True,
    )


def execute_automation_order(strategy: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    account_payload = refresh_account_cache_sync("simulated")
    position_state = automation_position_state(account_payload, str(strategy["inst_id"]))
    execution_action = automation_execution_action(str(signal.get("action") or ""), position_state)
    target_side = target_position_side(str(signal.get("action") or ""))
    opposite_side = opposite_position_side(str(signal.get("action") or ""))
    close_rows = position_state[f"{opposite_side}Rows"] if opposite_side in {"long", "short"} else []

    if execution_action == "skip_same_direction":
        return {
            "ok": True,
            "action": "skip_same_direction",
            "message": "已有同向持仓，未重复开仓。",
            "positionSide": position_state["side"],
            "steps": [
                {
                    "action": "skip_same_direction",
                    "status": "ok",
                    "message": "已有同向持仓，未重复开仓。",
                    "request": {"signal": signal},
                    "result": {"positionSide": position_state["side"]},
                }
            ],
        }

    steps: list[dict[str, Any]] = []
    if execution_action in {"reverse", "close_opposite"}:
        for position in close_rows:
            close_result = close_position_for_environment("simulated", close_request_for_position(strategy, position))
            close_request = close_request_for_position(strategy, position)
            steps.append(
                {
                    "action": "close-position",
                    "status": "ok",
                    "message": str(close_result.get("message") or "已提交平仓。"),
                    "posSide": position_direction(position),
                    "request": close_request.model_dump(),
                    "result": close_result,
                }
            )

    should_open = execution_action in {"open", "reverse"}
    if execution_action == "close_opposite":
        should_open = position_state[f"{target_side}Contracts"] <= 0
    if should_open:
        open_request = open_order_request(strategy, signal)
        open_result = place_order_for_environment("simulated", open_request)
        steps.append(
            {
                "action": "place",
                "status": "ok",
                "message": str(open_result.get("message") or "已提交开仓。"),
                "posSide": target_side,
                "request": open_request.model_dump(),
                "result": open_result,
            }
        )

    return {
        "ok": True,
        "action": execution_action,
        "message": "自动交易执行完成。",
        "steps": steps,
    }


def execute_automation_exit(strategy: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    position = signal.get("position")
    if not isinstance(position, dict):
        raise HTTPException(status_code=400, detail="止盈止损信号缺少持仓信息。")
    close_request = close_request_for_position(strategy, position)
    close_result = close_position_for_environment("simulated", close_request)
    return {
        "ok": True,
        "action": signal.get("action"),
        "message": signal.get("reason") or "止盈止损平仓已提交。",
        "steps": [
            {
                "action": str(signal.get("action") or "close-position"),
                "status": "ok",
                "message": str(close_result.get("message") or signal.get("reason") or "止盈止损平仓已提交。"),
                "posSide": position_direction(position),
                "request": close_request.model_dump(),
                "result": close_result,
            }
        ],
        "profitPct": signal.get("profit_pct"),
    }


def execute_automation_open_order(strategy: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    order = PlaceSimOrderRequest(
        instId=strategy["inst_id"],
        tdMode=strategy["td_mode"],
        side=str(signal["side"]),
        posSide=str(signal["pos_side"]),
        ordType=strategy["ord_type"],
        sz=strategy["sz"],
        px=signal.get("price") if strategy["ord_type"] in ORDER_TYPES_WITH_PRICE else None,
        reduceOnly=False,
    )
    return place_order_for_environment("simulated", order)


def automation_signal_for_candle(
    candles: list[dict[str, Any]], index: int, fast: int, slow: int
) -> dict[str, Any]:
    closes = [Decimal(str(item["close"])) for item in candles[: index + 1]]
    previous_fast = average(closes[-fast - 1 : -1])
    previous_slow = average(closes[-slow - 1 : -1])
    current_fast = average(closes[-fast:])
    current_slow = average(closes[-slow:])
    price = Decimal(str(candles[index]["close"]))
    candle_ts = int(candles[index]["ts"])
    base_reason = (
        f"MA{fast}={decimal_display(current_fast)}，MA{slow}={decimal_display(current_slow)}，"
        f"上一根 MA{fast}={decimal_display(previous_fast)}，MA{slow}={decimal_display(previous_slow)}。"
    )
    if previous_fast <= previous_slow and current_fast > current_slow:
        return {
            "action": "long",
            "side": "buy",
            "pos_side": "long",
            "price": decimal_display(price),
            "candle_ts": candle_ts,
            "reason": f"快线上穿慢线，产生做多信号。{base_reason}",
        }
    if previous_fast >= previous_slow and current_fast < current_slow:
        return {
            "action": "short",
            "side": "sell",
            "pos_side": "short",
            "price": decimal_display(price),
            "candle_ts": candle_ts,
            "reason": f"快线下穿慢线，产生做空信号。{base_reason}",
        }
    return {
        "action": "hold",
        "side": None,
        "pos_side": None,
        "price": decimal_display(price),
        "candle_ts": candle_ts,
        "reason": f"均线未交叉，保持观望。{base_reason}",
    }


def estimate_contract_value(inst_id: str) -> Decimal:
    for instrument in database.list_instruments(query=inst_id, limit=20):
        if str(instrument.get("inst_id") or "").upper() != inst_id:
            continue
        try:
            value = Decimal(str(instrument.get("ct_val") or ""))
        except InvalidOperation:
            break
        return value if value > 0 else Decimal("1")
    return Decimal("1")


def estimated_linear_pnl(side: str, entry_price: Decimal, exit_price: Decimal, contracts: Decimal, contract_value: Decimal) -> Decimal:
    if side == "long":
        return (exit_price - entry_price) * contracts * contract_value
    return (entry_price - exit_price) * contracts * contract_value


def load_backtest_candles(inst_id: str, bar: str, limit: int) -> list[dict[str, Any]]:
    try:
        rows = client.get_candles(inst_id, bar, limit)
        database.upsert_candles(inst_id, bar, rows)
    except OkxError:
        rows = database.latest_candles(inst_id, bar, limit)
    confirmed = [item for item in rows if str(item.get("confirm") or "1") != "0"]
    return confirmed[-limit:]


def run_ma_cross_backtest(strategy: dict[str, Any], limit: int, initial_capital: Decimal) -> dict[str, Any]:
    fast = int(strategy["fast_window"])
    slow = int(strategy["slow_window"])
    candles = load_backtest_candles(str(strategy["inst_id"]), str(strategy["bar"]), max(limit, slow + 3))
    if len(candles) < slow + 2:
        return {
            "ok": False,
            "message": f"K线数量不足，需要至少 {slow + 2} 根已收盘K线。",
            "candles": len(candles),
            "trades": [],
            "openPosition": None,
            "summary": {
                "signalCount": 0,
                "tradeCount": 0,
                "winRate": "0",
                "totalPnl": "0",
                "totalReturnPct": "0",
                "maxDrawdownPct": "0",
            },
        }

    contracts = decimal_value(str(strategy["sz"]), "策略下单张数")
    contract_value = estimate_contract_value(str(strategy["inst_id"]))
    realized_pnl = Decimal("0")
    equity = initial_capital
    peak_equity = initial_capital
    max_drawdown_pct = Decimal("0")
    position: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    signal_count = 0

    for index in range(slow, len(candles)):
        signal = automation_signal_for_candle(candles, index, fast, slow)
        action = str(signal["action"])
        price = Decimal(str(signal["price"]))
        if action in {"long", "short"}:
            signal_count += 1
            if position and position["side"] != action:
                pnl = estimated_linear_pnl(str(position["side"]), Decimal(str(position["entryPrice"])), price, contracts, contract_value)
                entry_notional = Decimal(str(position["entryPrice"])) * contracts * contract_value
                return_pct = pnl / entry_notional * Decimal("100") if entry_notional else Decimal("0")
                realized_pnl += pnl
                trades.append(
                    {
                        "side": position["side"],
                        "entryTs": position["entryTs"],
                        "exitTs": signal["candle_ts"],
                        "entryPrice": decimal_display(Decimal(str(position["entryPrice"]))),
                        "exitPrice": decimal_display(price),
                        "contracts": decimal_display(contracts),
                        "pnl": decimal_display(pnl),
                        "returnPct": decimal_display(return_pct),
                        "durationBars": index - int(position["entryIndex"]),
                        "exitReason": "反向均线交叉",
                    }
                )
                position = None
            if not position:
                position = {
                    "side": action,
                    "entryTs": signal["candle_ts"],
                    "entryPrice": decimal_display(price),
                    "entryIndex": index,
                    "reason": signal["reason"],
                }

        unrealized = Decimal("0")
        if position:
            unrealized = estimated_linear_pnl(str(position["side"]), Decimal(str(position["entryPrice"])), price, contracts, contract_value)
        equity = initial_capital + realized_pnl + unrealized
        if equity > peak_equity:
            peak_equity = equity
        if peak_equity > 0:
            drawdown_pct = (peak_equity - equity) / peak_equity * Decimal("100")
            if drawdown_pct > max_drawdown_pct:
                max_drawdown_pct = drawdown_pct

    last_price = Decimal(str(candles[-1]["close"]))
    open_position = None
    unrealized_pnl = Decimal("0")
    if position:
        unrealized_pnl = estimated_linear_pnl(str(position["side"]), Decimal(str(position["entryPrice"])), last_price, contracts, contract_value)
        entry_notional = Decimal(str(position["entryPrice"])) * contracts * contract_value
        open_return_pct = unrealized_pnl / entry_notional * Decimal("100") if entry_notional else Decimal("0")
        open_position = {
            "side": position["side"],
            "entryTs": position["entryTs"],
            "entryPrice": position["entryPrice"],
            "markPrice": decimal_display(last_price),
            "contracts": decimal_display(contracts),
            "unrealizedPnl": decimal_display(unrealized_pnl),
            "returnPct": decimal_display(open_return_pct),
            "durationBars": len(candles) - 1 - int(position["entryIndex"]),
        }

    wins = sum(1 for trade in trades if Decimal(str(trade["pnl"])) > 0)
    trade_count = len(trades)
    win_rate = Decimal(wins) / Decimal(trade_count) * Decimal("100") if trade_count else Decimal("0")
    total_pnl = realized_pnl + unrealized_pnl
    total_return_pct = total_pnl / initial_capital * Decimal("100") if initial_capital else Decimal("0")

    return {
        "ok": True,
        "message": "轻量回测完成，结果按收盘价估算，不含手续费、资金费、滑点和真实撮合。",
        "candles": len(candles),
        "bar": strategy["bar"],
        "instId": strategy["inst_id"],
        "contractValue": decimal_display(contract_value),
        "initialCapital": decimal_display(initial_capital),
        "summary": {
            "signalCount": signal_count,
            "tradeCount": trade_count,
            "winCount": wins,
            "winRate": decimal_display(win_rate),
            "realizedPnl": decimal_display(realized_pnl),
            "unrealizedPnl": decimal_display(unrealized_pnl),
            "totalPnl": decimal_display(total_pnl),
            "totalReturnPct": decimal_display(total_return_pct),
            "maxDrawdownPct": decimal_display(max_drawdown_pct),
        },
        "openPosition": open_position,
        "trades": trades[-30:],
    }


def llm_account_payload_for_signal() -> dict[str, Any]:
    if not settings.has_credentials_for_environment("simulated"):
        return {"environment": "simulated", "summary": {}, "positions": [], "source": "unconfigured"}
    try:
        return refresh_account_cache_sync("simulated")
    except Exception as exc:
        fallback = account_fallback_response("simulated", str(exc))
        if fallback:
            return fallback
        return {"environment": "simulated", "summary": {}, "positions": [], "source": "error", "warning": str(exc)}


def evaluate_automation_strategy(strategy: dict[str, Any], force: bool = False) -> dict[str, Any] | None:
    if not force and not bool(strategy.get("enabled")):
        return None
    if bool(strategy.get("archived")):
        return None

    if str(strategy.get("execution_mode") or "") == "simulated_auto" and settings.has_credentials_for_environment("simulated"):
        try:
            exit_signal = automation_exit_signal(strategy, refresh_account_cache_sync("simulated"))
        except Exception:
            exit_signal = None
        if exit_signal:
            preview = automation_risk_preview(strategy, exit_signal)
            global_block = automation_global_block_check(strategy, exit_signal)
            if global_block:
                return record_automation_signal(
                    strategy,
                    exit_signal,
                    "blocked",
                    str(global_block.get("message") or preview.get("message") or "自动交易已被全局状态拦截。"),
                    {"risk_snapshot": preview},
                )
            try:
                exit_result = execute_automation_exit(strategy, exit_signal)
            except HTTPException as exc:
                trigger_automation_circuit_breaker(str(exc.detail), strategy_id=int(strategy["id"]))
                return record_automation_signal(strategy, exit_signal, "failed", str(exc.detail), {"risk_snapshot": preview})
            except Exception as exc:
                trigger_automation_circuit_breaker(str(exc), strategy_id=int(strategy["id"]))
                return record_automation_signal(strategy, exit_signal, "failed", str(exc), {"risk_snapshot": preview})
            return record_automation_signal(
                strategy,
                exit_signal,
                "submitted",
                str(exit_result.get("message") or "止盈止损平仓已提交。"),
                {"risk_snapshot": preview, "execution_payload": exit_result, "execution_steps": exit_result.get("steps") or []},
            )

    if strategy["template"] == "llm_direct":
        candles = closed_strategy_candles(str(strategy["inst_id"]), str(strategy["bar"]), AUTOMATION_LLM_LOOKBACK_CANDLES)
        candle_ts = int(candles[-1].get("ts") or 0) if candles else 0
        if candle_ts and not force and int(strategy.get("last_eval_ts") or 0) >= candle_ts:
            return None
        if len(candles) < min(30, AUTOMATION_LLM_LOOKBACK_CANDLES):
            signal = {
                "action": "hold",
                "side": None,
                "pos_side": None,
                "price": str(candles[-1].get("close") or "") if candles else None,
                "candle_ts": candle_ts,
                "reason": "LLM 直接判断需要至少 30 根已收盘K线。",
                "record_hold": True,
            }
        else:
            signal = llm_direct_signal(strategy, candles, llm_account_payload_for_signal())
    elif strategy["template"] == "ma_cross":
        signal = ma_cross_signal(strategy)
    else:
        signal = {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": None,
            "candle_ts": 0,
            "reason": "策略模板不受支持。",
        }

    candle_ts = int(signal.get("candle_ts") or 0)
    if candle_ts and not force and int(strategy.get("last_eval_ts") or 0) >= candle_ts:
        return None

    if candle_ts:
        database.set_automation_strategy_last_eval(int(strategy["id"]), candle_ts, now_ms())

    global_block = automation_global_block_check(strategy, signal)
    if global_block and signal.get("action") in {"long", "short"}:
        return record_automation_signal(
            strategy,
            signal,
            "blocked",
            str(global_block.get("message") or "自动交易被全局状态拦截。"),
            {"risk_snapshot": automation_risk_preview(strategy, signal)},
        )

    if signal["action"] == "hold":
        if not force and not signal.get("record_hold"):
            return None
        decision = "blocked" if signal.get("llm_config_error") else "llm_failed" if signal.get("llm_error") else "observed"
        return record_automation_signal(
            strategy,
            signal,
            decision,
            signal.get("reason") or "未产生交易信号。",
            {"risk_snapshot": automation_risk_preview(strategy, signal)},
        )

    if strategy["execution_mode"] == "signal_only":
        return record_automation_signal(
            strategy,
            signal,
            "signal_only",
            "已记录信号，未自动下单。",
            {"risk_snapshot": automation_risk_preview(strategy, signal)},
        )

    preview = automation_risk_preview(strategy, signal)
    if not preview["allowed"]:
        return record_automation_signal(strategy, signal, "blocked", str(preview.get("message") or "自动交易被风控拦截。"), {"risk_snapshot": preview})

    try:
        order_result = execute_automation_order(strategy, signal)
    except HTTPException as exc:
        trigger_automation_circuit_breaker(str(exc.detail), strategy_id=int(strategy["id"]))
        return record_automation_signal(
            strategy,
            signal,
            "failed",
            str(exc.detail),
            {"risk_snapshot": preview},
        )
    except Exception as exc:
        trigger_automation_circuit_breaker(str(exc), strategy_id=int(strategy["id"]))
        return record_automation_signal(
            strategy,
            signal,
            "failed",
            str(exc),
            {"risk_snapshot": preview},
        )

    if order_result.get("action") == "skip_same_direction":
        return record_automation_signal(
            strategy,
            signal,
            "skipped",
            str(order_result.get("message") or "已有同向持仓，未重复开仓。"),
            {"risk_snapshot": preview, "execution_payload": order_result, "execution_steps": order_result.get("steps") or []},
        )
    if order_result.get("action") in {"reverse", "close_opposite"}:
        return record_automation_signal(
            strategy,
            signal,
            "submitted",
            "虚拟盘反向信号已执行：先平仓再按新方向处理。",
            {"risk_snapshot": preview, "execution_payload": order_result, "execution_steps": order_result.get("steps") or []},
        )
    return record_automation_signal(
        strategy,
        signal,
        "submitted",
        "虚拟盘订单已提交。",
        {"risk_snapshot": preview, "execution_payload": order_result, "execution_steps": order_result.get("steps") or []},
    )


def run_automation_once(force: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for strategy in list_automation_strategies_safe(include_archived=False):
        try:
            result = evaluate_automation_strategy(strategy, force=force)
            if result:
                results.append(result)
        except Exception as exc:
            signal = {
                "action": "hold",
                "side": None,
                "pos_side": None,
                "price": None,
                "candle_ts": 0,
                "reason": f"策略运行异常：{exc}",
            }
            trigger_automation_circuit_breaker(str(exc), strategy_id=int(strategy.get("id") or 0))
            results.append(record_automation_signal(strategy, signal, "failed", str(exc), {"risk_snapshot": automation_risk_preview(strategy, signal)}))
    with automation_state_lock:
        automation_state["lastRunAt"] = now_ms()
        automation_state["warning"] = ""
    return results


def normalize_announcement_language(language: str = "zh-CN") -> str:
    value = (language or "zh-CN").strip()
    if value.lower() in {"zh-cn", "zh_hans", "zh"}:
        return "zh-CN"
    if value.lower() in {"en-us", "en"}:
        return "en-US"
    if value in ANNOUNCEMENT_LANGUAGES:
        return value
    raise HTTPException(status_code=400, detail="不支持的公告语言。")


def normalize_announcement_type_filter(ann_type: str = "") -> str:
    value = (ann_type or "").strip()
    if not value:
        return ""
    if not valid_announcement_type_value(value):
        raise HTTPException(status_code=400, detail="公告类型参数无效。")
    return value


def valid_announcement_type_value(value: str) -> bool:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    return 0 < len(value) <= 80 and all(char in allowed for char in value)


def normalize_announcement_page(page: int) -> int:
    if page < 1 or page > 500:
        raise HTTPException(status_code=400, detail="公告页码参数无效。")
    return page


def normalize_announcement_timestamp(value: Any) -> int:
    try:
        timestamp = int(str(value or "0"))
    except ValueError:
        return 0
    return timestamp if timestamp > 0 else 0


def normalize_announcement_types(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ann_type = str(row.get("annType") or "").strip()
        if not valid_announcement_type_value(ann_type):
            continue
        normalized.append(
            {
                "annType": ann_type,
                "annTypeDesc": str(row.get("annTypeDesc") or ann_type).strip() or ann_type,
            }
        )
    return normalized


def normalize_announcements(payload: dict[str, Any], ann_type: str, page: int) -> dict[str, Any]:
    details = payload.get("details") if isinstance(payload, dict) else []
    rows = details if isinstance(details, list) else []
    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_type = str(row.get("annType") or "").strip()
        if row_type and not valid_announcement_type_value(row_type):
            row_type = ""
        title = str(row.get("title") or "").strip()
        url = str(row.get("url") or "").strip()
        if not title or not url:
            continue
        normalized_rows.append(
            {
                "annType": row_type,
                "title": title,
                "url": url,
                "pTime": normalize_announcement_timestamp(row.get("pTime")),
                "businessPTime": normalize_announcement_timestamp(row.get("businessPTime")),
            }
        )

    try:
        total_page = int(str(payload.get("totalPage") or "1"))
    except ValueError:
        total_page = 1
    return {
        "annType": ann_type,
        "page": page,
        "totalPage": max(1, total_page),
        "data": normalized_rows,
    }


def announcement_cache_meta(payload: dict[str, Any], source: str, ts: int, warning: str = "") -> dict[str, Any]:
    result = deepcopy(payload)
    result["source"] = source
    result["ts"] = ts
    result["cacheAgeMs"] = max(0, now_ms() - ts)
    if warning:
        result["warning"] = warning
    return result


def announcements_cache_key(language: str, ann_type: str, page: int) -> str:
    return f"{language}:{ann_type or 'all'}:{page}"


def cached_announcement_types(language: str = "zh-CN", force: bool = False) -> dict[str, Any]:
    normalized_language = normalize_announcement_language(language)
    now = now_ms()
    with announcement_cache_lock:
        cached = announcement_types_cache.get(normalized_language)
        if cached and not force and now - int(cached.get("ts") or 0) <= ANNOUNCEMENT_TYPES_CACHE_SECONDS * 1000:
            return announcement_cache_meta(cached["payload"], "announcement-types-cache", int(cached["ts"]))

    try:
        payload = {"language": normalized_language, "data": normalize_announcement_types(client.get_announcement_types(normalized_language))}
        ts = now_ms()
        with announcement_cache_lock:
            announcement_types_cache[normalized_language] = {"payload": deepcopy(payload), "ts": ts}
        return announcement_cache_meta(payload, "okx-announcement-types", ts)
    except OkxError as exc:
        with announcement_cache_lock:
            cached = announcement_types_cache.get(normalized_language)
            if cached:
                return announcement_cache_meta(cached["payload"], "announcement-types-stale-cache", int(cached["ts"]), str(exc))
        fallback = {"language": normalized_language, "data": deepcopy(DEFAULT_ANNOUNCEMENT_TYPES)}
        return announcement_cache_meta(fallback, "announcement-types-default", now_ms(), str(exc))


def cached_announcements(ann_type: str = "", page: int = 1, language: str = "zh-CN", force: bool = False) -> dict[str, Any]:
    normalized_language = normalize_announcement_language(language)
    normalized_type = normalize_announcement_type_filter(ann_type)
    normalized_page = normalize_announcement_page(page)
    cache_key = announcements_cache_key(normalized_language, normalized_type, normalized_page)
    now = now_ms()
    with announcement_cache_lock:
        cached = announcements_cache.get(cache_key)
        if cached and not force and now - int(cached.get("ts") or 0) <= ANNOUNCEMENTS_CACHE_SECONDS * 1000:
            return announcement_cache_meta(cached["payload"], "announcements-cache", int(cached["ts"]))

    try:
        payload = normalize_announcements(
            client.get_announcements(normalized_type, normalized_page, normalized_language),
            normalized_type,
            normalized_page,
        )
        payload["language"] = normalized_language
        ts = now_ms()
        with announcement_cache_lock:
            announcements_cache[cache_key] = {"payload": deepcopy(payload), "ts": ts}
        return announcement_cache_meta(payload, "okx-announcements", ts)
    except OkxError as exc:
        with announcement_cache_lock:
            cached = announcements_cache.get(cache_key)
            if cached:
                return announcement_cache_meta(cached["payload"], "announcements-stale-cache", int(cached["ts"]), str(exc))
        return {
            "language": normalized_language,
            "annType": normalized_type,
            "page": normalized_page,
            "totalPage": 1,
            "data": [],
            "source": "okx-announcements-unavailable",
            "warning": str(exc),
            "ts": now_ms(),
            "cacheAgeMs": None,
        }


def automation_loop() -> None:
    with automation_state_lock:
        if automation_state.get("running"):
            return
        automation_state["running"] = True
        automation_state["startedAt"] = now_ms()
    while True:
        try:
            run_automation_once(force=False)
        except Exception as exc:
            with automation_state_lock:
                automation_state["warning"] = str(exc)
                automation_state["lastRunAt"] = now_ms()
        time.sleep(AUTOMATION_INTERVAL_SECONDS)


def save_ticker_snapshot(rows: list[dict[str, Any]], ts: int) -> None:
    database.set_app_setting(
        "ticker_snapshot",
        json.dumps({"ts": ts, "data": rows}, ensure_ascii=False, separators=(",", ":")),
        ts,
    )


def load_ticker_snapshot() -> dict[str, Any] | None:
    raw = database.get_app_setting("ticker_snapshot")
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        return None
    ts = int(payload.get("ts") or now_ms())
    return {
        "data": rows,
        "source": "database-cache",
        "ts": ts,
        "cacheAgeMs": max(0, now_ms() - ts),
    }


def ticker_refresh_backoff_ms(failure_count: int) -> int:
    exponent = max(0, min(int(failure_count) - 1, 4))
    return min(TICKER_REFRESH_BACKOFF_MAX_MS, TICKER_REFRESH_BACKOFF_BASE_MS * (2**exponent))


def ticker_refresh_metadata(now: int, cached_ts: int, refreshing: bool, failure_count: int, next_retry_at: int) -> dict[str, Any]:
    cache_age_ms = max(0, now - cached_ts) if cached_ts else None
    if not cached_ts:
        state = "initializing" if refreshing else "unavailable"
        label = "行情列表正在获取完整快照" if refreshing else "行情列表暂不可用，正在等待完整行情快照"
    elif refreshing:
        state = "refreshing"
        label = "行情列表正在后台刷新，当前保留最近完整快照"
    elif next_retry_at > now:
        state = "backing_off"
        label = "行情列表暂沿用最近完整快照，稍后自动重试"
    elif cache_age_ms is not None and cache_age_ms <= int(settings.ticker_cache_seconds * 1000):
        state = "fresh"
        label = "行情列表已更新"
    else:
        state = "stale"
        label = "行情列表暂沿用最近完整快照"
    return {
        "state": state,
        "label": label,
        "snapshotTs": cached_ts or None,
        "cacheAgeMs": cache_age_ms,
        "nextRetryAt": next_retry_at or None,
        "failureCount": max(0, int(failure_count)),
    }


def ticker_snapshot_response(rows: list[dict[str, Any]], cached_ts: int, now: int, refreshing: bool, failure_count: int, next_retry_at: int) -> dict[str, Any]:
    refresh = ticker_refresh_metadata(now, cached_ts, refreshing, failure_count, next_retry_at)
    state = str(refresh["state"])
    source = "okx-cache" if state == "fresh" else "okx-stale-cache" if rows else "okx-unavailable"
    return {
        "data": rows,
        "source": source,
        "ts": cached_ts or now,
        "cacheAgeMs": refresh["cacheAgeMs"],
        "refresh": refresh,
        # Retain the field for older clients, but never leak an upstream transport exception
        # while a validated complete snapshot is available.
        "warning": "" if rows else str(refresh["label"]),
    }


def ticker_cache_values() -> tuple[list[dict[str, Any]], int, bool, int, int]:
    with ticker_cache_condition:
        return (
            list(ticker_cache.get("data") or []),
            int(ticker_cache.get("ts") or 0),
            bool(ticker_cache.get("refreshing")),
            int(ticker_cache.get("failureCount") or 0),
            int(ticker_cache.get("nextRetryAt") or 0),
        )


def record_ticker_refresh_failure(exc: Exception) -> None:
    now = now_ms()
    with ticker_cache_condition:
        failures = min(8, int(ticker_cache.get("failureCount") or 0) + 1)
        ticker_cache["failureCount"] = failures
        ticker_cache["nextRetryAt"] = now + ticker_refresh_backoff_ms(failures)
        # Raw transport detail belongs in server logs, not in user-facing API payloads.
        ticker_cache["warning"] = ""
        ticker_cache_condition.notify_all()
    logger.warning("OKX bulk ticker refresh failed; retaining the last complete snapshot: %s", exc)


def refresh_ticker_cache_sync() -> dict:
    rows = client.get_tickers()
    now = now_ms()
    save_ticker_snapshot(rows, now)
    with ticker_cache_condition:
        ticker_cache["data"] = rows
        ticker_cache["ts"] = now
        ticker_cache["warning"] = ""
        ticker_cache["failureCount"] = 0
        ticker_cache["nextRetryAt"] = 0
        ticker_cache_condition.notify_all()
    return ticker_snapshot_response(rows, now, now, False, 0, 0)


def refresh_ticker_cache_background() -> None:
    try:
        refresh_ticker_cache_sync()
    except OkxError as exc:
        record_ticker_refresh_failure(exc)
    finally:
        with ticker_cache_condition:
            ticker_cache["refreshing"] = False
            ticker_cache_condition.notify_all()


def start_ticker_refresh(now: int | None = None) -> bool:
    refresh_now = now if now is not None else now_ms()
    with ticker_cache_condition:
        if ticker_cache.get("refreshing") or int(ticker_cache.get("nextRetryAt") or 0) > refresh_now:
            return False
        ticker_cache["refreshing"] = True
    Thread(target=refresh_ticker_cache_background, daemon=True).start()
    return True


def cached_tickers(force: bool = False) -> dict:
    now = now_ms()
    cached_rows, cached_ts, refreshing, _failures, _next_retry_at = ticker_cache_values()
    if not cached_rows:
        stored = load_ticker_snapshot()
        if stored:
            with ticker_cache_condition:
                if not ticker_cache.get("data"):
                    ticker_cache["data"] = stored["data"]
                    ticker_cache["ts"] = stored["ts"]
            cached_rows, cached_ts, refreshing, _failures, _next_retry_at = ticker_cache_values()

    if cached_rows and cached_ts:
        age_ms = max(0, now - cached_ts)
        if (force or age_ms > int(settings.ticker_cache_seconds * 1000)) and not refreshing and _next_retry_at <= now:
            start_ticker_refresh(now)
        cached_rows, cached_ts, refreshing, failures, next_retry_at = ticker_cache_values()
        return ticker_snapshot_response(cached_rows, cached_ts, now, refreshing, failures, next_retry_at)

    start_ticker_refresh(now)
    wait_until = now_ms() + min(2500, max(300, int(settings.timeout_seconds * 1000)))
    with ticker_cache_condition:
        while ticker_cache.get("refreshing") and now_ms() < wait_until:
            ticker_cache_condition.wait(timeout=max(0.05, (wait_until - now_ms()) / 1000))
            cached_rows = list(ticker_cache.get("data") or [])
            cached_ts = int(ticker_cache.get("ts") or 0)
            if cached_rows and cached_ts:
                break
    cached_rows, cached_ts, refreshing, failures, next_retry_at = ticker_cache_values()
    return ticker_snapshot_response(cached_rows, cached_ts, now_ms(), refreshing, failures, next_retry_at)


order_book_cache_condition = Condition(RLock())
order_book_cache: dict[str, dict[str, Any]] = {}


def normalize_public_order_book(inst_id: str, raw: dict[str, Any] | None, received_at: int) -> dict[str, Any]:
    raw = raw or {}
    source_ts_value = safe_decimal(raw.get("ts"))
    source_ts = int(source_ts_value) if source_ts_value is not None and source_ts_value.is_finite() and source_ts_value > 0 else 0

    def levels(side: str, reverse: bool) -> list[dict[str, str]]:
        parsed: list[tuple[Decimal, Decimal]] = []
        seen: set[Decimal] = set()
        for row in raw.get(side) if isinstance(raw.get(side), list) else []:
            if not isinstance(row, list) or len(row) < 2:
                continue
            price, size = safe_decimal(row[0]), safe_decimal(row[1])
            if price is None or size is None or not price.is_finite() or not size.is_finite() or price <= 0 or size <= 0 or price in seen:
                continue
            seen.add(price)
            parsed.append((price, size))
        parsed.sort(key=lambda item: item[0], reverse=reverse)
        cumulative = Decimal("0")
        result: list[dict[str, str]] = []
        for price, size in parsed[:10]:
            cumulative += size
            result.append({"price": format(price, "f"), "size": format(size, "f"), "cumulative": format(cumulative, "f")})
        return result

    asks = levels("asks", False)
    bids = levels("bids", True)
    spread = None
    warning = ""
    if asks and bids:
        ask = Decimal(asks[0]["price"])
        bid = Decimal(bids[0]["price"])
        if ask > bid:
            difference = ask - bid
            spread = {"absolute": format(difference, "f"), "percent": format(difference / bid * Decimal("100"), ".4f")}
        else:
            warning = "买卖盘口价格交叉，价差暂不可用。"
    elif asks or bids:
        warning = "盘口仅有单侧报价，价差暂不可用。"
    return {"instId": inst_id, "asks": asks, "bids": bids, "spread": spread, "ts": source_ts, "receivedAt": received_at, "warning": warning}


def order_book_response(inst_id: str, entry: dict[str, Any], now: int) -> dict[str, Any]:
    snapshot = entry.get("snapshot")
    age = max(0, now - int(snapshot.get("ts") or 0)) if snapshot else None
    usable = snapshot is not None and age is not None and age <= ORDER_BOOK_MAX_AGE_MS
    data = snapshot if usable else None
    refreshing = bool(entry.get("refreshing"))
    retrying = int(entry.get("nextRetryAt") or 0) > now
    if data and not data["asks"] and not data["bids"]:
        state, message = "empty", "当前盘口暂无可用档位。"
    elif data and refreshing:
        state, message = "updating", "盘口更新中，当前显示上次快照。"
    elif data and retrying:
        state, message = "cached", "盘口更新失败，当前显示最近缓存；稍后自动重试。"
    elif data and age is not None and age <= ORDER_BOOK_CACHE_MS:
        state, message = "fresh", "盘口快照已更新。"
    elif data:
        state, message = "cached", "盘口显示最近缓存，正在等待更新。"
    elif refreshing:
        state, message = "loading", "正在读取当前合约盘口。"
    else:
        state, message = "unavailable", "盘口暂不可用，请稍后重试。"
    return {"instId": inst_id, "data": data, "state": state, "message": message, "cacheAgeMs": age if usable else None, "ts": data["ts"] if data else None}


def cached_order_book(inst_id: str) -> dict[str, Any]:
    now = now_ms()
    with order_book_cache_condition:
        entry = order_book_cache.setdefault(inst_id, {"snapshot": None, "refreshing": False, "nextRetryAt": 0})
        snapshot = entry.get("snapshot")
        if snapshot and now - int(snapshot.get("receivedAt") or 0) <= ORDER_BOOK_CACHE_MS:
            return order_book_response(inst_id, entry, now)
        if entry["refreshing"] or int(entry["nextRetryAt"]) > now:
            return order_book_response(inst_id, entry, now)
        entry["refreshing"] = True

    try:
        raw = client.get_order_book(inst_id, 10)
        received_at = now_ms()
        normalized = normalize_public_order_book(inst_id, raw, received_at)
        if not normalized["ts"] or received_at - normalized["ts"] > ORDER_BOOK_MAX_AGE_MS:
            raise OkxError("Order book source snapshot is missing or expired")
        with order_book_cache_condition:
            entry["snapshot"] = normalized
            entry["nextRetryAt"] = 0
    except (OkxError, ValueError, TypeError) as exc:
        logger.warning("Public order-book refresh failed for %s: %s", inst_id, exc)
        with order_book_cache_condition:
            entry["nextRetryAt"] = now_ms() + ORDER_BOOK_RETRY_MS
    finally:
        with order_book_cache_condition:
            entry["refreshing"] = False
            order_book_cache_condition.notify_all()
    return order_book_response(inst_id, entry, now_ms())


def normalize_platform_24_volume(raw: dict[str, Any] | None, received_at: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Platform volume response is missing")
    volume = safe_decimal(raw.get("volUsd"))
    timestamp = safe_decimal(raw.get("ts"))
    if volume is None or not volume.is_finite() or volume <= 0:
        raise ValueError("Platform USD volume is invalid")
    if timestamp is None or not timestamp.is_finite() or timestamp != timestamp.to_integral_value():
        raise ValueError("Platform volume timestamp is invalid")
    source_ts = int(timestamp)
    if source_ts > received_at + 5 * 60_000 or received_at - source_ts > PLATFORM_VOLUME_MAX_AGE_MS:
        raise ValueError("Platform volume timestamp is outside the usable window")
    return {"volUsd": str(volume), "ts": source_ts}


def platform_24_volume_response(now: int) -> dict[str, Any]:
    with platform_volume_cache_lock:
        snapshot = platform_volume_cache.get("snapshot")
        received_at = int(platform_volume_cache.get("receivedAt") or 0)
        refreshing = bool(platform_volume_cache.get("refreshing"))
        retrying = int(platform_volume_cache.get("nextRetryAt") or 0) > now
    source_age = max(0, now - int(snapshot["ts"])) if snapshot else None
    usable = snapshot is not None and source_age is not None and source_age <= PLATFORM_VOLUME_MAX_AGE_MS
    if usable and not refreshing and not retrying and now - received_at <= PLATFORM_VOLUME_CACHE_MS:
        state, message = "fresh", "OKX 平台成交额已更新。"
    elif usable:
        state, message = "cached", "OKX 平台成交额正在更新或暂时失败，已显示最近快照。"
    elif refreshing:
        state, message = "loading", "正在读取 OKX 平台成交额。"
    else:
        state, message = "unavailable", "OKX 平台成交额暂不可用，请稍后重试。"
    return {
        "data": snapshot if usable else None,
        "state": state,
        "message": message,
        "source": "okx-platform-24-volume" if state == "fresh" else "okx-cache" if usable else "okx-unavailable",
        "cacheAgeMs": source_age if usable else None,
        "ts": int(snapshot["ts"]) if usable else None,
    }


def cached_platform_24_volume() -> dict[str, Any]:
    now = now_ms()
    with platform_volume_cache_lock:
        snapshot = platform_volume_cache.get("snapshot")
        received_at = int(platform_volume_cache.get("receivedAt") or 0)
        if snapshot and now - received_at <= PLATFORM_VOLUME_CACHE_MS and now - int(snapshot["ts"]) <= PLATFORM_VOLUME_MAX_AGE_MS:
            return platform_24_volume_response(now)
        if platform_volume_cache["refreshing"] or int(platform_volume_cache["nextRetryAt"]) > now:
            return platform_24_volume_response(now)
        platform_volume_cache["refreshing"] = True
    try:
        normalized = normalize_platform_24_volume(client.get_platform_24_volume(), now_ms())
        with platform_volume_cache_lock:
            platform_volume_cache["snapshot"] = normalized
            platform_volume_cache["receivedAt"] = now_ms()
            platform_volume_cache["nextRetryAt"] = 0
    except (OkxError, ValueError, TypeError) as exc:
        logger.warning("OKX platform 24-hour volume refresh failed: %s", exc)
        with platform_volume_cache_lock:
            platform_volume_cache["nextRetryAt"] = now_ms() + PLATFORM_VOLUME_RETRY_MS
    finally:
        with platform_volume_cache_lock:
            platform_volume_cache["refreshing"] = False
    return platform_24_volume_response(now_ms())


def warm_ticker_cache() -> None:
    start_ticker_refresh()


def account_unconfigured_response(environment: str) -> dict:
    return {
        "configured": False,
        "environment": environment,
        "summary": None,
        "positions": [],
        "message": f"{environment_label(environment)} API Key 未配置。",
        "source": "not-configured",
        "ts": now_ms(),
        "cacheAgeMs": 0,
        "refresh": {
            "state": "not_configured",
            "label": f"{environment_label(environment)} API Key 未配置。",
            "snapshotTs": None,
            "cacheAgeMs": 0,
            "nextRetryAt": None,
            "failureCount": 0,
        },
    }


def account_response_from_payload(
    environment: str,
    balance: dict[str, Any],
    positions: dict[str, Any],
    ts: int,
    source: str,
    warning: str = "",
) -> dict:
    account_rows = balance.get("data", [])
    summary = account_rows[0] if account_rows else {}
    position_rows = positions.get("data", [])
    response = {
        "configured": True,
        "environment": environment,
        "summary": summary,
        "positions": position_rows,
        "source": source,
        "ts": ts,
        "cacheAgeMs": max(0, now_ms() - ts),
    }
    if warning:
        response["warning"] = warning
    return response


def load_account_from_database(environment: str) -> dict | None:
    if not hasattr(database, "latest_account_snapshot") or not hasattr(database, "latest_position_snapshot_payload"):
        return None
    try:
        account_snapshot = database.latest_account_snapshot(environment)
    except Exception:
        return None
    if not account_snapshot:
        return None
    try:
        balance = json.loads(str(account_snapshot["details_json"]))
    except (TypeError, json.JSONDecodeError):
        return None

    try:
        position_snapshot = database.latest_position_snapshot_payload(environment)
    except Exception:
        position_snapshot = None
    positions = {"data": []}
    if position_snapshot:
        try:
            positions = json.loads(str(position_snapshot["raw_json"]))
        except (TypeError, json.JSONDecodeError):
            positions = {"data": []}

    return account_response_from_payload(
        environment=environment,
        balance=balance,
        positions=positions,
        ts=int(account_snapshot["ts"]),
        source="database-cache",
    )


def reset_account_cache() -> None:
    with account_cache_condition:
        account_cache.clear()
        account_cache.update(
            {
                "environment": "",
                "payload": None,
                "ts": 0,
                "refreshing": False,
                "failureCount": 0,
                "nextRetryAt": 0,
            }
        )
        account_cache_condition.notify_all()


def account_cache_values(environment: str) -> tuple[dict | None, int, bool, int, int]:
    with account_cache_condition:
        if account_cache.get("environment") != environment:
            return None, 0, False, 0, 0
        payload = account_cache.get("payload")
        return (
            dict(payload) if payload else None,
            int(account_cache.get("ts") or 0),
            bool(account_cache.get("refreshing")),
            int(account_cache.get("failureCount") or 0),
            int(account_cache.get("nextRetryAt") or 0),
        )


def account_refresh_backoff_ms(failure_count: int) -> int:
    exponent = max(0, min(int(failure_count) - 1, 4))
    return min(ACCOUNT_REFRESH_BACKOFF_MAX_MS, ACCOUNT_REFRESH_BACKOFF_BASE_MS * (2**exponent))


def account_refresh_metadata(now: int, cached_ts: int, refreshing: bool, failure_count: int, next_retry_at: int) -> dict[str, Any]:
    cache_age_ms = max(0, now - cached_ts) if cached_ts else None
    if not cached_ts:
        state = "initializing" if refreshing else "unavailable"
        label = "账户和持仓正在获取完整快照" if refreshing else "账户和持仓暂不可用，正在等待完整快照"
    elif refreshing:
        state = "refreshing"
        label = "账户和持仓正在后台刷新，当前保留最近完整快照"
    elif next_retry_at > now:
        state = "backing_off"
        label = "账户和持仓暂沿用最近完整快照，稍后自动重试"
    elif cache_age_ms is not None and cache_age_ms <= int(settings.account_cache_seconds * 1000):
        state = "fresh"
        label = "账户和持仓已更新"
    else:
        state = "stale"
        label = "账户和持仓暂沿用最近完整快照"
    return {
        "state": state,
        "label": label,
        "snapshotTs": cached_ts or None,
        "cacheAgeMs": cache_age_ms,
        "nextRetryAt": next_retry_at or None,
        "failureCount": max(0, int(failure_count)),
    }


def account_snapshot_response(environment: str, payload: dict, now: int, source: str = "") -> dict:
    cached_payload, cached_ts, refreshing, failures, next_retry_at = account_cache_values(environment)
    snapshot = cached_payload or dict(payload)
    snapshot_ts = cached_ts or int(snapshot.get("ts") or 0)
    refresh = account_refresh_metadata(now, snapshot_ts, refreshing, failures, next_retry_at)
    state = str(refresh["state"])
    result = dict(snapshot)
    if source:
        result["source"] = source
    elif str(snapshot.get("source") or "") == "database-cache":
        result["source"] = "database-cache"
    else:
        result["source"] = "okx-cache" if state == "fresh" else "okx-stale-cache"
    result["ts"] = snapshot_ts or now
    result["cacheAgeMs"] = refresh["cacheAgeMs"]
    result["refresh"] = refresh
    if state in {"refreshing", "backing_off", "stale"}:
        result["warning"] = str(refresh["label"])
    else:
        result.pop("warning", None)
    return result


def account_unavailable_response(environment: str, now: int, refreshing: bool, failure_count: int, next_retry_at: int) -> dict:
    refresh = account_refresh_metadata(now, 0, refreshing, failure_count, next_retry_at)
    message = str(refresh["label"])
    return {
        "configured": True,
        "environment": environment,
        "summary": None,
        "positions": [],
        "message": message,
        "warning": message,
        "source": "okx-unavailable",
        "ts": now,
        "cacheAgeMs": None,
        "refresh": refresh,
    }


def refresh_account_cache_sync(environment: str) -> dict:
    ts = now_ms()
    account_client = client_for_environment(environment)
    balance = account_client.get_balance()
    positions = account_client.get_positions()
    summary = balance.get("data", [{}])[0] if balance.get("data") else {}
    database.insert_account_snapshot(environment, ts, summary, json.dumps(balance, ensure_ascii=False))
    database.insert_position_snapshots(environment, ts, positions.get("data", []), json.dumps(positions, ensure_ascii=False))
    payload = account_response_from_payload(environment, balance, positions, ts, "okx")
    with account_cache_condition:
        account_cache["environment"] = environment
        account_cache["payload"] = payload
        account_cache["ts"] = ts
        account_cache["failureCount"] = 0
        account_cache["nextRetryAt"] = 0
        account_cache_condition.notify_all()
    return account_snapshot_response(environment, payload, ts, source="okx")


def refresh_account_cache_background(environment: str) -> None:
    try:
        refresh_account_cache_sync(environment)
    except (OkxError, ValueError) as exc:
        now = now_ms()
        with account_cache_condition:
            if account_cache.get("environment") == environment:
                failures = min(8, int(account_cache.get("failureCount") or 0) + 1)
                account_cache["failureCount"] = failures
                account_cache["nextRetryAt"] = now + account_refresh_backoff_ms(failures)
                account_cache_condition.notify_all()
        logger.warning("OKX account refresh failed; retaining the last complete snapshot: %s", exc)
    finally:
        with account_cache_condition:
            if account_cache.get("environment") == environment:
                account_cache["refreshing"] = False
            account_cache_condition.notify_all()


def start_account_refresh(environment: str, now: int | None = None) -> bool:
    refresh_now = now if now is not None else now_ms()
    with account_cache_condition:
        if account_cache.get("environment") not in {"", environment}:
            reset_account_cache()
        if account_cache.get("refreshing") or int(account_cache.get("nextRetryAt") or 0) > refresh_now:
            return False
        account_cache["environment"] = environment
        account_cache["refreshing"] = True
        account_cache_condition.notify_all()
    Thread(target=refresh_account_cache_background, args=(environment,), daemon=True).start()
    return True


def account_fallback_response(environment: str, _warning: str = "") -> dict | None:
    cached, _cached_ts, _refreshing, _failures, _next_retry_at = account_cache_values(environment)
    if cached:
        return account_snapshot_response(environment, cached, now_ms())
    stored = load_account_from_database(environment)
    if stored:
        with account_cache_condition:
            account_cache["payload"] = stored
            account_cache["ts"] = int(stored.get("ts") or 0)
            account_cache["environment"] = environment
            account_cache_condition.notify_all()
        return account_snapshot_response(environment, stored, now_ms())
    return None


def cached_account(force: bool = False) -> dict:
    environment = current_trading_environment()
    if not settings.has_credentials_for_environment(environment):
        return account_unconfigured_response(environment)

    now = now_ms()
    payload, cached_ts, refreshing, _failures, next_retry_at = account_cache_values(environment)
    if not payload:
        stored = load_account_from_database(environment)
        if stored:
            with account_cache_condition:
                if account_cache.get("environment") in {"", environment} and not account_cache.get("payload"):
                    account_cache["environment"] = environment
                    account_cache["payload"] = stored
                    account_cache["ts"] = int(stored.get("ts") or 0)
                    account_cache_condition.notify_all()
            payload, cached_ts, refreshing, _failures, next_retry_at = account_cache_values(environment)

    if payload and cached_ts:
        age_ms = max(0, now - cached_ts)
        refresh_required = force or age_ms > int(settings.account_cache_seconds * 1000)
        if refresh_required and not refreshing and next_retry_at <= now:
            start_account_refresh(environment, now)
        return account_snapshot_response(environment, payload, now)

    start_account_refresh(environment, now)
    wait_until = now_ms() + min(2500, max(300, int(settings.timeout_seconds * 1000)))
    with account_cache_condition:
        while account_cache.get("refreshing") and now_ms() < wait_until:
            account_cache_condition.wait(timeout=max(0.05, (wait_until - now_ms()) / 1000))
            payload = account_cache.get("payload")
            cached_ts = int(account_cache.get("ts") or 0)
            if payload and cached_ts:
                break
    payload, cached_ts, refreshing, failures, next_retry_at = account_cache_values(environment)
    if payload and cached_ts:
        return account_snapshot_response(environment, payload, now_ms())
    return account_unavailable_response(environment, now_ms(), refreshing, failures, next_retry_at)


@app.on_event("startup")
def startup() -> None:
    database.init()
    load_persisted_trading_environment()
    Thread(target=warm_ticker_cache, daemon=True).start()
    Thread(target=automation_loop, daemon=True).start()
    Thread(target=market_ai_sample_verification_loop, daemon=True).start()


@app.get("/api/health")
def health() -> dict:
    environment = current_trading_environment()
    return {
        "ok": True,
        "environment": environment,
        "hasCredentials": settings.has_credentials_for_environment(environment),
    }


@app.get("/api/settings/status")
def settings_status() -> dict:
    environment = current_trading_environment()
    return {
        "baseUrl": settings.base_url,
        "databasePath": settings.database_label,
        "tradingEnvironment": environment,
        "hasCredentials": settings.has_credentials_for_environment(environment),
        "simulatedTrading": environment == "simulated",
        "tradeEnabled": can_trade(environment),
        "liveTradingEnabled": settings.live_trading_enabled,
        "demoHasCredentials": settings.has_credentials_for_environment("simulated"),
        "liveHasCredentials": settings.has_credentials_for_environment("live"),
        "wsPublicUrl": settings.ws_public_url,
        "wsBusinessUrl": settings.ws_business_url,
        "realtime": realtime_capabilities(environment),
        "accountCacheSeconds": settings.account_cache_seconds,
        "accountStaleSeconds": settings.account_stale_seconds,
    }


@app.put("/api/settings/trading-environment")
def update_trading_environment(payload: TradingEnvironmentRequest) -> dict:
    environment = set_current_trading_environment(payload.environment)
    return settings_status()


@app.get("/api/llm/config")
def llm_config() -> dict:
    return {"data": sanitize_llm_config(stored_llm_config())}


@app.put("/api/llm/config")
def update_llm_config(payload: LlmConfigRequest) -> dict:
    config = normalize_llm_config(payload, stored_llm_config())
    database.set_app_setting(LLM_CONFIG_KEY, json.dumps(config, ensure_ascii=False, separators=(",", ":")), now_ms())
    return {"ok": True, "data": sanitize_llm_config(config)}


@app.post("/api/llm/test")
def test_llm_config() -> dict:
    config = stored_llm_config()
    if not config.get("baseUrl") or not config.get("model") or not config.get("apiKey"):
        raise HTTPException(status_code=400, detail="LLM 配置不完整，无法测试连接。")
    try:
        completion = llm_chat_completion(
            config,
            [
                {"role": "system", "content": "你只返回 JSON，不返回 Markdown。"},
                {
                    "role": "user",
                    "content": (
                        "请返回一个 JSON 对象用于测试连接："
                        "{\"summary\":\"连接正常\",\"recommendation\":\"observe\",\"confidence\":50,"
                        "\"reasons\":[\"配置测试\"],\"risks\":[],\"invalidation\":\"\",\"notes\":\"\"}"
                    ),
                },
            ],
            request_type="connection_test",
        )
        raw_text = str(completion["content"])
        parsed = extract_json_object(raw_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True, "data": attach_llm_completion_meta(normalize_llm_analysis(parsed, config, raw_text), completion)}


def normalize_llm_usage_log_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if normalized.get("ts") is not None:
        normalized["ts"] = coerce_int(normalized.get("ts"), 0, 0, 9_999_999_999_999)
    for key in [
        "id",
        "strategy_id",
        "signal_id",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cached_tokens",
        "reasoning_tokens",
        "cache_hit_tokens",
        "cache_miss_tokens",
        "duration_ms",
        "timeout_seconds",
    ]:
        if normalized.get(key) is not None:
            normalized[key] = coerce_int(normalized.get(key), 0, 0, 99_999_999_999)
    return normalized


def normalize_llm_usage_summary(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "calls": coerce_int(summary.get("calls"), 0, 0, 99_999_999),
        "promptTokens": coerce_int(summary.get("prompt_tokens"), 0, 0, 99_999_999_999),
        "completionTokens": coerce_int(summary.get("completion_tokens"), 0, 0, 99_999_999_999),
        "totalTokens": coerce_int(summary.get("total_tokens"), 0, 0, 99_999_999_999),
        "cachedTokens": coerce_int(summary.get("cached_tokens"), 0, 0, 99_999_999_999),
        "reasoningTokens": coerce_int(summary.get("reasoning_tokens"), 0, 0, 99_999_999_999),
        "cacheHitTokens": coerce_int(summary.get("cache_hit_tokens"), 0, 0, 99_999_999_999),
        "cacheMissTokens": coerce_int(summary.get("cache_miss_tokens"), 0, 0, 99_999_999_999),
        "failedCalls": coerce_int(summary.get("failed_calls"), 0, 0, 99_999_999),
        "avgDurationMs": coerce_int(summary.get("avg_duration_ms"), 0, 0, 99_999_999),
    }


@app.get("/api/llm/usage")
def llm_usage(
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    requestType: Annotated[str, Query(max_length=40)] = "",
    status: Annotated[str, Query(max_length=20)] = "",
    strategyId: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    rows = database.list_llm_usage_logs(
        limit=limit,
        offset=offset,
        request_type=requestType.strip(),
        status=status.strip(),
        strategy_id=strategyId,
    )
    total = database.count_llm_usage_logs(request_type=requestType.strip(), status=status.strip(), strategy_id=strategyId)
    page = (offset // limit) + 1
    page_count = max((total + limit - 1) // limit, 1)
    return {
        "data": [normalize_llm_usage_log_row(row) for row in rows],
        "summary": normalize_llm_usage_summary(database.llm_usage_summary()),
        "last24h": normalize_llm_usage_summary(database.llm_usage_summary(since_ts=now_ms() - 86_400_000)),
        "paging": {
            "limit": limit,
            "offset": offset,
            "hasMore": len(rows) == limit,
            "total": total,
            "page": page,
            "pageCount": page_count,
        },
    }


@app.post("/api/instruments/refresh")
def refresh_instruments() -> dict:
    try:
        instruments = client.get_instruments()
    except OkxError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    database.upsert_instruments(instruments, now_ms())
    return {"count": len(instruments)}


@app.get("/api/instruments")
def instruments(
    query: Annotated[str, Query(max_length=80)] = "",
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> dict:
    rows = database.list_instruments(query=query, limit=limit)
    if not rows:
        try:
            fresh = client.get_instruments()
            database.upsert_instruments(fresh, now_ms())
            rows = database.list_instruments(query=query, limit=limit)
        except OkxError:
            rows = []
    return {"data": rows}


@app.get("/api/watchlist")
def watchlist() -> dict:
    return {"data": database.watchlist()}


@app.put("/api/watchlist/{inst_id}")
def add_watchlist(inst_id: str) -> dict:
    database.set_watched(inst_id.upper(), True, now_ms())
    return {"ok": True}


@app.delete("/api/watchlist/{inst_id}")
def remove_watchlist(inst_id: str) -> dict:
    database.set_watched(inst_id.upper(), False, now_ms())
    return {"ok": True}


@app.get("/api/candles")
def candles(
    instId: str,
    bar: Annotated[str, Query()] = "1m",
    limit: Annotated[int, Query(ge=1, le=300)] = 200,
    force: Annotated[bool, Query()] = False,
) -> dict:
    if bar not in SUPPORTED_BARS:
        raise HTTPException(status_code=400, detail="Unsupported K-line interval")
    inst_id = instId.upper()
    if not force:
        cached = normalize_candle_batch(database.latest_candles(inst_id, bar, limit))
        if cached:
            snapshot_ts = now_ms()
            start_candle_refresh(inst_id, bar, limit)
            return {
                "data": cached,
                "source": "cache",
                "ts": snapshot_ts,
                "snapshot": chart_snapshot_metadata(inst_id, bar, cached, "cache", snapshot_ts=snapshot_ts),
            }
    try:
        rows = normalize_candle_batch(client.get_candles(inst_id, bar, limit))
        database.upsert_candles(inst_id, bar, rows)
    except OkxError as exc:
        cached = normalize_candle_batch(database.latest_candles(inst_id, bar, limit))
        if cached:
            snapshot_ts = now_ms()
            return {
                "data": cached,
                "source": "cache",
                "warning": str(exc),
                "ts": snapshot_ts,
                "snapshot": chart_snapshot_metadata(inst_id, bar, cached, "cache", warning=str(exc), snapshot_ts=snapshot_ts),
            }
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    snapshot_ts = now_ms()
    return {
        "data": rows,
        "source": "okx",
        "ts": snapshot_ts,
        "snapshot": chart_snapshot_metadata(inst_id, bar, rows, "okx", snapshot_ts=snapshot_ts),
    }


@app.get("/api/tickers")
def tickers(force: Annotated[bool, Query()] = False) -> dict:
    try:
        return cached_tickers(force=force)
    except OkxError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/market/overview/volume")
def market_overview_volume() -> dict:
    return cached_platform_24_volume()


@app.get("/api/market/order-book")
def market_order_book(instId: Annotated[str, Query(max_length=80)]) -> dict:
    inst_id = normalize_market_stats_inst_id(instId)
    matching = database.list_instruments(query=inst_id, limit=20)
    if not any(str(row.get("inst_id") or "").upper() == inst_id and str(row.get("inst_type") or "").upper() == "SWAP" for row in matching):
        raise HTTPException(status_code=404, detail="未找到可用的永续合约。")
    return cached_order_book(inst_id)


@app.get("/api/announcements/types")
def announcement_types(
    language: Annotated[str, Query(max_length=16)] = "zh-CN",
    force: Annotated[bool, Query()] = False,
) -> dict:
    return cached_announcement_types(language, force=force)


@app.get("/api/announcements")
def announcements(
    annType: Annotated[str, Query(max_length=80)] = "",
    page: Annotated[int, Query(ge=1, le=500)] = 1,
    language: Annotated[str, Query(max_length=16)] = "zh-CN",
    force: Annotated[bool, Query()] = False,
) -> dict:
    return cached_announcements(annType, page, language, force=force)


@app.get("/api/market/stats")
def market_stats(
    instId: Annotated[str, Query(min_length=1, max_length=64)],
    period: Annotated[str, Query(max_length=12)] = MARKET_STATS_DEFAULT_PERIOD,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    force: Annotated[bool, Query()] = False,
) -> dict:
    inst_id = normalize_market_stats_inst_id(instId)
    requested_period = period.strip() or MARKET_STATS_DEFAULT_PERIOD
    effective_period = normalize_market_stats_period(requested_period)
    return cached_market_stats(inst_id, requested_period, effective_period, limit, force=force)


@app.post("/api/market/ai-outlook")
def market_ai_outlook(payload: MarketAiOutlookRequest) -> dict:
    return cached_market_ai_outlook(payload)


@app.get("/api/market/ai-outlook/evaluations")
def market_ai_outlook_evaluations(
    instId: Annotated[str, Query(min_length=1, max_length=64)] = "BTC-USDT-SWAP",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    return market_ai_sample_history(normalize_market_ai_inst_id(instId), limit)


@app.get("/api/market/ai-outlook/evaluations/records")
def market_ai_outlook_evaluation_records(
    instId: Annotated[str, Query(max_length=64)] = "",
    status: Annotated[str, Query(max_length=32)] = "",
    kind: Annotated[str, Query(max_length=32)] = "",
    pricedOnly: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    normalized_inst_id = normalize_market_ai_inst_id(instId) if instId else ""
    if status not in {"", "pending", "hit", "miss", "flat", "not_scored", "insufficient_data"}:
        raise HTTPException(status_code=400, detail="核验状态筛选不受支持。")
    if kind not in {"", "main_direction", "price_plan_15m"}:
        raise HTTPException(status_code=400, detail="预测类型筛选不受支持。")
    rows, total = database.page_ai_outlook_samples(normalized_inst_id, status, kind, limit, offset, pricedOnly)
    return {
        "samples": [public_sample(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "generatedAt": now_ms(),
        "readOnly": True,
        "scope": "行情方向比较目标收盘价与预测基准价；目标 K 线可能在报告生成前已开始。未确认入场时交易收益率不适用；理论价差仅供价格对照，触价也不代表成交。",
    }


@app.get("/api/market/us-events")
def market_us_events(
    from_date: Annotated[str, Query(alias="from", max_length=10)],
    to_date: Annotated[str, Query(alias="to", max_length=10)],
    categories: Annotated[str, Query(max_length=160)] = "",
    states: Annotated[str, Query(max_length=120)] = "",
) -> dict:
    return market_us_events_view(from_date, to_date, categories, states)


@app.get("/api/market/us-events/{event_id}")
def market_us_event_detail(event_id: str) -> dict:
    event = database.get_market_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="美国事件不存在。")
    event["versions"] = database.list_market_event_versions(event_id)
    return event


@app.get("/api/market/radar")
def market_radar(
    settlement: Annotated[str, Query(max_length=16)] = "usdt",
    minVolume: Annotated[str, Query(max_length=40)] = "1000000",
    volatility: Annotated[str, Query(max_length=16)] = "all",
    risk: Annotated[str, Query(max_length=16)] = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = RADAR_DEFAULT_LIMIT,
    candidateLimit: Annotated[int, Query(ge=5, le=200)] = RADAR_CANDIDATE_LIMIT,
    bar: Annotated[str, Query(max_length=8)] = RADAR_DEFAULT_BAR,
    sortBy: Annotated[str, Query(max_length=24)] = RADAR_DEFAULT_SORT,
    explain: Annotated[bool, Query()] = False,
    force: Annotated[bool, Query()] = False,
) -> dict:
    request = normalize_radar_request(settlement, minVolume, volatility, risk, limit, candidateLimit, bar, sortBy, explain)
    return cached_radar_scan(request, force=force)


@app.get("/api/market/radar/analysis")
def market_radar_analysis(
    settlement: Annotated[str, Query(max_length=16)] = "usdt",
    minVolume: Annotated[str, Query(max_length=40)] = "1000000",
    volatility: Annotated[str, Query(max_length=16)] = "all",
    risk: Annotated[str, Query(max_length=16)] = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = RADAR_DEFAULT_LIMIT,
    candidateLimit: Annotated[int, Query(ge=5, le=200)] = RADAR_CANDIDATE_LIMIT,
    bar: Annotated[str, Query(max_length=8)] = RADAR_DEFAULT_BAR,
    sortBy: Annotated[str, Query(max_length=24)] = RADAR_DEFAULT_SORT,
    force: Annotated[bool, Query()] = False,
) -> dict:
    request = normalize_radar_request(settlement, minVolume, volatility, risk, limit, candidateLimit, bar, sortBy, False)
    radar_payload = cached_radar_scan(request, force=False)
    return cached_radar_market_analysis(request, radar_payload, force=force)


@app.get("/api/account")
def account(force: Annotated[bool, Query()] = False) -> dict:
    try:
        return cached_account(force=force)
    except (OkxError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/earn/offers")
def earn_offers(
    productId: Annotated[str, Query(max_length=80)] = "",
    protocolType: Annotated[str, Query(max_length=20)] = "",
    ccy: Annotated[str, Query(max_length=20)] = "",
    force: Annotated[bool, Query()] = False,
) -> dict:
    product_id = normalize_earn_token(productId, "项目ID")
    protocol_type = normalize_earn_protocol_type(protocolType)
    currency = normalize_earn_upper(ccy, "投资币种", max_length=20)
    return build_earn_offers(product_id, protocol_type, currency, force=force)


@app.get("/api/earn/orders/active")
def earn_active_orders(
    productId: Annotated[str, Query(max_length=80)] = "",
    protocolType: Annotated[str, Query(max_length=20)] = "",
    ccy: Annotated[str, Query(max_length=20)] = "",
    state: Annotated[str, Query(max_length=8)] = "",
    force: Annotated[bool, Query()] = False,
) -> dict:
    product_id = normalize_earn_token(productId, "项目ID")
    protocol_type = normalize_earn_protocol_type(protocolType)
    currency = normalize_earn_upper(ccy, "投资币种", max_length=20)
    order_state = normalize_earn_active_state(state)
    return build_earn_active_orders(product_id, protocol_type, currency, order_state, force=force)


@app.get("/api/earn/orders/history")
def earn_order_history(
    productId: Annotated[str, Query(max_length=80)] = "",
    protocolType: Annotated[str, Query(max_length=20)] = "",
    ccy: Annotated[str, Query(max_length=20)] = "",
    after: Annotated[str, Query(max_length=80)] = "",
    before: Annotated[str, Query(max_length=80)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    force: Annotated[bool, Query()] = False,
) -> dict:
    product_id = normalize_earn_token(productId, "项目ID")
    protocol_type = normalize_earn_protocol_type(protocolType)
    currency = normalize_earn_upper(ccy, "投资币种", max_length=20)
    after_id = normalize_earn_token(after, "分页 after", max_length=80)
    before_id = normalize_earn_token(before, "分页 before", max_length=80)
    return build_earn_order_history(product_id, protocol_type, currency, after_id, before_id, limit, force=force)


@app.get("/api/earn/eth")
def earn_eth(
    type: Annotated[str, Query(max_length=20)] = "",
    status: Annotated[str, Query(max_length=20)] = "",
    after: Annotated[str, Query(max_length=80)] = "",
    before: Annotated[str, Query(max_length=80)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    days: Annotated[int, Query(ge=1, le=365)] = EARN_APY_DEFAULT_DAYS,
    force: Annotated[bool, Query()] = False,
) -> dict:
    request_type = normalize_earn_staking_history_type(type)
    request_status = normalize_earn_staking_history_status(status)
    after_ts = normalize_earn_token(after, "分页 after", max_length=80)
    before_ts = normalize_earn_token(before, "分页 before", max_length=80)
    return build_earn_staking_overview("ETH", request_type, request_status, after_ts, before_ts, limit, normalize_earn_days(days), force=force)


@app.get("/api/earn/sol")
def earn_sol(
    type: Annotated[str, Query(max_length=20)] = "",
    status: Annotated[str, Query(max_length=20)] = "",
    after: Annotated[str, Query(max_length=80)] = "",
    before: Annotated[str, Query(max_length=80)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    days: Annotated[int, Query(ge=1, le=365)] = EARN_APY_DEFAULT_DAYS,
    force: Annotated[bool, Query()] = False,
) -> dict:
    request_type = normalize_earn_staking_history_type(type)
    request_status = normalize_earn_staking_history_status(status)
    after_ts = normalize_earn_token(after, "分页 after", max_length=80)
    before_ts = normalize_earn_token(before, "分页 before", max_length=80)
    return build_earn_staking_overview("SOL", request_type, request_status, after_ts, before_ts, limit, normalize_earn_days(days), force=force)


@app.get("/api/automation/status")
def automation_status() -> dict:
    return automation_status_payload()


@app.get("/api/automation/strategies")
def automation_strategies(includeArchived: Annotated[bool, Query()] = False) -> dict:
    return {"data": [strategy_response(item) for item in list_automation_strategies_safe(include_archived=includeArchived)]}


@app.post("/api/automation/pause")
def pause_automation(payload: AutomationPauseRequest) -> dict:
    state = automation_global_state()
    now = now_ms()
    updated = persist_automation_global_state(
        {
            **state,
            "globalPaused": True,
            "pauseReason": payload.reason.strip() or "自动交易已暂停。",
            "pauseStartedAt": state.get("pauseStartedAt") or now,
            "pausedBy": "manual",
            "updatedAt": now,
        }
    )
    create_automation_alert(
        "warning",
        "global_pause",
        updated["pauseReason"],
        raw_payload={"state": updated, "action": "pause"},
    )
    return {"ok": True, "data": updated}


@app.post("/api/automation/resume")
def resume_automation() -> dict:
    state = automation_global_state()
    now = now_ms()
    updated = persist_automation_global_state(
        {
            **state,
            "globalPaused": False,
            "pauseReason": "",
            "pauseStartedAt": 0,
            "pausedBy": "",
            "circuitBreakerActive": False,
            "circuitReason": "",
            "circuitTriggeredAt": 0,
            "resumedAt": now,
            "updatedAt": now,
        }
    )
    if hasattr(database, "acknowledge_automation_alert"):
        for alert in list_automation_alerts_safe(active_only=True, source="global_pause", limit=200):
            database.acknowledge_automation_alert(int(alert["id"]), now)
        for alert in list_automation_alerts_safe(active_only=True, source="circuit_breaker", limit=200):
            database.acknowledge_automation_alert(int(alert["id"]), now)
    return {"ok": True, "data": updated}


@app.post("/api/automation/strategies")
def create_automation_strategy(payload: AutomationStrategyRequest) -> dict:
    strategy = normalize_automation_strategy(payload)
    ensure_strategy_enable_preconditions(strategy)
    row = database.create_automation_strategy(strategy)
    data = strategy_response(row)
    broadcast_realtime_event(
        {"type": "automation.status", "topic": "automation.status", "source": "automation", "data": data, "refreshRequired": True},
        topic="automation.status",
    )
    return {"ok": True, "data": data}


@app.put("/api/automation/strategies/{strategy_id}")
def update_automation_strategy(strategy_id: int, payload: AutomationStrategyRequest) -> dict:
    existing = database.get_automation_strategy(strategy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="策略不存在。")
    strategy = normalize_automation_strategy(payload, existing)
    ensure_strategy_enable_preconditions(strategy, strategy_id)
    row = database.update_automation_strategy(strategy_id, strategy)
    if not row:
        raise HTTPException(status_code=404, detail="策略不存在。")
    data = strategy_response(row)
    broadcast_realtime_event(
        {"type": "automation.status", "topic": "automation.status", "source": "automation", "data": data, "refreshRequired": True},
        topic="automation.status",
    )
    return {"ok": True, "data": data}


@app.post("/api/automation/strategies/{strategy_id}/toggle")
def toggle_automation_strategy(strategy_id: int, payload: AutomationToggleRequest) -> dict:
    existing = database.get_automation_strategy(strategy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="策略不存在。")
    if bool(existing.get("archived")) and payload.enabled:
        raise HTTPException(status_code=400, detail="已归档策略请先恢复后再启动。")
    updated = dict(existing)
    updated["enabled"] = payload.enabled
    updated["updated_at"] = now_ms()
    ensure_strategy_enable_preconditions(updated, strategy_id)
    row = database.update_automation_strategy(strategy_id, updated)
    if not row:
        raise HTTPException(status_code=404, detail="策略不存在。")
    data = strategy_response(row)
    broadcast_realtime_event(
        {"type": "automation.status", "topic": "automation.status", "source": "automation", "data": data, "refreshRequired": True},
        topic="automation.status",
    )
    return {"ok": True, "data": data}


@app.post("/api/automation/strategies/{strategy_id}/archive")
def archive_automation_strategy(strategy_id: int, payload: AutomationArchiveRequest) -> dict:
    existing = database.get_automation_strategy(strategy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="策略不存在。")
    updated = dict(existing)
    updated["enabled"] = False
    updated["archived"] = True
    updated["archived_at"] = now_ms()
    updated["archived_reason"] = payload.reason.strip()
    updated["updated_at"] = now_ms()
    row = database.update_automation_strategy(strategy_id, updated)
    if not row:
        raise HTTPException(status_code=404, detail="策略不存在。")
    data = strategy_response(row)
    broadcast_realtime_event(
        {"type": "automation.status", "topic": "automation.status", "source": "automation", "data": data, "refreshRequired": True},
        topic="automation.status",
    )
    return {"ok": True, "data": data}


@app.post("/api/automation/strategies/{strategy_id}/restore")
def restore_automation_strategy(strategy_id: int) -> dict:
    existing = database.get_automation_strategy(strategy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="策略不存在。")
    updated = dict(existing)
    updated["enabled"] = False
    updated["archived"] = False
    updated["archived_at"] = None
    updated["archived_reason"] = ""
    updated["updated_at"] = now_ms()
    row = database.update_automation_strategy(strategy_id, updated)
    if not row:
        raise HTTPException(status_code=404, detail="策略不存在。")
    data = strategy_response(row)
    broadcast_realtime_event(
        {"type": "automation.status", "topic": "automation.status", "source": "automation", "data": data, "refreshRequired": True},
        topic="automation.status",
    )
    return {"ok": True, "data": data}


@app.post("/api/automation/strategies/{strategy_id}/run")
def run_automation_strategy(strategy_id: int) -> dict:
    strategy = database.get_automation_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在。")
    if bool(strategy.get("archived")):
        raise HTTPException(status_code=400, detail="已归档策略请先恢复后再运行。")
    result = evaluate_automation_strategy(strategy, force=True)
    return {"ok": True, "data": result}


@app.post("/api/automation/preview")
def preview_automation_strategy(payload: AutomationPreviewRequest) -> dict:
    strategy = normalized_strategy_from_preview_payload(payload)
    if strategy["template"] == "ma_cross":
        signal = ma_cross_signal(strategy)
    elif strategy["template"] == "llm_direct":
        candles = closed_strategy_candles(str(strategy["inst_id"]), str(strategy["bar"]), min(30, AUTOMATION_LLM_LOOKBACK_CANDLES))
        signal = {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": str(candles[-1].get("close") or "") if candles else None,
            "candle_ts": int(candles[-1].get("ts") or 0) if candles else 0,
            "reason": "LLM 直接判断会在策略运行时调用；预览不请求模型。",
        }
    else:
        signal = {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": None,
            "candle_ts": 0,
            "reason": "策略模板不受支持。",
        }
    preview = automation_risk_preview(strategy, signal)
    preview["signal"] = signal
    return {"ok": True, "data": preview}


@app.post("/api/automation/backtest")
def backtest_automation_strategy(payload: AutomationBacktestRequest) -> dict:
    strategy = normalized_strategy_from_preview_payload(payload)
    if strategy["template"] != "ma_cross":
        raise HTTPException(status_code=400, detail="当前仅支持 MA 均线交叉策略回测；LLM 直接判断暂不做历史回放。")
    initial_capital = decimal_value(payload.initialCapital, "初始资金")
    if initial_capital <= 0:
        raise HTTPException(status_code=400, detail="初始资金必须大于 0。")
    try:
        result = run_ma_cross_backtest(strategy, payload.limit, initial_capital)
    except (OkxError, ValueError, InvalidOperation) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True, "data": result}


@app.post("/api/automation/run")
def run_automation() -> dict:
    return {"ok": True, "data": run_automation_once(force=True)}


@app.get("/api/automation/alerts")
def automation_alerts(
    activeOnly: Annotated[bool, Query()] = True,
    severity: Annotated[str, Query(max_length=32)] = "",
    source: Annotated[str, Query(max_length=48)] = "",
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> dict:
    return {
        "data": [dict(row) for row in list_automation_alerts_safe(active_only=activeOnly, severity=severity, source=source, limit=limit)]
    }


@app.post("/api/automation/alerts/{alert_id}/ack")
def acknowledge_automation_alert(alert_id: int) -> dict:
    existing = next((item for item in list_automation_alerts_safe(active_only=False, limit=1000) if int(item.get("id") or 0) == alert_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="告警不存在。")
    now = now_ms()
    database.acknowledge_automation_alert(alert_id, now)
    row = dict(existing)
    row["acknowledged_at"] = now
    return {"ok": True, "data": row}


def normalize_automation_signal_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if normalized.get("decision") != "failed":
        return normalized
    try:
        raw_payload = json.loads(str(normalized.get("raw_json") or "{}"))
    except json.JSONDecodeError:
        raw_payload = {}
    if isinstance(raw_payload, dict) and raw_payload.get("llm_error"):
        normalized["decision"] = "llm_failed"
    return normalized


def signal_raw_payload(signal: dict[str, Any]) -> dict[str, Any] | None:
    raw_json = signal.get("raw_json")
    if not raw_json:
        return None
    try:
        parsed = json.loads(str(raw_json))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


@app.get("/api/automation/signals")
def automation_signals(
    strategyId: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> dict:
    rows = database.list_automation_signals(strategy_id=strategyId, limit=limit)
    return {"data": [normalize_automation_signal_row(row) for row in rows]}


@app.get("/api/automation/signals/{signal_id}")
def automation_signal_detail(signal_id: int) -> dict:
    row = database.get_automation_signal(signal_id)
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"data": enrich_automation_signal_detail(row)}


def order_source(environment: str) -> str:
    return "okx-sim" if environment == "simulated" else "okx-live"


def order_cache_key(environment: str, inst_id: str) -> tuple[str, str]:
    return (environment, inst_id.upper())


def refresh_order_cache_sync(environment: str, inst_id: str) -> dict[str, Any]:
    response = client_for_environment(environment).get_pending_orders(inst_id or None)
    pending = response.get("data", [])
    now = now_ms()
    key = order_cache_key(environment, inst_id)
    with order_cache_lock:
        order_cache[key] = {
            "pending": pending,
            "ts": now,
            "warning": "",
            "refreshing": False,
        }
    return {
        "pending": pending,
        "source": order_source(environment),
        "warning": "",
        "ts": now,
        "cacheAgeMs": 0,
    }


def refresh_order_cache_background(environment: str, inst_id: str) -> None:
    key = order_cache_key(environment, inst_id)
    try:
        refresh_order_cache_sync(environment, inst_id)
    except OkxError as exc:
        with order_cache_lock:
            current = dict(order_cache.get(key) or {})
            current["pending"] = current.get("pending") or []
            current["warning"] = str(exc)
            current["refreshing"] = False
            current["ts"] = int(current.get("ts") or now_ms())
            order_cache[key] = current
    finally:
        with order_cache_lock:
            current = dict(order_cache.get(key) or {})
            current["refreshing"] = False
            order_cache[key] = current


def start_order_cache_refresh(environment: str, inst_id: str) -> None:
    key = order_cache_key(environment, inst_id)
    with order_cache_lock:
        current = dict(order_cache.get(key) or {})
        if current.get("refreshing"):
            return
        current["refreshing"] = True
        order_cache[key] = current
    Thread(target=refresh_order_cache_background, args=(environment, inst_id), daemon=True).start()


def cached_pending_orders(environment: str, inst_id: str, async_on_miss: bool = False) -> dict[str, Any]:
    key = order_cache_key(environment, inst_id)
    now = now_ms()
    with order_cache_lock:
        cached = dict(order_cache.get(key) or {})
        pending = cached.get("pending")
        cached_ts = int(cached.get("ts") or 0)
        warning = str(cached.get("warning") or "")
        refreshing = bool(cached.get("refreshing"))
        age_ms = now - cached_ts if cached_ts else None

    if pending is not None and age_ms is not None and age_ms <= ORDER_CACHE_MS:
        suffix = "cache" if not warning else "unavailable"
        return {
            "pending": pending,
            "source": f"{order_source(environment)}-{suffix}",
            "warning": warning,
            "ts": cached_ts,
            "cacheAgeMs": age_ms,
        }

    if pending is not None and age_ms is not None and age_ms <= ORDER_STALE_MS:
        if not refreshing:
            start_order_cache_refresh(environment, inst_id)
        return {
            "pending": pending,
            "source": f"{order_source(environment)}-stale-cache",
            "warning": warning,
            "ts": cached_ts,
            "cacheAgeMs": age_ms,
        }

    if async_on_miss:
        if not refreshing:
            start_order_cache_refresh(environment, inst_id)
        return {
            "pending": pending or [],
            "source": "local-refreshing",
            "warning": warning,
            "ts": now,
            "cacheAgeMs": None,
        }

    try:
        return refresh_order_cache_sync(environment, inst_id)
    except OkxError as exc:
        if pending is not None:
            return {
                "pending": pending,
                "source": f"{order_source(environment)}-stale-cache",
                "warning": str(exc),
                "ts": cached_ts or now,
                "cacheAgeMs": age_ms,
            }
        raise


def invalidate_order_cache(environment: str, inst_id: str) -> None:
    key = order_cache_key(environment, inst_id)
    with order_cache_lock:
        order_cache.pop(key, None)
        order_cache.pop(order_cache_key(environment, ""), None)


def refresh_candles_background(inst_id: str, bar: str, limit: int) -> None:
    key = (inst_id, bar)
    try:
        rows = client.get_candles(inst_id, bar, limit)
        database.upsert_candles(inst_id, bar, rows)
    except OkxError:
        pass
    finally:
        with candle_refresh_lock:
            candle_refreshing.discard(key)


def start_candle_refresh(inst_id: str, bar: str, limit: int) -> None:
    key = (inst_id, bar)
    with candle_refresh_lock:
        if key in candle_refreshing:
            return
        candle_refreshing.add(key)
    Thread(target=refresh_candles_background, args=(inst_id, bar, limit), daemon=True).start()


def orders_for_environment(
    environment: str,
    instId: str = "",
    limit: int = 100,
    offset: int = 0,
    q: str = "",
    action: str = "",
    state: str = "",
) -> dict:
    environment = normalize_trading_environment(environment)
    inst_id = instId.strip().upper()
    keyword = q.strip()
    action_filter = action.strip()
    state_filter = state.strip()
    has_credentials = settings.has_credentials_for_environment(environment)
    local_events = database.list_sim_order_events(
        environment=environment,
        inst_id=inst_id,
        limit=limit,
        offset=offset,
        keyword=keyword,
        action=action_filter,
        state=state_filter,
    )
    total = database.count_sim_order_events(
        environment=environment,
        inst_id=inst_id,
        keyword=keyword,
        action=action_filter,
        state=state_filter,
    )
    page = (offset // limit) + 1
    page_count = max((total + limit - 1) // limit, 1)
    payload: dict[str, Any] = {
        "configured": has_credentials,
        "environment": environment,
        "simulatedTrading": environment == "simulated",
        "tradeEnabled": can_trade(environment),
        "liveTradingEnabled": settings.live_trading_enabled,
        "pending": [],
        "events": local_events,
        "paging": {
            "limit": limit,
            "offset": offset,
            "hasMore": offset + len(local_events) < total,
            "total": total,
            "page": page,
            "pageCount": page_count,
        },
        "source": "local",
        "ts": now_ms(),
    }
    if not has_credentials:
        payload["message"] = f"{environment_label(environment)} API Key 未配置。"
        return payload

    try:
        orders = cached_pending_orders(environment, inst_id, async_on_miss=environment == "simulated")
    except OkxError as exc:
        payload["warning"] = str(exc)
        return payload

    payload["pending"] = orders["pending"]
    payload["source"] = orders["source"]
    payload["ts"] = orders["ts"]
    payload["cacheAgeMs"] = orders["cacheAgeMs"]
    if orders.get("warning"):
        payload["warning"] = orders["warning"]
    return payload


def place_order_for_environment(environment: str, order: PlaceSimOrderRequest) -> dict:
    environment = normalize_trading_environment(environment)
    require_trading_enabled(environment)
    request_payload = build_place_order_payload(order)
    try:
        response = client_for_environment(environment).place_order(request_payload)
    except OkxError as exc:
        retry_payload = net_mode_retry_payload(request_payload, exc)
        if retry_payload:
            try:
                response = client_for_environment(environment).place_order(retry_payload)
                request_payload = retry_payload
            except OkxError as retry_exc:
                error_payload = retry_exc.payload or {"code": "okx-error", "msg": str(retry_exc), "data": []}
                event = sim_order_event(environment, "place", retry_payload, error_payload, "failed")
                invalidate_order_cache(environment, str(retry_payload.get("instId", "")))
                raise HTTPException(status_code=502, detail=order_error_detail(event, str(retry_exc))) from retry_exc
        else:
            error_payload = exc.payload or {"code": "okx-error", "msg": str(exc), "data": []}
            event = sim_order_event(environment, "place", request_payload, error_payload, "failed")
            invalidate_order_cache(environment, str(request_payload.get("instId", "")))
            raise HTTPException(status_code=502, detail=order_error_detail(event, str(exc))) from exc

    event = sim_order_event(
        environment,
        "place",
        request_payload,
        response,
        "accepted" if response_successful(response) else "failed",
    )
    invalidate_order_cache(environment, str(request_payload.get("instId", "")))
    if not success_code(event):
        raise HTTPException(status_code=400, detail=order_error_detail(event, "OKX 拒绝了该订单。"))

    return {
        "ok": True,
        "environment": environment,
        "data": response.get("data", []),
        "event": event,
        "source": order_source(environment),
        "ts": now_ms(),
    }


def close_position_for_environment(environment: str, order: ClosePositionRequest) -> dict:
    environment = normalize_trading_environment(environment)
    require_trading_enabled(environment)
    request_payload = build_close_position_payload(order)
    inst_id = str(request_payload.get("instId", ""))
    try:
        response = client_for_environment(environment).close_position(request_payload)
    except OkxError as exc:
        retry_payload = net_mode_retry_payload(request_payload, exc)
        if retry_payload:
            try:
                response = client_for_environment(environment).close_position(retry_payload)
                request_payload = retry_payload
            except OkxError as retry_exc:
                error_payload = retry_exc.payload or {"code": "okx-error", "msg": str(retry_exc), "data": []}
                event = sim_order_event(environment, "close-position", retry_payload, error_payload, "failed")
                invalidate_order_cache(environment, inst_id)
                raise HTTPException(status_code=502, detail=order_error_detail(event, str(retry_exc))) from retry_exc
        else:
            error_payload = exc.payload or {"code": "okx-error", "msg": str(exc), "data": []}
            event = sim_order_event(environment, "close-position", request_payload, error_payload, "failed")
            invalidate_order_cache(environment, inst_id)
            raise HTTPException(status_code=502, detail=order_error_detail(event, str(exc))) from exc

    event = sim_order_event(
        environment,
        "close-position",
        request_payload,
        response,
        "close_requested" if response_successful(response) else "failed",
    )
    invalidate_order_cache(environment, inst_id)
    with account_cache_condition:
        if account_cache.get("environment") == environment:
            reset_account_cache()
    if not success_code(event):
        raise HTTPException(status_code=400, detail=order_error_detail(event, "OKX 拒绝了该平仓请求。"))

    return {
        "ok": True,
        "environment": environment,
        "data": response.get("data", []),
        "event": event,
        "source": order_source(environment),
        "ts": now_ms(),
    }


def set_leverage_for_environment(environment: str, order: SetLeverageRequest) -> dict:
    environment = normalize_trading_environment(environment)
    require_trading_enabled(environment)
    request_payload = build_set_leverage_payload(order)
    inst_id = str(request_payload.get("instId", ""))
    try:
        response = client_for_environment(environment).set_leverage(request_payload)
    except OkxError as exc:
        retry_payload = net_mode_retry_payload(request_payload, exc)
        if retry_payload:
            try:
                response = client_for_environment(environment).set_leverage(retry_payload)
                request_payload = retry_payload
            except OkxError as retry_exc:
                raise HTTPException(status_code=502, detail=str(retry_exc)) from retry_exc
        else:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    with account_cache_condition:
        if account_cache.get("environment") == environment:
            reset_account_cache()

    return {
        "ok": True,
        "environment": environment,
        "data": response.get("data", []),
        "request": request_payload,
        "source": order_source(environment),
        "ts": now_ms(),
        "message": f"{environment_label(environment)}杠杆已提交设置。",
        "instId": inst_id,
    }


def place_local_paper_order(order: PlaceSimOrderRequest) -> dict:
    environment = current_trading_environment()
    if environment != "simulated":
        raise HTTPException(status_code=403, detail="本地模拟订单只能在虚拟盘环境提交。")

    request_payload = build_place_order_payload(order)
    local_order_id = f"LOCAL{uuid.uuid4().hex[:24].upper()}"
    response = {
        "code": "0",
        "data": [
            {
                "clOrdId": request_payload.get("clOrdId"),
                "ordId": local_order_id,
                "sCode": "0",
                "sMsg": "本地模拟订单，未发送到 OKX。",
            }
        ],
        "msg": "",
    }
    event = sim_order_event(environment, "place", request_payload, response, "accepted")
    invalidate_order_cache(environment, str(request_payload.get("instId", "")))
    return {
        "ok": True,
        "environment": environment,
        "data": response["data"],
        "event": event,
        "source": "local-paper",
        "ts": now_ms(),
    }


def cancel_order_for_environment(environment: str, order: CancelSimOrderRequest) -> dict:
    environment = normalize_trading_environment(environment)
    require_trading_enabled(environment)
    inst_id = order.instId.strip().upper()
    ord_id = (order.ordId or "").strip()
    cl_ord_id = (order.clOrdId or "").strip()
    if not inst_id.endswith("-SWAP"):
        raise HTTPException(status_code=400, detail="手动撤单当前只支持 OKX 永续合约 SWAP。")
    if not ord_id and not cl_ord_id:
        raise HTTPException(status_code=400, detail="撤单需要 ordId 或 clOrdId。")

    request_payload: dict[str, Any] = {"instId": inst_id}
    if ord_id:
        request_payload["ordId"] = ord_id
    elif cl_ord_id:
        request_payload["clOrdId"] = cl_ord_id

    try:
        response = client_for_environment(environment).cancel_order(request_payload)
    except OkxError as exc:
        error_payload = exc.payload or {"code": "okx-error", "msg": str(exc), "data": []}
        event = sim_order_event(environment, "cancel", request_payload, error_payload, "failed")
        invalidate_order_cache(environment, inst_id)
        raise HTTPException(status_code=502, detail=order_error_detail(event, str(exc))) from exc

    event = sim_order_event(
        environment,
        "cancel",
        request_payload,
        response,
        "cancel_requested" if response_successful(response) else "failed",
    )
    invalidate_order_cache(environment, inst_id)
    if not success_code(event):
        raise HTTPException(status_code=400, detail=order_error_detail(event, "OKX 拒绝了该撤单请求。"))

    return {
        "ok": True,
        "environment": environment,
        "data": response.get("data", []),
        "event": event,
        "source": order_source(environment),
        "ts": now_ms(),
    }


@app.get("/api/trading/orders")
def trading_orders(
    instId: Annotated[str, Query(max_length=64)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str, Query(max_length=128)] = "",
    action: Annotated[str, Query(max_length=32)] = "",
    state: Annotated[str, Query(max_length=32)] = "",
) -> dict:
    return orders_for_environment(
        current_trading_environment(),
        instId=instId,
        limit=limit,
        offset=offset,
        q=q,
        action=action,
        state=state,
    )


@app.get("/api/trading/leverage")
def trading_leverage(
    instId: Annotated[str, Query(min_length=1, max_length=64)],
    tdMode: Annotated[str, Query(min_length=1, max_length=16)] = "cross",
) -> dict:
    environment = current_trading_environment()
    if not settings.has_credentials_for_environment(environment):
        return {
            "configured": False,
            "environment": environment,
            "data": [],
            "message": f"{environment_label(environment)} API Key 未配置。",
            "ts": now_ms(),
        }

    inst_id = instId.strip().upper()
    td_mode = tdMode.strip().lower()
    if not inst_id.endswith("-SWAP"):
        raise HTTPException(status_code=400, detail="杠杆查询当前只支持 OKX 永续合约 SWAP。")
    if td_mode not in TRADE_MODES:
        raise HTTPException(status_code=400, detail="交易模式仅支持 cross 或 isolated。")

    try:
        payload = client_for_environment(environment).get_leverage_info(inst_id, td_mode)
    except OkxError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "configured": True,
        "environment": environment,
        "data": payload.get("data", []),
        "source": order_source(environment),
        "ts": now_ms(),
    }


@app.post("/api/trading/leverage")
def update_trading_leverage(order: SetLeverageRequest) -> dict:
    return set_leverage_for_environment(current_trading_environment(), order)


@app.post("/api/trading/orders")
def place_trading_order(order: PlaceSimOrderRequest) -> dict:
    return place_order_for_environment(current_trading_environment(), order)


@app.post("/api/trading/positions/close")
def close_trading_position(order: ClosePositionRequest) -> dict:
    return close_position_for_environment(current_trading_environment(), order)


@app.post("/api/trading/orders/local")
def place_local_trading_order(order: PlaceSimOrderRequest) -> dict:
    return place_local_paper_order(order)


@app.post("/api/trading/orders/cancel")
def cancel_trading_order(order: CancelSimOrderRequest) -> dict:
    return cancel_order_for_environment(current_trading_environment(), order)


@app.get("/api/sim/orders")
def sim_orders(
    instId: Annotated[str, Query(max_length=64)] = "",
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> dict:
    return orders_for_environment("simulated", instId=instId, limit=limit)


@app.post("/api/sim/orders")
def place_sim_order(order: PlaceSimOrderRequest) -> dict:
    return place_order_for_environment("simulated", order)


@app.post("/api/sim/orders/cancel")
def cancel_sim_order(order: CancelSimOrderRequest) -> dict:
    return cancel_order_for_environment("simulated", order)


async def realtime_heartbeat(session: RealtimeSession) -> None:
    while True:
        await asyncio.sleep(25)
        if not await realtime_hub.send(
            session,
            {
                "type": "heartbeat",
                "topic": "heartbeat",
                "source": "backend",
                "ts": now_ms(),
            },
        ):
            return


async def realtime_public_ticker_sender(
    session: RealtimeSession,
    environment: str,
    inst_ids: list[str],
) -> None:
    active_inst_ids = list(dict.fromkeys(inst_ids))
    if not active_inst_ids:
        await realtime_hub.send(
            session,
            {
                "type": "error",
                "topic": "market.ticker",
                "source": "backend",
                "message": "ticker 订阅需要至少一个合约。",
                "ts": now_ms(),
            },
        )
        return
    attempt = 0
    last_sent_by_inst: dict[str, int] = {}
    skipped_inst_ids: set[str] = set()
    last_partial_notice_ts = 0

    def ticker_chunks(values: list[str], chunk_size: int = 20) -> list[list[str]]:
        if len(values) <= 1:
            return [values]
        chunks = [[values[0]]]
        remaining = values[1:]
        chunks.extend(remaining[index : index + chunk_size] for index in range(0, len(remaining), chunk_size))
        return [chunk for chunk in chunks if chunk]

    while True:
        queue: asyncio.Queue[tuple[str, list[str], dict[str, Any] | OkxWsError]] = asyncio.Queue()
        tasks: list[asyncio.Task[None]] = []

        async def forward(chunk: list[str]) -> None:
            try:
                async for event in stream_public_tickers(settings.ws_public_url_for_environment(environment), chunk):
                    await queue.put(("event", chunk, event))
            except asyncio.CancelledError:
                raise
            except OkxWsError as exc:
                await queue.put(("error", chunk, exc))

        def start_chunk(chunk: list[str]) -> None:
            tasks.append(asyncio.create_task(forward(chunk)))

        for chunk in ticker_chunks(active_inst_ids):
            start_chunk(chunk)

        try:
            if attempt:
                await realtime_hub.send(
                    session,
                    {
                        "type": "stale",
                        "topic": "market.ticker",
                        "environment": environment,
                        "source": "okx-ws",
                        "refreshRequired": True,
                        "message": "行情 WebSocket 已重连，请刷新 ticker 快照。",
                        "ts": now_ms(),
                    },
                )
            while True:
                kind, chunk, event = await queue.get()
                if kind == "error":
                    exc = event
                    failed_inst_id = str(getattr(exc, "inst_id", "") or "").upper()
                    failed_channel = str(getattr(exc, "channel", "") or "")
                    failed_code = str(getattr(exc, "code", "") or "")
                    if failed_code == "60018" and failed_channel == "tickers" and failed_inst_id in active_inst_ids:
                        active_inst_ids = [item for item in active_inst_ids if item != failed_inst_id]
                        skipped_inst_ids.add(failed_inst_id)
                        notice_ts = now_ms()
                        if len(skipped_inst_ids) == 1 or notice_ts - last_partial_notice_ts >= 2000:
                            last_partial_notice_ts = notice_ts
                            if not await realtime_hub.send(
                                session,
                                {
                                    "type": "status",
                                    "topic": "market.ticker",
                                    "environment": environment,
                                    "source": "partial-fallback",
                                    "message": f"部分合约价格实时回退，{len(skipped_inst_ids)} 个使用 REST/缓存快照。",
                                    "refreshRequired": True,
                                    "skippedInstIds": sorted(skipped_inst_ids),
                                    "activeCount": len(active_inst_ids),
                                    "ts": notice_ts,
                                },
                            ):
                                return
                        if not active_inst_ids:
                            if not await realtime_hub.send(
                                session,
                                {
                                    "type": "disabled",
                                    "topic": "market.ticker",
                                    "environment": environment,
                                    "source": "rest-fallback",
                                    "message": "本轮 ticker 合约均无法实时订阅，已保留 REST/缓存快照。",
                                    "refreshRequired": True,
                                    "skippedInstIds": sorted(skipped_inst_ids),
                                    "ts": now_ms(),
                                },
                            ):
                                return
                            return
                        next_chunk = [item for item in chunk if item != failed_inst_id]
                        if next_chunk:
                            start_chunk(next_chunk)
                        continue
                    raise exc

                attempt = 0
                if event["type"] == "ticker":
                    inst_id = str(event.get("instId") or event.get("data", {}).get("instId") or "")
                    tick_ts = now_ms()
                    if tick_ts - last_sent_by_inst.get(inst_id, 0) < 500:
                        continue
                    last_sent_by_inst[inst_id] = tick_ts
                    if not await realtime_hub.send(
                        session,
                        {
                            "type": "market.ticker",
                            "topic": "market.ticker",
                            "environment": environment,
                            "instId": inst_id,
                            "data": event["data"],
                            "source": "okx-ws",
                            "ts": tick_ts,
                        },
                    ):
                        return
                elif event["type"] == "status":
                    payload = {**event, "type": "status", "environment": environment}
                    if not await realtime_hub.send(session, payload):
                        return
        except asyncio.CancelledError:
            raise
        except OkxWsError as exc:
            if not await realtime_hub.send(
                session,
                {
                    "type": "error",
                    "topic": "market.ticker",
                    "environment": environment,
                    "source": "okx-ws",
                    "message": str(exc),
                    "refreshRequired": True,
                    "ts": now_ms(),
                },
            ):
                return
            attempt += 1
            await asyncio.sleep(min(30, 2**min(attempt, 5)))
        finally:
            await cancel_tasks(tasks)


def normalize_candle_batch(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return valid candle rows in ascending timestamp order with duplicate timestamps removed."""
    by_timestamp: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            timestamp = int(str(row.get("ts") or ""))
        except (TypeError, ValueError):
            continue
        if timestamp <= 0:
            continue
        by_timestamp[timestamp] = {**row, "ts": str(timestamp)}
    return [by_timestamp[timestamp] for timestamp in sorted(by_timestamp)]


def candle_batch_issue(rows: list[dict[str, Any]], bar: str, current_ms: int | None = None) -> str | None:
    """Classify whether a normalized candle batch is safe to present as a current chart seed."""
    normalized = normalize_candle_batch(rows)
    if not normalized:
        return "empty"
    interval_ms = CANDLE_BAR_MILLISECONDS[bar]
    timestamps = [int(item["ts"]) for item in normalized]
    now = now_ms() if current_ms is None else current_ms
    if timestamps[-1] > now + interval_ms:
        return "future"
    if now - timestamps[-1] > interval_ms * CANDLE_CACHE_FRESHNESS_BARS:
        return "stale"
    if any(current - previous > interval_ms * CANDLE_GAP_TOLERANCE_BARS for previous, current in zip(timestamps, timestamps[1:])):
        return "gap"
    return None


def candle_batch_warning(issue: str | None) -> str:
    messages = {
        "empty": "K线快照为空，正在等待数据补齐。",
        "future": "K线时间异常，正在等待 OKX 快照校正。",
        "stale": "K线缓存已过期，正在等待 OKX 最新快照。",
        "gap": "K线缓存存在时间断层，正在等待 OKX 最新快照。",
    }
    return messages.get(issue or "", "K线历史暂不完整，正在等待 OKX 快照。")


def chart_snapshot_id(inst_id: str, bar: str, candles: list[dict[str, Any]]) -> str:
    material = {
        "instId": inst_id,
        "bar": bar,
        "candles": [
            [item.get("ts"), item.get("open"), item.get("high"), item.get("low"), item.get("close"), item.get("volume"), item.get("confirm")]
            for item in candles
        ],
    }
    digest = hashlib.sha256(json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
    return f"cs_{digest[:40]}"


def prune_chart_snapshots(current_ms: int | None = None) -> None:
    now = now_ms() if current_ms is None else current_ms
    expired = [snapshot_id for snapshot_id, item in chart_snapshot_cache.items() if now - int(item.get("createdAt") or 0) > CHART_SNAPSHOT_CACHE_SECONDS * 1000]
    for snapshot_id in expired:
        chart_snapshot_cache.pop(snapshot_id, None)


def create_chart_snapshot(
    inst_id: str,
    bar: str,
    rows: list[dict[str, Any]],
    source: str,
    *,
    warning: str = "",
    snapshot_ts: int | None = None,
) -> dict[str, Any]:
    normalized = normalize_candle_batch(rows)[-CHART_SNAPSHOT_CANDLE_LIMIT:]
    created_at = now_ms() if snapshot_ts is None else snapshot_ts
    issue = candle_batch_issue(normalized, bar, created_at)
    effective_warning = warning or (candle_batch_warning(issue) if issue else "")
    snapshot_id = chart_snapshot_id(inst_id, bar, normalized)
    metadata = {
        "snapshotId": snapshot_id,
        "instId": inst_id,
        "bar": bar,
        "candleCount": len(normalized),
        "lastCandleTs": int(normalized[-1]["ts"]) if normalized else 0,
        "snapshotTs": created_at,
        "source": source,
        "warning": effective_warning,
        "complete": issue is None,
        "currentCandleOpen": bool(normalized and str(normalized[-1].get("confirm") or "") != "1"),
    }
    snapshot = {"metadata": metadata, "candles": deepcopy(normalized), "createdAt": created_at}
    with chart_snapshot_cache_lock:
        prune_chart_snapshots(created_at)
        chart_snapshot_cache[snapshot_id] = snapshot
    return deepcopy(snapshot)


def chart_snapshot_metadata(
    inst_id: str,
    bar: str,
    rows: list[dict[str, Any]],
    source: str,
    *,
    warning: str = "",
    snapshot_ts: int | None = None,
) -> dict[str, Any]:
    return create_chart_snapshot(inst_id, bar, rows, source, warning=warning, snapshot_ts=snapshot_ts)["metadata"]


def chart_snapshot_for_request(snapshot_id: str, inst_id: str, bar: str) -> tuple[dict[str, Any] | None, str]:
    if not snapshot_id:
        return None, "请先加载当前图表快照后再开始分析。"
    with chart_snapshot_cache_lock:
        prune_chart_snapshots()
        snapshot = deepcopy(chart_snapshot_cache.get(snapshot_id))
    if not snapshot:
        return None, "图表快照已过期，请等待图表数据重新加载后再分析。"
    metadata = snapshot.get("metadata") if isinstance(snapshot.get("metadata"), dict) else {}
    if metadata.get("instId") != inst_id or metadata.get("bar") != bar:
        return None, "图表快照与当前合约或周期不一致，请重新加载后再分析。"
    if not metadata.get("complete") or candle_batch_issue(snapshot.get("candles") or [], bar):
        return None, "当前图表 K线尚未更新，请等待最新快照后再分析。"
    return snapshot, ""


async def realtime_public_candle_sender(
    session: RealtimeSession,
    environment: str,
    inst_id: str,
    bar: str,
) -> None:
    if bar not in SUPPORTED_BARS:
        await realtime_hub.send(
            session,
            {
                "type": "error",
                "topic": "market.candles",
                "environment": environment,
                "source": "backend",
                "message": "Unsupported K-line interval",
                "ts": now_ms(),
            },
        )
        return

    cached_seed = normalize_candle_batch(await asyncio.to_thread(database.latest_candles, inst_id, bar, 200))
    cached_issue = candle_batch_issue(cached_seed, bar)
    if cached_seed and cached_issue is None:
        snapshot_ts = now_ms()
        if not await realtime_hub.send(
            session,
            {
                "type": "market.candles",
                "topic": "market.candles",
                "environment": environment,
                "instId": inst_id,
                "bar": bar,
                "data": cached_seed,
                "source": "cache-seed",
                "ts": snapshot_ts,
                "snapshot": chart_snapshot_metadata(inst_id, bar, cached_seed, "cache-seed", snapshot_ts=snapshot_ts),
            },
        ):
            return

    try:
        initial_rows = normalize_candle_batch(
            await asyncio.to_thread(client_for_environment(environment).get_candles, inst_id, bar, 200)
        )
        if initial_rows:
            await asyncio.to_thread(database.upsert_candles, inst_id, bar, initial_rows)
            initial_issue = candle_batch_issue(initial_rows, bar)
            snapshot_ts = now_ms()
            source = "rest-seed" if initial_issue is None else "rest-degraded"
            warning = candle_batch_warning(initial_issue) if initial_issue else ""
            if not await realtime_hub.send(
                session,
                {
                    "type": "market.candles",
                    "topic": "market.candles",
                    "environment": environment,
                    "instId": inst_id,
                    "bar": bar,
                    "data": initial_rows,
                    "source": source,
                    "warning": warning or None,
                    "ts": snapshot_ts,
                    "snapshot": chart_snapshot_metadata(inst_id, bar, initial_rows, source, warning=warning, snapshot_ts=snapshot_ts),
                },
            ):
                return
        elif cached_issue is not None:
            snapshot_ts = now_ms()
            warning = candle_batch_warning(cached_issue)
            if not await realtime_hub.send(
                session,
                {
                    "type": "market.candles",
                    "topic": "market.candles",
                    "environment": environment,
                    "instId": inst_id,
                    "bar": bar,
                    "data": cached_seed,
                    "source": "cache-degraded",
                    "warning": warning,
                    "ts": snapshot_ts,
                    "snapshot": chart_snapshot_metadata(inst_id, bar, cached_seed, "cache-degraded", warning=warning, snapshot_ts=snapshot_ts),
                },
            ):
                return
    except Exception as exc:
        cached = normalize_candle_batch(await asyncio.to_thread(database.latest_candles, inst_id, bar, 200))
        cached_issue = candle_batch_issue(cached, bar)
        warning = str(exc) if cached_issue is None else f"{candle_batch_warning(cached_issue)} {str(exc)}"
        snapshot_ts = now_ms()
        source = "cache" if cached_issue is None else "cache-degraded"
        if not await realtime_hub.send(
            session,
            {
                "type": "market.candles",
                "topic": "market.candles",
                "environment": environment,
                "instId": inst_id,
                "bar": bar,
                "data": cached,
                "source": source,
                "warning": warning,
                "ts": snapshot_ts,
                "snapshot": chart_snapshot_metadata(inst_id, bar, cached, source, warning=warning, snapshot_ts=snapshot_ts),
            },
        ):
            return

    attempt = 0
    while True:
        try:
            if attempt:
                await realtime_hub.send(
                    session,
                    {
                        "type": "stale",
                        "topic": "market.candles",
                        "environment": environment,
                        "instId": inst_id,
                        "bar": bar,
                        "source": "okx-ws",
                        "refreshRequired": True,
                        "message": "K线 WebSocket 已重连，请刷新快照。",
                        "ts": now_ms(),
                    },
                )
            async for event in stream_public_candles(settings.ws_business_url_for_environment(environment), inst_id, bar):
                attempt = 0
                if event["type"] == "candle":
                    rows = normalize_candle_batch(event["data"])
                    await asyncio.to_thread(database.upsert_candles, inst_id, bar, rows)
                    cached = normalize_candle_batch(await asyncio.to_thread(database.latest_candles, inst_id, bar, 200))
                    cached_issue = candle_batch_issue(cached, bar)
                    snapshot_ts = now_ms()
                    source = "okx-ws" if cached_issue is None else "okx-ws-degraded"
                    warning = candle_batch_warning(cached_issue) if cached_issue else ""
                    payload = {
                        "type": "market.candles",
                        "topic": "market.candles",
                        "environment": environment,
                        "instId": inst_id,
                        "bar": bar,
                        "data": cached,
                        "source": source,
                        "channel": candle_channel(bar),
                        "warning": warning or None,
                        "ts": snapshot_ts,
                        "snapshot": chart_snapshot_metadata(inst_id, bar, cached, source, warning=warning, snapshot_ts=snapshot_ts),
                    }
                else:
                    payload = {**event, "type": "status", "environment": environment}
                if not await realtime_hub.send(session, payload):
                    return
        except asyncio.CancelledError:
            raise
        except OkxWsError as exc:
            if not await realtime_hub.send(
                session,
                {
                    "type": "error",
                    "topic": "market.candles",
                    "environment": environment,
                    "source": "okx-ws",
                    "message": str(exc),
                    "refreshRequired": True,
                    "ts": now_ms(),
                },
            ):
                return
            attempt += 1
            await asyncio.sleep(min(30, 2**min(attempt, 5)))


async def realtime_private_sender(session: RealtimeSession, environment: str, topics: set[str]) -> None:
    private_topics = topics & PRIVATE_TOPICS
    if not private_topics:
        return
    if not settings.has_credentials_for_environment(environment):
        for topic in sorted(private_topics):
            if not await realtime_hub.send(
                session,
                {
                    "type": "disabled",
                    "topic": topic,
                    "environment": environment,
                    "source": "backend",
                    "message": f"{environment_label(environment)} API Key 未配置，实时私有频道不可用。",
                    "refreshRequired": True,
                    "ts": now_ms(),
                },
            ):
                return
        return

    attempt = 0
    while True:
        try:
            if attempt:
                for topic in sorted(private_topics):
                    if not await realtime_hub.send(
                        session,
                        {
                            "type": "stale",
                            "topic": topic,
                            "environment": environment,
                            "source": "okx-private-ws",
                            "refreshRequired": True,
                            "message": "OKX 私有 WebSocket 已重连，请刷新 REST 快照。",
                            "ts": now_ms(),
                        },
                    ):
                        return
            async for event in stream_private_account_data(
                settings.ws_private_url_for_environment(environment),
                settings.for_environment(environment),
                private_topics,
            ):
                attempt = 0
                event_type = str(event.get("type") or "")
                data = event.get("data") if isinstance(event.get("data"), list) else []
                if event_type == "orders":
                    for row in data:
                        if not isinstance(row, dict):
                            continue
                        record = await asyncio.to_thread(record_private_order_update, environment, row, event.get("raw") or {})
                        if not await realtime_hub.send(
                            session,
                            {
                                "type": "order.update",
                                "topic": "orders",
                                "environment": environment,
                                "data": record,
                                "source": "okx-private-ws",
                                "refreshRequired": True,
                                "ts": now_ms(),
                            },
                        ):
                            return
                elif event_type == "account":
                    if not await realtime_hub.send(
                        session,
                        {
                            "type": "account.update",
                            "topic": "account",
                            "environment": environment,
                            "data": data,
                            "source": "okx-private-ws",
                            "refreshRequired": True,
                            "ts": now_ms(),
                        },
                    ):
                        return
                elif event_type == "positions":
                    if not await realtime_hub.send(
                        session,
                        {
                            "type": "position.update",
                            "topic": "positions",
                            "environment": environment,
                            "data": data,
                            "source": "okx-private-ws",
                            "refreshRequired": True,
                            "ts": now_ms(),
                        },
                    ):
                        return
                elif event_type == "status":
                    if not await realtime_hub.send(session, {**event, "type": "status", "environment": environment}):
                        return
        except asyncio.CancelledError:
            raise
        except OkxWsError as exc:
            if not await realtime_hub.send(
                session,
                {
                    "type": "error",
                    "topic": "private",
                    "environment": environment,
                    "source": "okx-private-ws",
                    "message": str(exc),
                    "refreshRequired": True,
                    "ts": now_ms(),
                },
            ):
                return
            attempt += 1
            await asyncio.sleep(min(30, 2**min(attempt, 5)))


def realtime_tasks_for_subscription(session: RealtimeSession, payload: dict[str, Any], topics: set[str]) -> list[asyncio.Task[Any]]:
    environment = normalize_trading_environment(str(payload.get("environment") or current_trading_environment()))
    inst_ids = normalize_inst_ids(payload)
    primary_inst_id = str(payload.get("instId") or "").strip().upper()
    inst_id = primary_inst_id or (inst_ids[0] if inst_ids else "BTC-USDT-SWAP")
    bar = str(payload.get("bar") or "1m")
    tasks: list[asyncio.Task[Any]] = []
    if topics & MARKET_TOPICS:
        if "market.candles" in topics or "market" in topics:
            tasks.append(asyncio.create_task(realtime_public_candle_sender(session, environment, inst_id, bar)))
        if "market.ticker" in topics or ("market" in topics and inst_ids):
            ticker_inst_ids = [inst_id, *[item for item in inst_ids if item != inst_id]]
            tasks.append(asyncio.create_task(realtime_public_ticker_sender(session, environment, ticker_inst_ids)))
    if topics & PRIVATE_TOPICS:
        tasks.append(asyncio.create_task(realtime_private_sender(session, environment, topics)))
    return tasks


@app.websocket("/ws/realtime")
async def realtime_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    realtime_hub.attach_loop()
    session = await realtime_hub.connect(websocket)
    stream_tasks: list[asyncio.Task[Any]] = []
    heartbeat_task = asyncio.create_task(realtime_heartbeat(session))
    await realtime_hub.send(
        session,
        {
            "type": "status",
            "topic": "connection",
            "source": "backend",
            "message": "实时通道已连接。",
            "sessionId": session.session_id,
            "ts": now_ms(),
        },
    )
    try:
        while True:
            payload = await websocket.receive_json()
            op = str(payload.get("op") or "subscribe").strip().lower()
            if op == "ping":
                if not await realtime_hub.send(session, {"type": "pong", "topic": "heartbeat", "source": "backend", "ts": now_ms()}):
                    return
                continue

            if op == "unsubscribe":
                await cancel_tasks(stream_tasks)
                stream_tasks = []
                await realtime_hub.update_subscription(session, set(), session.environment)
                if not await realtime_hub.send(
                    session,
                    {"type": "status", "topic": "connection", "source": "backend", "message": "实时订阅已取消。", "ts": now_ms()},
                ):
                    return
                continue

            if op != "subscribe":
                if not await realtime_hub.send(
                    session,
                    {
                        "type": "error",
                        "topic": "connection",
                        "source": "backend",
                        "message": f"Unsupported realtime operation: {op}",
                        "ts": now_ms(),
                    },
                ):
                    return
                continue

            topics, unsupported = normalize_subscription_message(payload)
            for topic in unsupported:
                if not await realtime_hub.send(
                    session,
                    {
                        "type": "error",
                        "topic": topic,
                        "source": "backend",
                        "message": f"Unsupported realtime topic: {topic}",
                        "ts": now_ms(),
                    },
                ):
                    return
            if not topics:
                continue

            try:
                environment = normalize_trading_environment(str(payload.get("environment") or current_trading_environment()))
            except HTTPException as exc:
                if not await realtime_hub.send(
                    session,
                    {
                        "type": "error",
                        "topic": "connection",
                        "source": "backend",
                        "message": str(exc.detail),
                        "ts": now_ms(),
                    },
                ):
                    return
                continue

            await cancel_tasks(stream_tasks)
            await realtime_hub.update_subscription(session, topics, environment)
            if not await realtime_hub.send(
                session,
                {
                    "type": "status",
                    "topic": "connection",
                    "source": "backend",
                    "environment": environment,
                    "topics": sorted(topics),
                    "message": "实时订阅已更新。",
                    "ts": now_ms(),
                },
            ):
                return
            stream_tasks = realtime_tasks_for_subscription(session, payload, topics)
    except (WebSocketDisconnect, RuntimeError):
        return
    finally:
        heartbeat_task.cancel()
        await cancel_tasks([heartbeat_task, *stream_tasks])
        await realtime_hub.disconnect(session)


@app.websocket("/ws/candles")
async def candle_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    inst_id = websocket.query_params.get("instId", "BTC-USDT-SWAP").upper()
    bar = websocket.query_params.get("bar", "1m")
    if bar not in SUPPORTED_BARS:
        await send_ws_json(websocket, {"type": "error", "message": "Unsupported K-line interval"})
        await websocket.close(code=1008)
        return

    cached_seed = await asyncio.to_thread(database.latest_candles, inst_id, bar, 200)
    if cached_seed:
        if not await send_ws_json(
            websocket,
            {
                "type": "candles",
                "instId": inst_id,
                "bar": bar,
                "data": cached_seed,
                "source": "cache-seed",
                "ts": now_ms(),
            },
        ):
            return

    try:
        initial_rows = await asyncio.to_thread(client.get_candles, inst_id, bar, 200)
        await asyncio.to_thread(database.upsert_candles, inst_id, bar, initial_rows)
        if not await send_ws_json(
            websocket,
            {
                "type": "candles",
                "instId": inst_id,
                "bar": bar,
                "data": initial_rows,
                "source": "rest-seed",
                "ts": now_ms(),
            },
        ):
            return
    except Exception as exc:
        cached = await asyncio.to_thread(database.latest_candles, inst_id, bar, 200)
        if not await send_ws_json(
            websocket,
            {
                "type": "candles",
                "instId": inst_id,
                "bar": bar,
                "data": cached,
                "source": "cache",
                "warning": str(exc),
                "ts": now_ms(),
            },
        ):
            return

    try:
        async for event in stream_market_data(settings.ws_business_url, inst_id, bar, settings.ws_public_url):
            try:
                if event["type"] == "candle":
                    rows = event["data"]
                    await asyncio.to_thread(database.upsert_candles, inst_id, bar, rows)
                    cached = await asyncio.to_thread(database.latest_candles, inst_id, bar, 200)
                    if not await send_ws_json(
                        websocket,
                        {
                            "type": "candles",
                            "instId": inst_id,
                            "bar": bar,
                            "data": cached,
                            "source": "okx-ws",
                            "channel": candle_channel(bar),
                            "ts": now_ms(),
                        },
                    ):
                        return
                elif event["type"] == "ticker":
                    if not await send_ws_json(
                        websocket,
                        {
                            "type": "ticker",
                            "instId": inst_id,
                            "data": event["data"],
                            "source": "okx-ws",
                            "ts": now_ms(),
                        },
                    ):
                        return
                elif event["type"] == "status":
                    if not await send_ws_json(websocket, event):
                        return
            except WebSocketDisconnect:
                return
            except RuntimeError as exc:
                if "close message" in str(exc):
                    return
                raise
    except (WebSocketDisconnect, RuntimeError):
        return
    except OkxWsError as exc:
        if not await send_ws_json(
            websocket,
            {
                "type": "error",
                "message": str(exc),
                "source": "okx-ws",
                "ts": now_ms(),
            },
        ):
            return

    try:
        while True:
            try:
                rows = await asyncio.to_thread(client.get_candles, inst_id, bar, 200)
                await asyncio.to_thread(database.upsert_candles, inst_id, bar, rows)
                if not await send_ws_json(
                    websocket,
                    {
                        "type": "candles",
                        "instId": inst_id,
                        "bar": bar,
                        "data": rows,
                        "source": "rest-fallback",
                        "warning": "OKX WebSocket unavailable; using REST fallback.",
                        "ts": now_ms(),
                    },
                ):
                    return
            except WebSocketDisconnect:
                return
            except RuntimeError as exc:
                if "close message" in str(exc):
                    return
                raise
            except Exception as exc:
                cached = await asyncio.to_thread(database.latest_candles, inst_id, bar, 200)
                if not await send_ws_json(
                    websocket,
                    {
                        "type": "candles",
                        "instId": inst_id,
                        "bar": bar,
                        "data": cached,
                        "source": "cache",
                        "warning": str(exc),
                        "ts": now_ms(),
                    },
                ):
                    return
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return
