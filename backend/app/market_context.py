"""市场上下文聚合：把 OKX 公开行情聚合成「大盘 + 赛道 + 情绪」摘要。

纯函数模块，不发起网络请求；所有数据由调用方（main.py 的缓存层）拉取后传入，
便于单测与失败降级。输出只用于给 LLM 提供判断背景，不参与风控拦截。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

# 赛道篮子：以 USDT 本位永续为成分。成分币按 OKX 实际存在的合约过滤，
# 缺失的自动跳过，不会因某一币下架而报错。
SECTOR_BASKETS: dict[str, list[str]] = {
    "L1": ["SOL", "ADA", "AVAX", "DOT", "NEAR", "APT", "SUI", "TRX", "ATOM", "ALGO", "FIL", "ICP", "HBAR", "XLM", "ETC", "BNB"],
    "L2": ["ARB", "OP", "POL", "IMX", "STRK", "METIS", "ZK"],
    "Meme": ["DOGE", "SHIB", "PEPE", "WIF", "BONK", "FLOKI", "MEME", "BOME", "POPCAT", "MEW"],
    "AI": ["FET", "RENDER", "TAO", "GRT", "ARKM", "JUP"],
    "DeFi": ["UNI", "AAVE", "LINK", "INJ", "SNX", "CRV", "LDO", "COMP", "SUSHI", "PENDLE", "ONDO"],
}

SECTOR_LABELS = {
    "L1": "公链 L1",
    "L2": "二层 L2",
    "Meme": "Meme 币",
    "AI": "AI 概念",
    "DeFi": "DeFi",
}

# 情绪采样标的：BTC/ETH + 各赛道龙头，控制请求量。
SENTIMENT_SAMPLE_INST_IDS = [
    "BTC-USDT-SWAP",
    "ETH-USDT-SWAP",
    "SOL-USDT-SWAP",
    "ARB-USDT-SWAP",
    "DOGE-USDT-SWAP",
    "FET-USDT-SWAP",
    "UNI-USDT-SWAP",
]

MAJOR_INST_IDS = {"BTC-USDT-SWAP": "BTC", "ETH-USDT-SWAP": "ETH"}


def _decimal(value: Any) -> Decimal | None:
    try:
        if value is None or value == "":
            return None
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator * Decimal("100")


def _fmt(value: Decimal | None, places: str = "0.01") -> str:
    if value is None:
        return ""
    return str(value.quantize(Decimal(places)))


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / Decimal("2")


def ticker_change_pct(ticker: dict[str, Any]) -> Decimal | None:
    """24h 涨跌幅（%）。用 last / open24h - 1，open24h 缺失或为 0 时返回 None。"""
    last = _decimal(ticker.get("last"))
    open24h = _decimal(ticker.get("open24h"))
    if last is None or open24h is None or open24h == 0:
        return None
    return _pct(last - open24h, open24h)


def ticker_range_position_pct(ticker: dict[str, Any]) -> Decimal | None:
    """当前价在 24h 高低区间中的相对位置（0=最低，100=最高）。"""
    last = _decimal(ticker.get("last"))
    high = _decimal(ticker.get("high24h"))
    low = _decimal(ticker.get("low24h"))
    if last is None or high is None or low is None or high <= low:
        return None
    return _pct(last - low, high - low)


def _ticker_map(tickers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in tickers or []:
        if not isinstance(item, dict):
            continue
        inst_id = str(item.get("instId") or "").upper()
        if inst_id:
            result[inst_id] = item
    return result


def build_breadth(tickers: list[dict[str, Any]]) -> dict[str, Any]:
    """全市场涨跌宽度：上涨/下跌家数、上涨占比、中位与均值涨跌。"""
    changes: list[Decimal] = []
    for item in tickers or []:
        if not isinstance(item, dict):
            continue
        change = ticker_change_pct(item)
        if change is not None:
            changes.append(change)
    if not changes:
        return {"total": 0, "rising": 0, "falling": 0, "flat": 0, "advancePct": "", "medianChange24hPct": "", "avgChange24hPct": ""}
    rising = sum(1 for value in changes if value > Decimal("0.1"))
    falling = sum(1 for value in changes if value < Decimal("-0.1"))
    flat = len(changes) - rising - falling
    avg = sum(changes, Decimal("0")) / Decimal(len(changes))
    return {
        "total": len(changes),
        "rising": rising,
        "falling": falling,
        "flat": flat,
        "advancePct": _fmt(_pct(Decimal(rising), Decimal(len(changes)))),
        "medianChange24hPct": _fmt(_median(changes)),
        "avgChange24hPct": _fmt(avg),
    }


def build_majors(tickers_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    majors: dict[str, Any] = {}
    for inst_id, label in MAJOR_INST_IDS.items():
        ticker = tickers_by_id.get(inst_id)
        if not ticker:
            continue
        majors[label.lower()] = {
            "instId": inst_id,
            "last": str(ticker.get("last") or ""),
            "change24hPct": _fmt(ticker_change_pct(ticker)),
            "rangePositionPct": _fmt(ticker_range_position_pct(ticker)),
        }
    return majors


def build_sectors(tickers_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """按赛道聚合 24h 平均涨跌、上涨占比与龙头（涨幅最高者）。"""
    sectors: list[dict[str, Any]] = []
    for name, bases in SECTOR_BASKETS.items():
        members: list[tuple[str, Decimal]] = []
        for base in bases:
            ticker = tickers_by_id.get(f"{base}-USDT-SWAP")
            if not ticker:
                continue
            change = ticker_change_pct(ticker)
            if change is None:
                continue
            members.append((base, change))
        if not members:
            continue
        changes = [change for _, change in members]
        rising = sum(1 for value in changes if value > Decimal("0"))
        avg = sum(changes, Decimal("0")) / Decimal(len(changes))
        leader_base, leader_change = max(members, key=lambda pair: pair[1])
        sectors.append(
            {
                "name": name,
                "label": SECTOR_LABELS.get(name, name),
                "members": len(members),
                "avgChange24hPct": _fmt(avg),
                "risingPct": _fmt(_pct(Decimal(rising), Decimal(len(changes)))),
                "leader": leader_base,
                "leaderChange24hPct": _fmt(leader_change),
            }
        )
    sectors.sort(key=lambda item: _decimal(item.get("avgChange24hPct")) or Decimal("0"), reverse=True)
    return sectors


def classify_bias(breadth: dict[str, Any], majors: dict[str, Any]) -> str:
    """综合大盘倾向：risk-on / mixed / risk-off。

    规则保守，只在证据较一致时给出方向，其余一律 mixed，避免过度解读。
    """
    advance = _decimal(breadth.get("advancePct"))
    btc_change = _decimal((majors.get("btc") or {}).get("change24hPct"))
    if advance is None or btc_change is None:
        return "mixed"
    if btc_change <= Decimal("-2") or advance <= Decimal("35"):
        return "risk-off"
    if btc_change >= Decimal("2") and advance >= Decimal("60"):
        return "risk-on"
    return "mixed"


def normalize_sentiment(raw: dict[str, Any] | None) -> dict[str, Any]:
    """归一化情绪输入（funding 分布 + OI 总量）。缺失字段返回空，不报错。"""
    raw = raw or {}
    funding = raw.get("funding") if isinstance(raw.get("funding"), dict) else {}
    oi = raw.get("openInterest") if isinstance(raw.get("openInterest"), dict) else {}
    return {
        "funding": {
            "sampled": int(funding.get("sampled") or 0),
            "positive": int(funding.get("positive") or 0),
            "negative": int(funding.get("negative") or 0),
            "neutral": int(funding.get("neutral") or 0),
            "avgFundingRatePct": str(funding.get("avgFundingRatePct") or ""),
        },
        "openInterest": {
            "sampled": int(oi.get("sampled") or 0),
            "totalOiUsd": str(oi.get("totalOiUsd") or ""),
        },
    }


def build_market_context(
    tickers: list[dict[str, Any]],
    sentiment: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """聚合大盘 + 赛道 + 情绪的完整摘要。"""
    tickers_by_id = _ticker_map(tickers)
    breadth = build_breadth(tickers)
    majors = build_majors(tickers_by_id)
    sectors = build_sectors(tickers_by_id)
    context = {
        "breadth": breadth,
        "majors": majors,
        "bias": classify_bias(breadth, majors),
        "sectors": sectors,
        "sentiment": normalize_sentiment(sentiment),
        "warnings": [str(item) for item in (warnings or [])][:5],
    }
    return context


def sector_brief(context: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    """压缩赛道摘要给 LLM：只保留名称、平均涨跌、上涨占比、龙头。"""
    rows = (context or {}).get("sectors") or []
    return [
        {
            "name": row.get("label") or row.get("name"),
            "avgChange24hPct": row.get("avgChange24hPct"),
            "risingPct": row.get("risingPct"),
            "leader": row.get("leader"),
            "leaderChange24hPct": row.get("leaderChange24hPct"),
        }
        for row in rows[:limit]
    ]
