from __future__ import annotations

import json

from backend.app import main
from backend.app.db import Database
from backend.app.okx import OkxError


def reset_market_ai_cache():
    with main.market_ai_macro_cache_lock:
        main.market_ai_macro_cache.clear()
    with main.market_ai_outlook_cache_lock:
        main.market_ai_outlook_cache.clear()
    with main.chart_snapshot_cache_lock:
        main.chart_snapshot_cache.clear()


def sample_candles(count: int = 60) -> list[dict[str, str]]:
    rows = []
    for index in range(count):
        close = 100 + index
        rows.append(
            {
                "ts": str(1_700_000_000_000 + index * 60_000),
                "open": str(close - 1),
                "high": str(close + 2),
                "low": str(close - 2),
                "close": str(close),
                "volume": str(1000 + index),
                "volumeQuote": str((1000 + index) * close),
            }
        )
    return rows


def sample_market() -> dict:
    return {
        "instrument": {"instId": "BTC-USDT-SWAP"},
        "ticker": {"last": "120", "change24hPct": "1.2"},
        "technical": {
            "bar": "1m",
            "lastTs": 123,
            "lastClose": "120",
            "trend": "up",
            "recent20High": "122",
            "recent20Low": "100",
            "recent20RangePct": "5",
            "volume": {"context": "normal"},
        },
        "freshness": {"ticker": {"source": "okx", "ts": 111}, "candles": {"source": "okx", "ts": 123}},
        "warnings": [],
    }


def sample_macro() -> dict:
    return {
        "items": [
            {
                "source": "BLS",
                "kind": "cpi",
                "title": "US CPI-U 最新读数",
                "url": "https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0",
                "value": "310.0",
                "previousValue": "309.0",
                "publishedAt": "2026 August",
                "summary": "美国 CPI-U 最新可用读数 2026 August 为 310.0，前值 309.0",
                "official": True,
            }
        ],
        "warnings": [],
        "source": "macro-public",
    }


def test_ai_ticker_prefers_fresh_single_contract_quote_when_bulk_snapshot_is_stale(monkeypatch):
    current = 1_800_000_000_000
    cached = {"instId": "BTC-USDT-SWAP", "bidPx": "99", "askPx": "100", "ts": str(current - 45_000)}
    fresh = {"instId": "BTC-USDT-SWAP", "bidPx": "101", "askPx": "102", "ts": str(current - 1_000)}
    monkeypatch.setattr(main, "now_ms", lambda: current)
    monkeypatch.setattr(main, "cached_tickers", lambda force=False: {"data": [cached], "source": "okx-stale-cache", "ts": current - 45_000})
    monkeypatch.setattr(main.client, "get_ticker", lambda inst_id: fresh)

    ticker, meta = main.ticker_snapshot_for_inst("BTC-USDT-SWAP")

    assert ticker == fresh
    assert meta["source"] == "okx-single-ticker"
    assert meta["ts"] == current - 1_000


def test_ai_ticker_keeps_stale_quote_provenance_when_single_contract_read_fails(monkeypatch):
    current = 1_800_000_000_000
    cached = {"instId": "BTC-USDT-SWAP", "bidPx": "99", "askPx": "100", "ts": str(current - 45_000)}
    monkeypatch.setattr(main, "now_ms", lambda: current)
    monkeypatch.setattr(main, "cached_tickers", lambda force=False: {"data": [cached], "source": "okx-stale-cache", "ts": current - 45_000})

    def unavailable(_inst_id):
        raise OkxError("upstream unavailable")

    monkeypatch.setattr(main.client, "get_ticker", unavailable)
    ticker, meta = main.ticker_snapshot_for_inst("BTC-USDT-SWAP")

    assert ticker == cached
    assert meta["source"] == "okx-stale-cache"


def sample_trading_structure(source: str = "okx-market-stats", ts: int = 456) -> dict:
    return {
        "instId": "BTC-USDT-SWAP",
        "requestedPeriod": "15m",
        "period": "15m",
        "periodFallback": False,
        "source": source,
        "ts": ts,
        "quality": "complete",
        "warnings": [],
        "items": [
            {"key": "longShortAccountRatio", "label": "多空账户", "value": "1.2", "state": "more_long_accounts", "signal": "up", "available": True},
            {"key": "takerVolume", "label": "主动买卖", "value": "62", "state": "active_buying_stronger", "signal": "up", "available": True},
            {"key": "openInterest", "label": "持仓变化", "value": "3.1", "state": "increasing", "signal": "participation", "available": True},
        ],
    }


def sample_price_plan_input(direction: str = "long") -> tuple[dict, list[dict], dict, int]:
    interval = main.CANDLE_BAR_MILLISECONDS["15m"]
    first = 1_800_000_000_000
    signal_close = "102" if direction == "long" else "98"
    signal_high = "102.5" if direction == "long" else "100"
    signal_low = "100" if direction == "long" else "97.5"
    candles = [
        {"ts": str(first + index * interval), "open": "100", "high": "101", "low": "99", "close": "100", "volume": "100", "confirm": "1"}
        for index in range(20)
    ]
    candles.append({"ts": str(first + 20 * interval), "open": "100", "high": signal_high, "low": signal_low, "close": signal_close, "volume": "120", "confirm": "1"})
    candles.append({"ts": str(first + 21 * interval), "open": signal_close, "high": "104", "low": "96", "close": signal_close, "volume": "1", "confirm": "0"})
    current = first + 21 * interval + 1_000
    market = {
        "instrument": {"instId": "BTC-USDT-SWAP", "tickSize": "0.1"},
        "ticker": {"bidPx": "101.2", "askPx": "101.3", "ts": str(current)} if direction == "long" else {"bidPx": "98.7", "askPx": "98.8", "ts": str(current)},
        "freshness": {"ticker": {"ts": current}},
        "pricePlanStructure": {"period": "15m", "items": []},
        "multiTimeframeTrend": {"periods": [{"bar": "1H", "available": True, "trend": "up" if direction == "long" else "down"}]},
    }
    return market, candles, {"source": "okx", "ts": current}, current


def test_market_ai_price_plan_uses_ask_quote_for_long_and_separate_reassessment_level():
    market, candles, meta, current = sample_price_plan_input()
    plan = main.build_market_ai_price_plan(market, candles, meta, current)

    assert plan["direction"] == "long"
    assert plan["status"] == "ready"
    assert plan["rangeHigh"] == "101"
    assert plan["upperReassess"] == "101.1"
    assert plan["entryPrice"] == market["ticker"]["askPx"] == "101.3"
    assert plan["entryBasis"] == "quote_snapshot"
    assert plan["entryQuoteTs"] == current
    assert plan["version"] == 3
    assert plan["stopPrice"] == "98.9"
    assert plan["targetPrice"] == "106.1"
    assert "卖一报价" in plan["priceLogic"]["entry"]
    assert "101.3" in plan["priceLogic"]["entry"]
    assert "最低价 99" in plan["priceLogic"]["stop"]
    assert "98.9" in plan["priceLogic"]["stop"]
    assert "2 × 2.4" in plan["priceLogic"]["target"]
    assert "106.1" in plan["priceLogic"]["target"]
    assert "合计" in plan["priceLogic"]["direction"]
    assert plan["lastClosedTs"] == int(candles[-2]["ts"])
    assert plan["validUntil"] == int(candles[-2]["ts"]) + 2 * main.CANDLE_BAR_MILLISECONDS["15m"]
    assert plan["readOnly"] is True
    market["ticker"]["ts"] = str(current + 2_000)
    assert main.build_market_ai_price_plan(market, candles, meta, current)["quoteFresh"] is True
    market["ticker"]["ts"] = str(current + 6_000)
    assert main.build_market_ai_price_plan(market, candles, meta, current)["status"] == "unavailable"


def test_market_ai_price_plan_short_uses_bid_and_open_candle_does_not_set_entry():
    market, candles, meta, current = sample_price_plan_input("short")
    short = main.build_market_ai_price_plan(market, candles, meta, current)
    assert short["direction"] == "short"
    assert short["status"] == "ready"
    assert short["entryPrice"] == "98.7"
    assert short["stopPrice"] == "101.1"
    assert short["targetPrice"] == "93.9"
    assert "买一报价" in short["priceLogic"]["entry"]
    assert "最高价" in short["priceLogic"]["stop"]
    assert "98.7 − 2 × 2.4" in short["priceLogic"]["target"]

    market, candles, meta, current = sample_price_plan_input()
    candles[-2].update({"high": "101", "low": "99", "close": "100"})
    candles[-1].update({"high": "103", "close": "102"})
    watch = main.build_market_ai_price_plan(market, candles, meta, current)
    assert watch["direction"] == "long"
    assert watch["entryPrice"] == market["ticker"]["askPx"]
    assert watch["priceConditionMet"] is True
    assert watch["status"] == "ready"


def test_market_ai_price_plan_rejects_missing_inputs_and_marks_expiry_or_stale_quote():
    market, candles, meta, current = sample_price_plan_input()
    assert main.build_market_ai_price_plan(market, candles[:20], meta, current)["status"] == "unavailable"
    market["instrument"]["tickSize"] = ""
    assert main.build_market_ai_price_plan(market, candles, meta, current)["entryPrice"] == ""
    market["instrument"]["tickSize"] = "0.1"
    assert main.build_market_ai_price_plan(market, candles, meta, current + 2 * main.CANDLE_BAR_MILLISECONDS["15m"])["status"] == "expired"
    market["ticker"] = {"bidPx": "102.9", "askPx": "103", "ts": str(current)}
    assert main.build_market_ai_price_plan(market, candles, meta, current)["entryPrice"] == "103"
    market["ticker"]["ts"] = str(current - 31_000)
    assert main.build_market_ai_price_plan(market, candles, meta, current)["status"] == "unavailable"
    market["ticker"] = {"bidPx": "101.2", "askPx": "101.35", "ts": str(current)}
    assert main.build_market_ai_price_plan(market, candles, meta, current)["status"] == "unavailable"
    market["ticker"] = {"bidPx": "101.2", "askPx": "101.3"}
    assert main.build_market_ai_price_plan(market, candles, meta, current)["status"] == "unavailable"
    market["ticker"] = {"bidPx": "100", "askPx": "101.3", "ts": str(current)}
    wide = main.build_market_ai_price_plan(market, candles, meta, current)
    assert wide["status"] == "watch"
    assert wide["entryPrice"] == "101.3"
    assert wide["priceConditionMet"] is False


def test_market_ai_price_plan_cache_key_changes_with_15m_levels():
    market = sample_market()
    market["pricePlan"] = {"lastClosedTs": 100, "source": "okx", "status": "watch", "direction": "long", "entryPrice": "101.1"}
    first = main.market_ai_outlook_cache_key(market, sample_macro())
    market["pricePlan"]["entryPrice"] = "101.2"
    assert main.market_ai_outlook_cache_key(market, sample_macro()) != first
    current = main.market_ai_outlook_cache_key(market, sample_macro())
    market["pricePlan"].update({"version": 2, "entryBasis": "quote_snapshot", "entryQuoteTs": 123})
    assert main.market_ai_outlook_cache_key(market, sample_macro()) != current


def test_market_ai_cpi_evidence_normalizes_bls_payload(monkeypatch):
    reset_market_ai_cache()

    def fake_json(url, method="GET", body=None, timeout=8):
        assert "CUUR0000SA0" in url
        assert method == "POST"
        return {
            "Results": {
                "series": [
                    {
                        "data": [
                            {"year": "2026", "periodName": "August", "value": "310.0"},
                            {"year": "2026", "periodName": "July", "value": "309.0"},
                        ]
                    }
                ]
            }
        }

    monkeypatch.setattr(main, "http_json_request", fake_json)

    payload = main.load_cpi_evidence(force=True)

    assert payload["source"] == "bls-cpi"
    assert payload["items"][0]["source"] == "BLS"
    assert payload["items"][0]["value"] == "310.0"
    assert payload["items"][0]["previousValue"] == "309.0"
    assert payload["items"][1]["url"].endswith("/schedule/news_release/cpi.htm")


def test_market_ai_macro_uses_stale_cache_after_provider_failure(monkeypatch):
    reset_market_ai_cache()
    stale_payload = {"items": [main.market_ai_source_item("BLS", "cached", "u", "old", "cpi")], "warnings": []}
    main.market_ai_macro_cache_set("bls-cpi-cu", stale_payload, 100_000)
    monkeypatch.setattr(main, "now_ms", lambda: 100_000 + (main.MARKET_AI_MACRO_CACHE_SECONDS + 10) * 1000)
    monkeypatch.setattr(main, "http_json_request", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("network down")))

    payload = main.load_cpi_evidence(force=True)

    assert payload["source"] == "macro-stale-cache"
    assert payload["items"][0]["title"] == "cached"
    assert any("BLS CPI 刷新失败" in warning for warning in payload["warnings"])


def test_market_ai_macro_no_provider_fallback(monkeypatch):
    reset_market_ai_cache()
    monkeypatch.setattr(main, "http_json_request", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("bls down")))
    monkeypatch.setattr(main, "http_text_request", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("fed down")))

    payload = main.build_market_ai_macro_snapshot(force=True)

    assert payload["source"] == "macro-partial"
    assert any(item["source"] == "BLS" for item in payload["items"])
    assert any(item["source"] == "Federal Reserve" for item in payload["items"])
    assert any("获取失败" in warning for warning in payload["warnings"])


def test_market_ai_market_evidence_caps_candles_and_summarizes(monkeypatch):
    class FakeDatabase:
        def list_instruments(self, query="", limit=200):
            return [{"inst_id": "BTC-USDT-SWAP", "settle_ccy": "USDT", "ct_val": "0.01", "state": "live"}]

        def upsert_candles(self, inst_id, bar, candles):
            self.saved = candles

        def latest_candles(self, inst_id, bar, limit=300):
            return []

    class FakeClient:
        def get_candles(self, inst_id, bar, limit):
            return sample_candles(limit)

        def get_ticker(self, inst_id):
            return None

    reset_market_ai_cache()
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "client", FakeClient())
    monkeypatch.setattr(
        main,
        "cached_tickers",
        lambda force=False: {
            "data": [
                {
                    "instId": "BTC-USDT-SWAP",
                    "last": "160",
                    "open24h": "100",
                    "sodUtc8": "200",
                    "sodUtc0": "180",
                    "high24h": "165",
                    "low24h": "95",
                    "volCcyQuote24h": "2000000",
                }
            ],
            "source": "okx",
            "ts": 200,
            "cacheAgeMs": 0,
        },
    )

    payload = main.build_market_ai_market_evidence("BTC-USDT-SWAP", "1m", 80)

    assert len(payload["candles"]) == main.MARKET_AI_PROMPT_CANDLES
    assert payload["technical"]["candles"] == 80
    assert payload["technical"]["trend"] in {"up", "down", "range", "volatile"}
    assert payload["ticker"]["volume24h"] == "2000000"
    assert payload["ticker"]["change24hPct"] == "60"
    assert payload["warnings"] == []


def test_market_ai_market_evidence_insufficient_data_warns(monkeypatch):
    class FakeDatabase:
        def list_instruments(self, query="", limit=200):
            return []

        def upsert_candles(self, inst_id, bar, candles):
            pass

        def latest_candles(self, inst_id, bar, limit=300):
            return []

    class FakeClient:
        def get_candles(self, inst_id, bar, limit):
            raise OkxError("OKX unavailable")

        def get_ticker(self, inst_id):
            raise OkxError("ticker unavailable")

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "client", FakeClient())
    monkeypatch.setattr(main, "cached_tickers", lambda force=False: {"data": [], "source": "okx-unavailable", "warning": "ticker down", "ts": 0})

    payload = main.build_market_ai_market_evidence("BTC-USDT-SWAP", "1m", 30)

    assert payload["candles"] == []
    assert any("Ticker 快照缺失" in warning for warning in payload["warnings"])
    assert any("K线数据缺失" in warning for warning in payload["warnings"])


def test_market_ai_fixed_trends_use_independent_period_snapshots_and_keep_missing_period_missing(monkeypatch):
    requested = []

    def fake_snapshot(inst_id, bar, limit):
        requested.append((inst_id, bar, limit))
        if bar == "1H":
            return [], {"source": "okx-unavailable", "ts": 10, "cacheAgeMs": None, "warning": "network failure"}
        return sample_candles(80), {"source": "okx", "ts": 10, "cacheAgeMs": 0, "warning": ""}

    monkeypatch.setattr(main, "candle_snapshot_for_inst", fake_snapshot)

    payload = main.build_market_ai_fixed_trends("BTC-USDT-SWAP", "1m")
    periods = {item["key"]: item for item in payload["periods"]}

    assert [bar for _inst, bar, _limit in requested] == ["15m", "1H", "1H", "1D"]
    assert periods["15m"]["available"] is True
    assert periods["15m"]["bar"] == "15m"
    assert periods["15m"]["trend"] != "unavailable"
    assert len(periods["15m"]["evidence"]) == 2
    assert "完整一根 15分钟 K线收在" in periods["15m"]["condition"]
    assert periods["1H"]["available"] is False
    assert periods["1H"]["trendLabel"] == "数据待获取"
    assert "未使用其他周期替代" in periods["1H"]["warning"]
    assert periods["1D"]["bar"] == "1D"
    assert payload["alignmentState"] == "incomplete"


def test_market_ai_fixed_trends_retry_recovers_a_transient_period_failure(monkeypatch):
    requested = []

    def fake_snapshot(inst_id, bar, limit):
        requested.append(bar)
        if bar == "1H" and requested.count("1H") == 1:
            return [], {"source": "okx-unavailable", "warning": "temporary connection failure"}
        return sample_candles(80), {"source": "okx", "warning": ""}

    monkeypatch.setattr(main, "candle_snapshot_for_inst", fake_snapshot)

    payload = main.build_market_ai_fixed_trends("BTC-USDT-SWAP", "15m")
    periods = {item["key"]: item for item in payload["periods"]}

    assert requested == ["15m", "1H", "1H", "1D"]
    assert all(item["available"] for item in periods.values())
    assert periods["1H"]["source"] == "okx"


def test_market_ai_fixed_trends_reuse_matching_chart_snapshot_without_aggregating_other_periods(monkeypatch):
    requested = []

    def fake_snapshot(inst_id, bar, limit):
        requested.append(bar)
        return sample_candles(80), {"source": "okx", "ts": 11, "cacheAgeMs": 0, "warning": ""}

    chart_snapshot = main.create_chart_snapshot("BTC-USDT-SWAP", "15m", sample_candles(80), "okx-ws", snapshot_ts=12)
    monkeypatch.setattr(main, "candle_snapshot_for_inst", fake_snapshot)

    payload = main.build_market_ai_fixed_trends("BTC-USDT-SWAP", "15m", chart_snapshot)
    periods = {item["key"]: item for item in payload["periods"]}

    assert requested == ["1H", "1D"]
    assert periods["15m"]["source"] == "okx-ws"
    assert periods["1H"]["source"] == "okx"
    assert periods["1D"]["source"] == "okx"


def test_market_ai_fixed_trends_do_not_present_expired_cache_as_a_current_period_reading(monkeypatch):
    current = 1_800_000_000_000
    stale = sample_candles(80)
    for item in stale:
        item["ts"] = str(current - 10 * 60 * 60 * 1000)

    monkeypatch.setattr(main, "now_ms", lambda: current)
    payload = main.market_ai_fixed_trend_evidence("1H", "1小时", stale, {"source": "database-cache", "warning": "upstream failed"})

    assert payload["available"] is False
    assert payload["trendLabel"] == "数据待获取"
    assert "缓存已过期" in payload["warning"]
    assert "未使用其他周期替代" in payload["warning"]


def test_market_ai_trading_structure_uses_labeled_supported_period_fallback(monkeypatch):
    def fake_stats(inst_id, requested_period, period, limit, force=False):
        assert (inst_id, requested_period, period, limit) == ("BTC-USDT-SWAP", "1m", "5m", 20)
        return {
            "period": period,
            "source": "okx-market-stats",
            "ts": 123,
            "cacheAgeMs": 0,
            "warnings": [],
            "longShortAccountRatio": {"latest": "0.9", "bias": "more_short_accounts"},
            "takerVolume": {"buySharePct": "42", "dominance": "active_selling_stronger"},
            "openInterest": {"changePct": "2.3", "trend": "increasing"},
        }

    monkeypatch.setattr(main, "cached_market_stats", fake_stats)
    payload = main.market_ai_trading_structure_evidence("BTC-USDT-SWAP", "1m")

    assert payload["period"] == "5m"
    assert payload["periodFallback"] is True
    assert payload["quality"] == "complete"
    assert [item["signal"] for item in payload["items"]] == ["down", "down", "participation"]


def test_market_ai_decision_reference_confirms_and_defers_on_conflict():
    market = sample_market()
    market["tradingStructure"] = sample_trading_structure()
    confirmed = main.market_ai_decision_reference(
        market,
        {"action": "consider_long", "condition": "站稳后观察", "invalidation": "跌破重评"},
        "bullish",
        68,
    )

    assert confirmed["assessment"] == "confirmed"
    assert confirmed["action"] == "consider_long"
    assert confirmed["dataQuality"] == "complete"

    market["tradingStructure"]["items"][1]["state"] = "active_selling_stronger"
    market["tradingStructure"]["items"][1]["signal"] = "down"
    conflict = main.market_ai_decision_reference(
        market,
        {"action": "consider_long", "condition": "站稳后观察", "invalidation": "跌破重评"},
        "bullish",
        68,
    )

    assert conflict["assessment"] == "conflict"
    assert conflict["action"] == "wait_release"
    assert conflict["confidence"] <= 50


def test_market_ai_decision_layers_explain_weak_bias_and_threshold_gaps():
    market = sample_market()
    market["technical"].update({"trend": "range", "changePct": "0.72", "ma5": "121", "ma20": "120", "lastClose": "122"})
    market["tradingStructure"] = sample_trading_structure()
    market["tradingStructure"].update({"requestedPeriod": "1m", "period": "5m", "periodFallback": True})
    market["tradingStructure"]["items"][0].update({"value": "1.0081", "state": "balanced_accounts", "signal": "neutral"})
    market["tradingStructure"]["items"][1].update({"value": "54.93", "state": "balanced_taker_flow", "signal": "neutral"})
    market["tradingStructure"]["items"][2].update({"value": "0.13", "state": "flat", "signal": "neutral"})

    decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 68)

    assert decision["assessment"] == "weak_bias"
    assert decision["directionLayer"] == "weak_bias"
    assert decision["direction"] == "up"
    assert decision["action"] == "wait_release"
    assert decision["chart"]["strength"] == "weak"
    assert decision["periods"] == {"chart": "1m", "structureRequested": "1m", "structureEffective": "5m", "structureFallback": True}
    gaps = {item["key"]: item for item in decision["evidenceGaps"]}
    assert "距偏多还差 0.0419" in gaps["longShortAccountRatio"]["gap"]
    assert "距买方确认还差 0.07pct" in gaps["takerVolume"]["gap"]
    assert "距参与度增加还差 0.87pct" in gaps["openInterest"]["gap"]


def test_market_ai_decision_layers_keep_balanced_data_neutral_not_missing():
    market = sample_market()
    market["technical"].update({"trend": "range", "changePct": "0.02", "ma5": "120", "ma20": "120", "lastClose": "120"})
    market["tradingStructure"] = sample_trading_structure()
    for item, value, state in zip(market["tradingStructure"]["items"], ["1.0081", "54.93", "0.13"], ["balanced_accounts", "balanced_taker_flow", "flat"]):
        item.update({"value": value, "state": state, "signal": "neutral"})

    decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 68)

    assert decision["assessment"] == "insufficient"
    assert decision["directionLayer"] == "neutral"
    assert decision["action"] == "wait_release"
    assert "数据已获取" in decision["summary"]


def test_market_ai_observation_levels_are_snapshot_scoped_and_conditional():
    market = sample_market()
    market["chartSnapshot"] = {"snapshotId": "cs_report_123", "snapshotTs": 789, "bar": "1m"}
    market["tradingStructure"] = sample_trading_structure()

    levels = main.market_ai_observation_levels(market, {"action": "wait_release"})

    assert levels["available"] is True
    assert levels["status"] == "watch"
    assert levels["snapshotId"] == "cs_report_123"
    assert levels["bar"] == "1m"
    assert levels["neutralRange"] == {
        "label": "观望区",
        "low": "100",
        "high": "122",
        "condition": "价格仍在 100 – 122 区间内，暂不形成方向。",
    }
    assert "完成一根 1m K线收在 122 上方" in levels["upper"]["condition"]
    assert "完成一根 1m K线收在 100 下方" in levels["lower"]["condition"]
    assert "市场参与度增加，仅作参与确认，不决定方向" == levels["participationNote"]
    assert levels["currentState"]["status"] == "watch"
    assert "当前：保持观望" == levels["currentState"]["label"]
    assert [candidate["confirmationPrice"] for candidate in levels["candidates"]] == ["122", "100"]
    assert all(candidate["priceMeaning"] == "条件确认价，不是直接成交价。" for candidate in levels["candidates"])
    assert "完整一根 1m K线收在 122 上方" in levels["candidates"][0]["requirements"][0]["detail"]
    assert "盘中触及或影线越过不算确认" in levels["candidates"][0]["requirements"][0]["detail"]
    assert levels["candidates"][0]["status"] == "awaiting_confirmation"
    assert levels["candidates"][0]["missingEvidence"] == []
    assert levels["candidates"][0]["invalidationStatus"] == "return_to_range_invalidates"
    assert "候选方向失效，恢复观望" in levels["candidates"][0]["invalidation"]
    assert "开仓" not in str(levels)
    assert "止损" not in str(levels)


def test_market_ai_observation_levels_do_not_invent_boundaries_or_full_confirmation():
    market = sample_market()
    market["technical"]["recent20High"] = "100"

    unavailable = main.market_ai_observation_levels(market, {"action": "wait_release"})

    assert unavailable["available"] is False
    assert unavailable["status"] == "unavailable"

    market = sample_market()
    market["tradingStructure"] = sample_trading_structure()
    market["tradingStructure"]["quality"] = "partial"
    market["tradingStructure"]["items"][1]["available"] = False
    partial = main.market_ai_observation_levels(market, {"action": "wait_release"})

    assert partial["available"] is True
    assert partial["partialConfirmation"] is True
    assert "不形成完整确认" in partial["upper"]["condition"]
    assert "不形成完整确认" in partial["lower"]["condition"]
    assert all(candidate["statusLabel"] == "缺少完整确认" for candidate in partial["candidates"])
    assert all("补齐可用数据" in candidate["statusDetail"] for candidate in partial["candidates"])


def test_market_ai_observation_levels_include_candidate_specific_evidence_gaps():
    market = sample_market()
    market["technical"].update({"trend": "range", "changePct": "0.72", "ma5": "121", "ma20": "120", "lastClose": "120"})
    market["tradingStructure"] = sample_trading_structure()
    market["tradingStructure"]["items"][1].update({"value": "54.93", "state": "balanced_taker_flow", "signal": "neutral"})
    decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 45)

    levels = main.market_ai_observation_levels(market, decision)

    assert levels["available"] is True
    assert any(item["key"] == "takerVolume" for item in levels["candidates"][0]["missingEvidence"])
    assert any(requirement["label"] == "尚缺确认" for requirement in levels["candidates"][0]["requirements"])


def test_market_ai_scenario_board_prioritizes_rule_score_and_data_limits():
    market = sample_market()
    market["chartSnapshot"] = {"snapshotId": "cs_scenario_123", "snapshotTs": 789, "bar": "15m"}
    market["technical"].update({"bar": "15m", "trend": "range", "changePct": "-0.2", "ma5": "119", "ma20": "120", "lastClose": "120"})
    market["tradingStructure"] = sample_trading_structure()
    market["tradingStructure"]["quality"] = "partial"
    market["tradingStructure"]["items"][0].update({"available": False, "value": "", "signal": "neutral"})
    market["tradingStructure"]["items"][1].update({"value": "38.67", "state": "active_selling_stronger", "signal": "down"})

    decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 58)
    levels = main.market_ai_observation_levels(market, decision)
    board = main.market_ai_scenario_board(market, decision, levels)

    assert decision["confidence"] == 45
    assert board["evidenceScore"] == 45
    assert board["marketState"]["label"] == "价格仍在观察区"
    assert board["marketState"]["strongestClue"]["label"] == "主动买卖"
    assert "主动卖出占优" in board["marketState"]["strongestClue"]["detail"]
    assert board["dataLimitations"] == [{"label": "多空账户", "detail": "本次数据未获取，不能参与完整多空确认。"}]
    assert all(candidate["status"] == "limited" for candidate in board["candidates"])
    assert all(candidate["limitations"][0]["label"] == "多空账户" for candidate in board["candidates"])
    assert "15m K线收在" in board["candidates"][0]["priceCondition"]


def test_market_ai_direction_summary_keeps_unconfirmed_and_limited_states_out_of_direction_calls():
    confirmed_market = sample_market()
    confirmed_market["chartSnapshot"] = {"snapshotId": "cs_direction_up", "snapshotTs": 790, "bar": "15m"}
    confirmed_market["technical"].update({"bar": "15m", "trend": "up", "lastClose": "120"})
    confirmed_market["tradingStructure"] = sample_trading_structure()
    confirmed_decision = main.market_ai_decision_reference(confirmed_market, {"action": "consider_long"}, "bullish", 82)
    confirmed_board = main.market_ai_scenario_board(confirmed_market, confirmed_decision, main.market_ai_observation_levels(confirmed_market, confirmed_decision))
    confirmed_summary = main.market_ai_direction_summary(confirmed_market, confirmed_decision, confirmed_board)

    assert confirmed_summary["headline"] == "偏多观察"
    assert confirmed_summary["state"] == "confirmed"
    assert confirmed_summary["direction"] == "up"
    assert confirmed_summary["confirmationPrice"] == "120"

    bearish_market = sample_market()
    bearish_market["chartSnapshot"] = {"snapshotId": "cs_direction_down", "snapshotTs": 791, "bar": "15m"}
    bearish_market["technical"].update({"bar": "15m", "trend": "down", "lastClose": "120"})
    bearish_market["tradingStructure"] = sample_trading_structure()
    bearish_market["tradingStructure"]["items"][0].update({"value": "0.8", "state": "more_short_accounts", "signal": "down"})
    bearish_market["tradingStructure"]["items"][1].update({"value": "38", "state": "active_selling_stronger", "signal": "down"})
    bearish_decision = main.market_ai_decision_reference(bearish_market, {"action": "consider_short"}, "bearish", 82)
    bearish_board = main.market_ai_scenario_board(bearish_market, bearish_decision, main.market_ai_observation_levels(bearish_market, bearish_decision))
    bearish_summary = main.market_ai_direction_summary(bearish_market, bearish_decision, bearish_board)

    assert bearish_summary["headline"] == "偏空观察"
    assert bearish_summary["state"] == "confirmed"
    assert bearish_summary["direction"] == "down"

    limited_market = sample_market()
    limited_market["chartSnapshot"] = {"snapshotId": "cs_direction_limited", "snapshotTs": 792, "bar": "15m"}
    limited_market["technical"].update({"bar": "15m", "trend": "range", "lastClose": "120"})
    limited_market["tradingStructure"] = sample_trading_structure()
    limited_market["tradingStructure"]["quality"] = "partial"
    limited_market["tradingStructure"]["items"][0].update({"available": False, "value": "", "signal": "neutral"})
    limited_market["tradingStructure"]["items"][1].update({"value": "38", "state": "active_selling_stronger", "signal": "down"})
    limited_decision = main.market_ai_decision_reference(limited_market, {"action": "observe"}, "neutral", 58)
    limited_board = main.market_ai_scenario_board(limited_market, limited_decision, main.market_ai_observation_levels(limited_market, limited_decision))
    limited_board["dataLimitations"] = [*limited_board["dataLimitations"], *limited_board["dataLimitations"]]
    limited_summary = main.market_ai_direction_summary(limited_market, limited_decision, limited_board)

    assert limited_summary["headline"] == "方向暂不可判定"
    assert limited_summary["state"] == "limited"
    assert limited_summary["direction"] == "down"
    assert limited_summary["confirmationPriceLabel"] == "待验证价"
    assert "多空账户" in limited_summary["nextCondition"]
    assert limited_summary["nextCondition"].count("多空账户") == 1


def test_market_ai_direction_summary_labels_weak_matching_evidence_without_calling_it_confirmed():
    market = sample_market()
    market["chartSnapshot"] = {"snapshotId": "cs_direction_weak", "snapshotTs": 793, "bar": "15m"}
    market["technical"].update({"bar": "15m", "trend": "range", "changePct": "-0.2", "ma5": "119", "ma20": "120", "lastClose": "119"})
    market["tradingStructure"] = sample_trading_structure()
    market["tradingStructure"]["items"][0].update({"value": "1", "state": "balanced_accounts", "signal": "neutral"})
    market["tradingStructure"]["items"][1].update({"value": "38", "state": "active_selling_stronger", "signal": "down"})
    market["tradingStructure"]["items"][2].update({"value": "0", "state": "flat", "signal": "neutral"})
    decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 58)
    board = main.market_ai_scenario_board(market, decision, main.market_ai_observation_levels(market, decision))
    summary = main.market_ai_direction_summary(market, decision, board)

    assert decision["assessment"] == "weak_bias"
    assert summary["headline"] == "短线偏空（未确认）"
    assert summary["state"] == "weak_bias"
    assert "主动卖出占优" in summary["metCondition"]
    assert "15m K线收在" in summary["missingCondition"]
    assert "还缺" in summary["missingCondition"]

    market["tradingStructure"]["items"][0].update({"value": "1.2", "state": "more_long_accounts", "signal": "up"})
    conflict_decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 58)
    conflict_board = main.market_ai_scenario_board(market, conflict_decision, main.market_ai_observation_levels(market, conflict_decision))
    conflict_summary = main.market_ai_direction_summary(market, conflict_decision, conflict_board)

    assert conflict_summary["headline"] == "无明确方向"
    assert conflict_summary["state"] == "conflict"


def test_market_ai_outlook_fallback_carries_observation_levels_when_waiting():
    payload = main.fallback_market_ai_outlook(sample_market(), sample_macro())

    assert payload["decision"]["action"] == "wait_release"
    assert payload["observationLevels"]["available"] is True
    assert payload["observationLevels"]["partialConfirmation"] is True


def test_market_ai_confidence_explanation_separates_available_data_from_direction_confirmation():
    market = sample_market()
    market["technical"]["trend"] = "range"
    market["tradingStructure"] = sample_trading_structure()
    market["tradingStructure"]["items"][0].update({"value": "1.0223", "state": "balanced_accounts", "signal": "neutral"})
    market["tradingStructure"]["items"][2].update({"value": "-0.08", "state": "flat", "signal": "neutral"})
    decision = main.market_ai_decision_reference(market, {"action": "observe"}, "neutral", 35)

    explanation = main.market_ai_confidence_explanation(market, "metric-fallback", 35, decision, "LLM 未启用，已使用指标降级分析。")

    assert explanation["referenceValue"] == 35
    assert explanation["sourceLabel"] == "指标降级"
    assert explanation["dataAvailability"]["label"] == "交易数据已获取"
    assert explanation["confirmation"]["label"] == "证据待确认"
    assert explanation["evidence"][0]["contribution"] == "当前不提供方向确认"
    assert explanation["evidence"][1]["contribution"] == "有方向，但图表尚未确认"
    assert "不代表价格涨跌概率" in explanation["referenceMeaning"]


def test_market_ai_fallback_sanitizes_llm_failure_details_from_report_payload():
    payload = main.fallback_market_ai_outlook(sample_market(), sample_macro(), "LLM 分析失败，已使用指标降级分析：token=private-value")

    serialized = str(payload)
    assert payload["confidenceExplanation"]["sourceReason"] == "LLM 分析失败，已使用规则化指标解读。"
    assert "private-value" not in serialized
    assert "token=" not in serialized


def test_market_ai_cache_key_tracks_trading_structure_values_not_display_source():
    market = sample_market()
    market["tradingStructure"] = sample_trading_structure("okx-market-stats", 456)
    first = main.market_ai_outlook_cache_key(market, sample_macro())
    market["tradingStructure"]["source"] = "market-stats-cache"
    second = main.market_ai_outlook_cache_key(market, sample_macro())
    market["tradingStructure"]["items"][1]["value"] = "63"
    third = main.market_ai_outlook_cache_key(market, sample_macro())

    assert first == second
    assert second != third


def test_market_ai_cache_key_tracks_each_multi_timeframe_snapshot_identity():
    market = sample_market()
    market["multiTimeframeTrend"] = {
        "periods": [
            {"key": "15m", "bar": "15m", "status": "available", "source": "okx", "lastCandleTs": 100},
            {"key": "1H", "bar": "1H", "status": "available", "source": "okx", "lastCandleTs": 200},
            {"key": "1D", "bar": "1D", "status": "available", "source": "okx", "lastCandleTs": 300},
        ]
    }

    first = main.market_ai_outlook_cache_key(market, sample_macro())
    market["multiTimeframeTrend"]["periods"][2]["lastCandleTs"] = 301
    second = main.market_ai_outlook_cache_key(market, sample_macro())

    assert first != second


def test_market_ai_profile_is_prompted_before_evidence_and_invalidates_cache():
    profile = main.compile_okx_market_reading_context()["metadata"]
    prompt = json.loads(main.market_ai_outlook_prompt(sample_market(), sample_macro()))

    assert prompt["skillProfile"]["id"] == "okx-market-reading"
    assert "okx_cli_execution" in prompt["skillProfile"]["prohibitedCapabilities"]
    assert prompt["skillRules"]
    assert list(prompt).index("skillRules") < list(prompt).index("macro_evidence")
    first = main.market_ai_outlook_cache_key(sample_market(), sample_macro(), profile)
    changed = {**profile, "contentHash": "changed"}
    assert first != main.market_ai_outlook_cache_key(sample_market(), sample_macro(), changed)


def test_market_ai_fallback_carries_readonly_profile_metadata():
    payload = main.fallback_market_ai_outlook(sample_market(), sample_macro())

    assert payload["analysisProfile"]["id"] == "okx-market-reading"
    assert payload["analysisProfile"]["dataPolicy"] == "public-read-only"
    assert payload["analysisProfile"]["upstream"]["license"] == "MIT"


def test_market_ai_invalid_profile_never_calls_llm(monkeypatch):
    monkeypatch.setattr(main, "compile_okx_market_reading_context", lambda: (_ for _ in ()).throw(ValueError("invalid")))
    monkeypatch.setattr(main, "llm_chat_completion", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not call")))

    payload = main.run_market_ai_outlook(sample_market(), sample_macro())

    assert payload["status"] == "fallback"
    assert payload["analysisProfile"]["status"] == "invalid"
    assert any("规则无效" in warning for warning in payload["warnings"])


def test_market_ai_usage_records_profile_metadata(monkeypatch):
    captured = {}

    class FakeDatabase:
        def insert_llm_usage_log(self, row):
            captured.update(row)
            return {"id": 1, **row}

    monkeypatch.setattr(main, "database", FakeDatabase())
    profile = main.compile_okx_market_reading_context()["metadata"]
    main.record_llm_usage_log(
        {"provider": "custom", "model": "model", "mode": "review"},
        "request",
        "market_ai_outlook",
        "success",
        {},
        1,
        20,
        context={"inst_id": "BTC-USDT-SWAP", "bar": "1m", "analysis_profile": profile},
    )

    assert captured["profile_id"] == "okx-market-reading"
    assert captured["profile_version"] == 3
    assert captured["profile_hash"] == profile["contentHash"]


def test_chart_snapshot_is_bounded_identifiable_and_reused_by_ai_evidence(monkeypatch):
    reset_market_ai_cache()
    current = 1_700_000_000_000 + 240 * 60_000
    monkeypatch.setattr(main, "now_ms", lambda: current)
    snapshot = main.create_chart_snapshot("BTC-USDT-SWAP", "1m", sample_candles(240), "okx-ws", snapshot_ts=current)

    assert snapshot["metadata"]["snapshotId"].startswith("cs_")
    assert snapshot["metadata"]["candleCount"] == main.CHART_SNAPSHOT_CANDLE_LIMIT
    assert snapshot["metadata"]["lastCandleTs"] == int(snapshot["candles"][-1]["ts"])
    assert snapshot["metadata"]["complete"] is True

    monkeypatch.setattr(main, "find_instrument", lambda inst_id: {"inst_id": inst_id, "settle_ccy": "USDT"})
    monkeypatch.setattr(main, "ticker_snapshot_for_inst", lambda inst_id: ({"last": "300", "open24h": "200"}, {"source": "okx", "ts": current, "warning": ""}))
    evidence = main.build_market_ai_market_evidence("BTC-USDT-SWAP", "1m", 120, snapshot)

    assert evidence["chartSnapshot"]["snapshotId"] == snapshot["metadata"]["snapshotId"]
    assert evidence["technical"]["candles"] == main.CHART_SNAPSHOT_CANDLE_LIMIT
    assert int(evidence["technical"]["lastTs"]) == snapshot["metadata"]["lastCandleTs"]


def test_market_ai_rejects_missing_expired_and_mismatched_chart_snapshots(monkeypatch):
    reset_market_ai_cache()
    current = 1_700_000_000_000 + 120 * 60_000
    monkeypatch.setattr(main, "now_ms", lambda: current)
    snapshot = main.create_chart_snapshot("BTC-USDT-SWAP", "1m", sample_candles(120), "okx", snapshot_ts=current)

    missing = main.cached_market_ai_outlook(main.MarketAiOutlookRequest(instId="BTC-USDT-SWAP", bar="1m"))
    mismatch = main.cached_market_ai_outlook(main.MarketAiOutlookRequest(instId="ETH-USDT-SWAP", bar="1m", snapshotId=snapshot["metadata"]["snapshotId"]))

    assert missing["snapshotRequired"] is True
    assert mismatch["snapshotRequired"] is True
    assert "不一致" in mismatch["detail"]


def test_market_ai_rejects_a_chart_snapshot_whose_candles_have_become_stale(monkeypatch):
    reset_market_ai_cache()
    current = 1_700_000_000_000 + 120 * 60_000
    monkeypatch.setattr(main, "now_ms", lambda: current)
    snapshot = main.create_chart_snapshot("BTC-USDT-SWAP", "1m", sample_candles(120), "okx", snapshot_ts=current)
    monkeypatch.setattr(main, "now_ms", lambda: current + 4 * 60_000)

    payload = main.cached_market_ai_outlook(
        main.MarketAiOutlookRequest(instId="BTC-USDT-SWAP", bar="1m", snapshotId=snapshot["metadata"]["snapshotId"])
    )

    assert payload["snapshotRequired"] is True
    assert "尚未更新" in payload["detail"]


def test_market_ai_outlook_missing_config_falls_back(monkeypatch):
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})

    payload = main.run_market_ai_outlook(sample_market(), sample_macro())

    assert payload["status"] == "fallback"
    assert payload["source"] == "metric-fallback"
    assert any("LLM 未启用" in warning for warning in payload["warnings"])


def test_market_ai_outlook_success_normalizes_llm_json(monkeypatch):
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "provider": "custom", "model": "test-model", "baseUrl": "http://llm", "apiKey": "k", "temperature": 0.2, "maxTokens": 800, "timeoutSeconds": 5},
    )
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *args, **kwargs: {
            "content": '{"stance":"bullish","confidence":68,"summary":"偏多参考","overall":{"view":"偏多参考","confidence":66,"summary":"多周期略偏强，仅供阅读参考"},"horizons":[{"key":"15m","bias":"震荡偏强","confidence":54,"summary":"短线量能正常","watch":["关注120上方延续"],"risk":"短线噪音大"},{"key":"1h","bias":"偏多参考","confidence":61,"summary":"小时级结构偏强","watch":["关注量能"],"risk":"回落需重评"},{"key":"today","bias":"震荡观察","confidence":46,"summary":"日内仍受宏观影响","watch":["关注CPI"],"risk":"宏观不确定"}],"report":{"keyFactors":["CPI 已纳入观察"],"focus":["关注价格区间"],"reassess":["跌破100"],"riskNotes":["波动风险"]},"macro":{"bias":"neutral","drivers":["CPI 已纳入观察"],"uncertainty":"等待下一次发布"},"technical":{"trend":"up","keyLevels":["120"],"volumeRead":"正常","notes":["站上均线"]},"suggestion":{"action":"consider_long","condition":"放量站稳后观察","invalidation":"跌破100","riskNotes":["波动风险"]},"warnings":[]}',
            "usage_log": {"id": 7, "prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "request_id": "req",
            "duration_ms": 12,
            "finish_reason": "stop",
        },
    )

    payload = main.run_market_ai_outlook(sample_market(), sample_macro())

    assert payload["status"] == "ok"
    assert payload["source"] == "llm-market-ai-outlook"
    assert payload["stance"] == "bullish"
    assert payload["overall"]["view"] == "偏多参考"
    assert [row["key"] for row in payload["horizons"]] == ["15m", "1h", "today"]
    assert payload["horizons"][0]["summary"] == "短线量能正常"
    assert payload["horizons"][1]["watch"] == ["关注量能"]
    assert payload["report"]["focus"] == ["关注价格区间"]
    assert payload["suggestion"]["action"] == "consider_long"
    assert payload["usage_log_id"] == 7


def test_market_ai_outlook_invalid_json_falls_back(monkeypatch):
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": True, "provider": "custom", "model": "m", "baseUrl": "u", "apiKey": "k", "temperature": 0.2, "maxTokens": 800, "timeoutSeconds": 5})
    monkeypatch.setattr(main, "llm_chat_completion", lambda *args, **kwargs: {"content": "not json"})

    payload = main.run_market_ai_outlook(sample_market(), sample_macro())

    assert payload["status"] == "fallback"
    assert any("LLM 分析失败" in warning for warning in payload["warnings"])


def test_market_ai_outlook_cache_reuse_and_force_refresh(monkeypatch, tmp_path):
    reset_market_ai_cache()
    sample_db = Database(f"sqlite:///{tmp_path / 'samples.sqlite3'}")
    sample_db.init()
    monkeypatch.setattr(main, "database", sample_db)
    calls = {"count": 0}
    current = 1_700_000_000_000 + 120 * 60_000
    monkeypatch.setattr(main, "now_ms", lambda: current)
    monkeypatch.setattr(main, "build_market_ai_macro_snapshot", lambda force=False: sample_macro())
    snapshot = main.create_chart_snapshot("BTC-USDT-SWAP", "1m", sample_candles(120), "okx", snapshot_ts=current)
    monkeypatch.setattr(main, "build_market_ai_market_evidence", lambda inst_id, bar, limit, chart_snapshot: sample_market())
    monkeypatch.setattr(main, "market_ai_trading_structure_evidence", lambda inst_id, bar: sample_trading_structure())
    monkeypatch.setattr(main, "market_ai_plan_candles", lambda inst_id, bar, chart_snapshot: ([], {"source": "test"}))
    monkeypatch.setattr(main, "build_market_ai_fixed_trends", lambda inst_id, bar, chart_snapshot, plan_candles=None: {"version": 1, "periods": [], "alignment": "", "alignmentState": "incomplete"})

    def fake_run(market, macro):
        calls["count"] += 1
        payload = main.fallback_market_ai_outlook(market, macro)
        payload["summary"] = f"run {calls['count']}"
        return payload

    monkeypatch.setattr(main, "run_market_ai_outlook", fake_run)

    first = main.cached_market_ai_outlook(main.MarketAiOutlookRequest(instId="BTC-USDT-SWAP", bar="1m", limit=120, snapshotId=snapshot["metadata"]["snapshotId"]))
    second = main.cached_market_ai_outlook(main.MarketAiOutlookRequest(instId="BTC-USDT-SWAP", bar="1m", limit=120, snapshotId=snapshot["metadata"]["snapshotId"]))
    third = main.cached_market_ai_outlook(main.MarketAiOutlookRequest(instId="BTC-USDT-SWAP", bar="1m", limit=120, snapshotId=snapshot["metadata"]["snapshotId"], forceAnalysis=True))

    assert calls["count"] == 2
    assert first["summary"] == "run 1"
    assert second["cached"] is True
    assert third["summary"] == "run 2"


def test_market_ai_outlook_fallback_explains_current_chart_without_future_horizons():
    payload = main.fallback_market_ai_outlook(sample_market(), sample_macro())

    assert payload["overall"]["view"] == "偏多参考"
    assert payload["horizons"] == []
    assert payload["report"]["keyFactors"]
    assert "仅供" in payload["report"]["riskNotes"][0] or payload["report"]["riskNotes"]


def test_market_ai_outlook_filters_prohibited_wording():
    payload = main.normalize_market_ai_outlook(
        {
            "stance": "bullish",
            "confidence": 88,
            "summary": "必须买入，保证盈利",
            "suggestion": {"action": "consider_long", "condition": "必须做多", "invalidation": "跌破失效", "riskNotes": ["立即下单"]},
        },
        sample_market(),
        sample_macro(),
        {"provider": "custom", "model": "m"},
        {"usage_log": {}, "request_id": "r", "duration_ms": 1, "finish_reason": "stop"},
    )

    assert "必须买入" not in payload["summary"]
    assert "必须做多" not in payload["suggestion"]["condition"]
    assert "立即下单" not in payload["suggestion"]["riskNotes"][0]


def test_market_ai_outlook_omits_missing_or_unsupported_forecast_horizons():
    payload = main.normalize_market_ai_outlook(
        {
            "stance": "neutral",
            "confidence": 50,
            "summary": "区间内观察",
            "horizons": [
                {"key": "1h", "bias": "range", "confidence": 40, "summary": "小时级区间内整理", "watch": ["关注近20根区间"]},
                {"key": "tomorrow", "bias": "bullish", "summary": "不应返回"},
            ],
        },
        sample_market(),
        sample_macro(),
        {"provider": "custom", "model": "m"},
        {"usage_log": {}, "request_id": "r", "duration_ms": 1, "finish_reason": "stop"},
    )

    assert [row["key"] for row in payload["horizons"]] == ["1h"]
    assert payload["horizons"][0]["label"] == "未来1小时"
