import re

import pytest

from backend.app import main


def radar_candles(base: int = 100, count: int = 40):
    rows = []
    for index in range(count):
        open_price = base + index
        close_price = open_price + (2 if index % 2 == 0 else -1)
        high = max(open_price, close_price) + 3
        low = min(open_price, close_price) - 3
        rows.append(
            {
                "ts": str(1000 + index),
                "open": str(open_price),
                "high": str(high),
                "low": str(low),
                "close": str(close_price),
                "volume": str(100 + index),
            }
        )
    return rows


def radar_instrument(inst_id="BTC-USDT-SWAP", state="live", settle_ccy="USDT"):
    return {
        "inst_id": inst_id,
        "inst_family": inst_id.replace("-SWAP", ""),
        "settle_ccy": settle_ccy,
        "state": state,
        "tick_sz": "0.1",
        "lot_sz": "1",
        "ct_val": "0.01",
    }


def radar_ticker(inst_id="BTC-USDT-SWAP", volume="100000000", last="120"):
    return {
        "instId": inst_id,
        "last": last,
        "open24h": "100",
        "high24h": "130",
        "low24h": "90",
        "volCcyQuote24h": volume,
    }


def radar_turnover_candles(values, confirmed="1"):
    return [
        {
            "ts": str(1000 + index),
            "open": "100",
            "high": "102",
            "low": "99",
            "close": "101",
            "volume": str(value),
            "volumeQuote": str(value),
            "confirm": confirmed if isinstance(confirmed, str) else confirmed[index],
        }
        for index, value in enumerate(values)
    ]


def test_radar_liquidity_prefers_quote_turnover_and_labels_fallbacks():
    quote = main.radar_liquidity({"volCcyQuote24h": "12000000", "volCcy24h": "99", "vol24h": "88"}, "USDT")
    estimated = main.radar_liquidity({"volCcy24h": "99", "last": "2"}, "USDT")
    base = main.radar_liquidity({"volCcy24h": "99", "vol24h": "88"}, "USDT")
    contracts = main.radar_liquidity({"vol24h": "88"}, "USDT")

    assert quote["value"] == main.Decimal("12000000")
    assert quote["basis"] == "quote_turnover"
    assert quote["unit"] == "USDT"
    assert quote["confidence"] == "high"
    assert quote["comparable"] is True

    assert estimated["value"] == main.Decimal("198")
    assert estimated["basis"] == "estimated_quote_turnover"
    assert estimated["unit"] == "USDT"
    assert estimated["confidence"] == "medium"
    assert estimated["comparable"] is True

    assert base["basis"] == "base_volume"
    assert base["confidence"] == "medium"
    assert base["comparable"] is False

    assert contracts["basis"] == "contract_volume"
    assert contracts["unit"] == "张"
    assert contracts["confidence"] == "low"
    assert contracts["comparable"] is False


def test_radar_scoring_is_deterministic():
    instrument = radar_instrument()
    ticker = radar_ticker()
    candles = radar_candles()

    first = main.score_radar_contract(instrument, ticker, candles, main.Decimal("1000000"))
    second = main.score_radar_contract(instrument, ticker, candles, main.Decimal("1000000"))

    assert first["scores"] == second["scores"]
    assert first["scores"]["opportunity"] > 0
    assert first["liquidity"]["basis"] == "quote_turnover"
    assert first["tradabilityStatus"] == "playable"
    assert first["entryAssessment"]["status"] in {"ready", "watch", "wait", "avoid"}
    assert any("24h 振幅" in driver for driver in first["entryAssessment"]["drivers"])
    assert first["riskLevel"] in {"low", "medium", "high"}


def test_radar_change24h_uses_rolling_open_not_daily_open_fields():
    ticker = radar_ticker(last="120")
    ticker["sodUtc8"] = "150"
    ticker["sodUtc0"] = "140"

    result = main.score_radar_contract(radar_instrument(), ticker, radar_candles(), main.Decimal("1000000"))

    assert result["change24hPct"] == "20"


def test_radar_one_hour_turnover_uses_four_latest_confirmed_quote_candles():
    candles = radar_turnover_candles([10, 20, 30, 40, 500], ["1", "1", "1", "1", "0"])

    result = main.score_radar_contract(
        radar_instrument(), radar_ticker(), candles, main.Decimal("1000000")
    )

    assert result["turnover"]["oneHour"]["value"] == "100"
    assert result["turnover"]["oneHour"]["candleCount"] == 4
    assert result["turnover"]["oneHour"]["comparable"] is True


def test_radar_one_hour_turnover_does_not_estimate_incomplete_candles():
    result = main.score_radar_contract(
        radar_instrument(), radar_ticker(), radar_turnover_candles([10, 20, 30]), main.Decimal("1000000")
    )

    one_hour = result["turnover"]["oneHour"]
    assert one_hour["value"] == ""
    assert one_hour["comparable"] is False
    assert "四根" in one_hour["warning"]


def test_radar_refreshes_legacy_candle_cache_without_quote_turnover(monkeypatch):
    cached = radar_candles(count=40)
    fresh = radar_turnover_candles([10, 20, 30, 40, 50])

    class FakeDatabase:
        def __init__(self):
            self.saved = []

        def latest_candles(self, *_args):
            return cached

        def upsert_candles(self, *args):
            self.saved.append(args)

    fake_database = FakeDatabase()
    monkeypatch.setattr(main, "database", fake_database)
    monkeypatch.setattr(main.client, "get_candles", lambda *_args: fresh)

    assert main.radar_candles("BTC-USDT-SWAP", "15m", 80) == fresh
    assert fake_database.saved


def test_radar_uses_history_candles_when_latest_candles_response_is_incomplete(monkeypatch):
    fresh = radar_turnover_candles([10, 20, 30, 40, 50])

    class FakeDatabase:
        def __init__(self):
            self.saved = []

        def latest_candles(self, *_args):
            return []

        def upsert_candles(self, *args):
            self.saved.append(args)

    fake_database = FakeDatabase()
    monkeypatch.setattr(main, "database", fake_database)
    monkeypatch.setattr(
        main.client,
        "get_candles",
        lambda *_args: (_ for _ in ()).throw(main.OkxError("IncompleteRead(0 bytes read)")),
    )
    calls = []

    def history_candles(inst_id, bar, limit):
        calls.append((inst_id, bar, limit))
        return fresh

    monkeypatch.setattr(main.client, "get_history_candles", history_candles)

    assert main.radar_candles("BTC-USDT-SWAP", "15m", 80) == fresh
    assert calls == [("BTC-USDT-SWAP", "15m", 80)]
    assert fake_database.saved


def test_radar_24h_scan_reuses_sufficient_legacy_candles_without_quote_turnover(monkeypatch):
    cached = radar_candles(count=40)

    class FakeDatabase:
        def latest_candles(self, *_args):
            return cached

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(
        main.client,
        "get_candles",
        lambda *_args: pytest.fail("24-hour ordering must not refresh candles only to fill one-hour turnover"),
    )

    assert main.radar_candles(
        "BTC-USDT-SWAP", "15m", 80, require_hourly_quote_turnover=False
    ) == cached


def test_radar_reuses_snake_case_db_candles_without_okx_refresh(monkeypatch):
    """Postgres/SQLite rows use volume_quote; downstream logic reads volumeQuote.

    A complete cached 15m window must be reused as-is so a scan does not re-hit
    OKX for every candidate (which causes 150s gateway timeouts when the
    upstream is unreachable).
    """
    cached = [
        {
            "ts": str(1000 + index),
            "open": "100",
            "high": "102",
            "low": "99",
            "close": "101",
            "volume": str(100 + index),
            "volume_quote": str(1000 + index),
            "volume_ccy": str(10 + index),
            "confirm": "1",
        }
        for index in range(40)
    ]

    class FakeDatabase:
        def latest_candles(self, *_args):
            return cached

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(
        main.client,
        "get_candles",
        lambda *_args: pytest.fail("complete snake_case cache must not trigger an OKX refresh"),
    )

    rows = main.radar_candles("BTC-USDT-SWAP", "15m", 80)
    assert len(rows) == 40
    assert rows[-1]["volumeQuote"] == "1039"

    turnover = main.radar_turnover_window(rows, {"comparable": True, "unit": "USDT"})
    assert turnover["comparable"] is True
    assert main.Decimal(turnover["value"]) == main.Decimal("4150")


def test_radar_entry_assessment_uses_volume_and_fluctuation():
    ticker = radar_ticker("MID-USDT-SWAP", volume="80000000", last="104")
    ticker["open24h"] = "100"
    ticker["high24h"] = "108"
    ticker["low24h"] = "98"

    result = main.score_radar_contract(
        radar_instrument("MID-USDT-SWAP"),
        ticker,
        [
            {"ts": str(1000 + index), "open": "100", "high": "102", "low": "99", "close": "101", "volume": str(200 + index)}
            for index in range(40)
        ],
        main.Decimal("1000000"),
    )

    assert result["tradabilityStatus"] == "playable"
    assert result["entryAssessment"]["status"] == "ready"
    assert result["entryAssessment"]["label"] == "可入手观察"
    assert "成交量和浮动" in result["entryAssessment"]["summary"]


def test_radar_sideways_condition_does_not_become_a_hidden_structure_risk_penalty():
    sideways_candles = [
        {
            "ts": str(1000 + index),
            "open": "100",
            "high": "101",
            "low": "99",
            "close": "100.15" if index % 2 else "99.85",
            "volume": "1000",
        }
        for index in range(40)
    ]
    ticker = radar_ticker("RANGE-USDT-SWAP", volume="100000000", last="100")
    ticker["high24h"] = "103"
    ticker["low24h"] = "98"

    result = main.score_radar_contract(
        radar_instrument("RANGE-USDT-SWAP"), ticker, sideways_candles, main.Decimal("1000000")
    )

    assert result["riskLevel"] == "low"
    assert result["scores"]["riskPenalty"] == 0
    assert result["marketCondition"]["key"] == "range"
    assert result["marketCondition"]["label"] == "横盘震荡"
    assert any("避免追突破" in warning for warning in result["warnings"])


def test_radar_low_volume_and_missing_candles_are_penalized():
    result = main.score_radar_contract(
        radar_instrument("LOW-USDT-SWAP"),
        radar_ticker("LOW-USDT-SWAP", volume="1000"),
        [],
        main.Decimal("1000000"),
    )

    assert result["scores"]["riskPenalty"] >= 50
    assert result["riskLevel"] == "high"
    assert result["tradabilityStatus"] == "watch_only"
    assert result["entryAssessment"]["status"] == "watch"
    assert any("成交量" in warning for warning in result["warnings"])
    assert any("K 线" in warning for warning in result["warnings"])


def test_radar_fallback_volume_is_watch_only_lower_confidence():
    ticker = radar_ticker()
    ticker.pop("volCcyQuote24h")
    ticker["volCcy24h"] = "999999999"
    ticker.pop("last")

    result = main.score_radar_contract(radar_instrument(), ticker, radar_candles(), main.Decimal("1000000"))

    assert result["liquidity"]["basis"] == "base_volume"
    assert result["liquidity"]["confidence"] == "medium"
    assert result["liquidity"]["comparable"] is False
    assert result["tradabilityStatus"] == "watch_only"
    assert result["entryAssessment"]["status"] == "watch"
    assert any("统一成交额口径" in warning for warning in result["warnings"])


def test_radar_filters_non_live_instruments():
    request = main.RadarScanRequest(settlement="usdt")

    assert main.radar_filter_instrument(radar_instrument(state="live"), request) is True
    assert main.radar_filter_instrument(radar_instrument(state="suspend"), request) is False


def test_radar_scan_returns_ranked_candidates(monkeypatch):
    monkeypatch.setattr(
        main,
        "radar_instruments",
        lambda: [
            radar_instrument("BTC-USDT-SWAP"),
            radar_instrument("DOGE-USDT-SWAP"),
            radar_instrument("OLD-USDT-SWAP", state="suspend"),
        ],
    )
    monkeypatch.setattr(
        main,
        "cached_tickers",
        lambda force=False: {
            "data": [
                radar_ticker("BTC-USDT-SWAP", volume="100000000", last="120"),
                radar_ticker("DOGE-USDT-SWAP", volume="300000000", last="12"),
                radar_ticker("OLD-USDT-SWAP", volume="900000000", last="9"),
            ]
        },
    )
    monkeypatch.setattr(
        main,
        "radar_candles",
        lambda inst_id, bar, limit, **_kwargs: radar_candles(10 if inst_id.startswith("DOGE") else 100),
    )
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})

    payload = main.build_radar_scan(main.RadarScanRequest(limit=10, candidateLimit=10, explain=True))

    assert [item["instId"] for item in payload["data"]] == ["DOGE-USDT-SWAP", "BTC-USDT-SWAP"]
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["returned"] == 2
    assert all("scores" in item for item in payload["data"])
    assert all("direction" in item and "entryZone" in item for item in payload["data"])


def test_radar_default_sort_uses_one_hour_turnover_and_24h_is_explicit(monkeypatch):
    monkeypatch.setattr(
        main,
        "radar_instruments",
        lambda: [radar_instrument("FAST-USDT-SWAP"), radar_instrument("SLOW-USDT-SWAP")],
    )
    monkeypatch.setattr(
        main,
        "cached_tickers",
        lambda force=False: {
            "data": [
                radar_ticker("FAST-USDT-SWAP", volume="100000000", last="100"),
                radar_ticker("SLOW-USDT-SWAP", volume="300000000", last="100"),
            ]
        },
    )
    monkeypatch.setattr(
        main,
        "radar_candles",
        lambda inst_id, _bar, _limit, **_kwargs: radar_turnover_candles(
            [40, 40, 40, 40] if inst_id.startswith("FAST") else [10, 10, 10, 10]
        ),
    )

    hourly = main.build_radar_scan(main.RadarScanRequest(limit=10, candidateLimit=10))
    daily = main.build_radar_scan(main.RadarScanRequest(limit=10, candidateLimit=10, sortBy="turnover_24h"))

    assert hourly["sort"]["key"] == "turnover_1h"
    assert hourly["data"][0]["instId"] == "FAST-USDT-SWAP"
    assert daily["sort"]["key"] == "turnover_24h"
    assert daily["data"][0]["instId"] == "SLOW-USDT-SWAP"
    assert "候选池" in hourly["sort"]["candidateScope"]
    assert hourly["rankings"]["turnover_1h"][0]["instId"] == "FAST-USDT-SWAP"
    assert hourly["rankings"]["turnover_24h"][0]["instId"] == "SLOW-USDT-SWAP"
    assert daily["rankings"] == hourly["rankings"]


def test_radar_recovers_transient_candle_failure_before_showing_warning(monkeypatch):
    monkeypatch.setattr(main, "radar_instruments", lambda: [radar_instrument("BTC-USDT-SWAP")])
    monkeypatch.setattr(
        main,
        "cached_tickers",
        lambda force=False: {"data": [radar_ticker("BTC-USDT-SWAP", volume="100000000", last="100")]},
    )
    calls = []

    def flaky_candles(inst_id, _bar, _limit, *, require_hourly_quote_turnover=True):
        calls.append((inst_id, require_hourly_quote_turnover))
        if len(calls) == 1:
            raise main.OkxError("IncompleteRead(0 bytes read)")
        return radar_turnover_candles([10, 20, 30, 40])

    monkeypatch.setattr(main, "radar_candles", flaky_candles)

    payload = main.build_radar_scan(main.RadarScanRequest(limit=10, candidateLimit=10))

    assert payload["warning"] == ""
    assert payload["data"][0]["instId"] == "BTC-USDT-SWAP"
    assert calls == [("BTC-USDT-SWAP", True), ("BTC-USDT-SWAP", True)]


def test_radar_scan_cache_key_is_shared_by_turnover_sort_and_hides_transport_error():
    hourly = main.RadarScanRequest()
    daily = main.RadarScanRequest(sortBy="turnover_24h")

    assert main.radar_request_key(hourly) == main.radar_request_key(daily)
    warning = main.radar_refresh_warning("BTC-USDT-SWAP", main.OkxError("IncompleteRead(0 bytes read)"))
    assert "IncompleteRead" not in warning
    assert "缓存或降级数据" in warning
    assert main.radar_refresh_warning_summary([warning, warning]).startswith("2 个合约")


def test_radar_cache_reuses_one_dual_ranking_snapshot_for_each_display_sort(monkeypatch):
    stored = {}
    calls = {"count": 0}

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored.get(key)

        def set_app_setting(self, key, value, ts):
            stored[key] = value

    hourly_row = {"instId": "FAST-USDT-SWAP", "scores": {}, "metrics": {}, "turnover": {}, "liquidity": {}}
    daily_row = {"instId": "SLOW-USDT-SWAP", "scores": {}, "metrics": {}, "turnover": {}, "liquidity": {}}

    def build(request):
        calls["count"] += 1
        return {
            "data": [hourly_row],
            "rankings": {"turnover_1h": [hourly_row], "turnover_24h": [daily_row]},
            "filters": request.model_dump(),
            "sort": {"key": request.sortBy, "label": main.radar_sort_label(request.sortBy), "legacy": False},
            "summary": {"total": 2, "candidates": 2, "returned": 1, "explained": 0},
            "marketSummaries": {"turnover_1h": {"leaders": [hourly_row]}, "turnover_24h": {"leaders": [daily_row]}},
            "warning": "",
        }

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "now_ms", lambda: 100000)
    monkeypatch.setattr(main, "build_radar_scan", build)
    with main.radar_cache_lock:
        main.radar_cache["payload"] = None
        main.radar_cache["ts"] = 0
        main.radar_cache["cacheKey"] = ""

    first = main.cached_radar_scan(main.RadarScanRequest(), force=True)
    second = main.cached_radar_scan(main.RadarScanRequest(sortBy="turnover_24h"), force=False)

    assert calls["count"] == 1
    assert first["data"][0]["instId"] == "FAST-USDT-SWAP"
    assert second["source"] == "radar-cache"
    assert second["sort"]["key"] == "turnover_24h"
    assert second["data"][0]["instId"] == "SLOW-USDT-SWAP"
    assert second["marketSummary"]["leaders"][0]["instId"] == "SLOW-USDT-SWAP"


def test_radar_analysis_cache_identity_keeps_turnover_sort_context():
    payload = {
        "data": [{"instId": "BTC-USDT-SWAP"}],
        "summary": {"returned": 1},
        "ts": 1000,
    }

    assert main.radar_market_analysis_key(main.RadarScanRequest(), payload) != main.radar_market_analysis_key(
        main.RadarScanRequest(sortBy="turnover_24h"), payload
    )


def test_radar_default_ranking_keeps_playable_before_low_liquidity(monkeypatch):
    monkeypatch.setattr(
        main,
        "radar_instruments",
        lambda: [
            radar_instrument("PLAY-USDT-SWAP"),
            radar_instrument("THIN-USDT-SWAP"),
        ],
    )
    monkeypatch.setattr(
        main,
        "cached_tickers",
        lambda force=False: {
            "data": [
                radar_ticker("PLAY-USDT-SWAP", volume="20000000", last="100"),
                radar_ticker("THIN-USDT-SWAP", volume="5000", last="10"),
            ]
        },
    )

    def candles_for(inst_id, bar, limit, **_kwargs):
        if inst_id == "THIN-USDT-SWAP":
            return [
                {"ts": str(1000 + index), "open": "10", "high": "18", "low": "6", "close": "12", "volume": "10"}
                for index in range(40)
            ]
        return radar_candles(base=100, count=40)

    monkeypatch.setattr(main, "radar_candles", candles_for)

    payload = main.build_radar_scan(main.RadarScanRequest(minVolume="1000", limit=10, candidateLimit=10))

    assert [item["instId"] for item in payload["data"]] == ["PLAY-USDT-SWAP", "THIN-USDT-SWAP"]
    assert payload["data"][0]["tradabilityStatus"] == "playable"
    assert payload["data"][1]["tradabilityStatus"] == "low_liquidity"
    assert payload["data"][1]["scores"]["volatility"] >= payload["data"][0]["scores"]["volatility"]


def test_radar_cache_returns_fresh_snapshot(monkeypatch):
    stored = {}

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored.get(key)

        def set_app_setting(self, key, value, ts):
            stored[key] = value

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "now_ms", lambda: 100000)
    monkeypatch.setattr(
        main,
        "build_radar_scan",
        lambda request: {
            "data": [{"instId": "BTC-USDT-SWAP"}],
            "filters": request.model_dump(),
            "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
            "warning": "",
        },
    )
    with main.radar_cache_lock:
        main.radar_cache["payload"] = None
        main.radar_cache["ts"] = 0
        main.radar_cache["cacheKey"] = ""

    request = main.RadarScanRequest()
    first = main.cached_radar_scan(request, force=True)
    second = main.cached_radar_scan(request, force=False)

    assert first["source"] == "okx-radar"
    assert second["source"] == "radar-cache"
    assert second["data"][0]["instId"] == "BTC-USDT-SWAP"


def test_radar_llm_explanation_does_not_change_rank(monkeypatch):
    results = [
        {"instId": "AAA-USDT-SWAP", "scores": {"opportunity": 90}, "reasons": ["A"], "warnings": []},
        {"instId": "BBB-USDT-SWAP", "scores": {"opportunity": 80}, "reasons": ["B"], "warnings": []},
    ]
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key"},
    )
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *_args, **_kwargs: {
            "content": '{"items":[{"instId":"BBB-USDT-SWAP","reasons":["解释 B"],"warnings":[]}]}',
        },
    )

    explained, warning = main.explain_radar_results_with_llm(results)

    assert warning == ""
    assert [item["instId"] for item in explained] == ["AAA-USDT-SWAP", "BBB-USDT-SWAP"]
    assert explained[1]["reasons"] == ["解释 B"]


def test_radar_market_summary_is_bounded_and_counts_risks():
    rows = []
    for index in range(20):
        result = main.score_radar_contract(
            radar_instrument(f"COIN{index}-USDT-SWAP"),
            radar_ticker(f"COIN{index}-USDT-SWAP", volume=str(10000000 + index), last=str(100 + index)),
            radar_candles(base=100 + index),
            main.Decimal("1000000"),
        )
        result["scores"]["dataQuality"] = 50 if index == 0 else result["scores"]["dataQuality"]
        rows.append(result)
    payload = {
        "data": rows[:5],
        "filters": main.RadarScanRequest().model_dump(),
        "summary": {"total": 20, "candidates": 20, "returned": 5, "explained": 0},
        "source": "okx-radar",
        "ts": 123000,
        "cacheAgeMs": 0,
    }

    summary = main.build_radar_market_summary(payload, rows)

    assert summary["scan"]["total"] == 20
    assert summary["scan"]["analyzed"] == 20
    assert len(summary["leaders"]) == main.RADAR_MARKET_LEADER_LIMIT
    assert len(summary["topTurnover"]) == main.RADAR_MARKET_TOP_LIST_LIMIT
    assert len(summary["topVolatility"]) == main.RADAR_MARKET_TOP_LIST_LIMIT
    assert summary["risk"]["staleOrMissingData"] >= 1
    assert "." not in summary["liquidity"]["medianComparableTurnover"]
    assert re.search(r"\d+\.\d{3,}", summary["breadth"]["medianChange24hPct"]) is None
    assert re.search(r"\d+\.\d{3,}", summary["leaders"][0]["entryAssessment"]["drivers"][1]) is None


def test_radar_market_llm_analysis_returns_structured_output(monkeypatch):
    result = main.score_radar_contract(
        radar_instrument("AAA-USDT-SWAP"),
        radar_ticker("AAA-USDT-SWAP", volume="50000000", last="100"),
        radar_candles(),
        main.Decimal("1000000"),
    )
    payload = {
        "data": [result],
        "filters": main.RadarScanRequest().model_dump(),
        "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
        "source": "okx-radar",
        "ts": 123000,
        "cacheAgeMs": 0,
    }
    market_summary = main.build_radar_market_summary(payload, [result])
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key", "temperature": 0.2, "maxTokens": 800},
    )
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *_args, **_kwargs: {
            "content": (
                '{"marketRegime":"mixed","confidence":72,"summary":"市场分化。",'
                '"highlights":["成交额集中"],'
                '"watchlist":[{"instId":"AAA-USDT-SWAP","reason":"流动性好","riskNote":"注意振幅"}],'
                '"riskWarnings":["避免追涨"],"suggestedFilters":["低风险"],"warnings":[]}'
            )
        },
    )

    analysis = main.run_radar_market_llm_analysis(market_summary)

    assert analysis["source"] == "llm-market-analysis"
    assert analysis["marketRegime"] == "mixed"
    assert analysis["confidence"] == 72
    assert analysis["watchlist"][0]["instId"] == "AAA-USDT-SWAP"


def test_radar_market_llm_analysis_accepts_wrapped_json(monkeypatch):
    result = main.score_radar_contract(
        radar_instrument("AAA-USDT-SWAP"),
        radar_ticker("AAA-USDT-SWAP", volume="50000000", last="100"),
        radar_candles(),
        main.Decimal("1000000"),
    )
    market_summary = main.build_radar_market_summary(
        {
            "data": [result],
            "filters": main.RadarScanRequest().model_dump(),
            "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
            "ts": 123000,
        },
        [result],
    )
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key", "temperature": 0.2, "maxTokens": 800},
    )
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *_args, **_kwargs: {
            "content": (
                "```json\n"
                '{"marketRegime":"trend","confidence":70,"summary":"成交量和浮动配合。",'
                '"highlights":["成交额充足"],'
                '"watchlist":[{"instId":"AAA-USDT-SWAP","reason":"成交量充足且浮动适中","riskNote":"确认盘口"}],'
                '"riskWarnings":["避免追入"],"suggestedFilters":["低风险"],"warnings":[]}'
                "\n```\n补充说明"
            )
        },
    )

    analysis = main.run_radar_market_llm_analysis(market_summary)

    assert analysis["source"] == "llm-market-analysis"
    assert analysis["marketRegime"] == "trend"


def test_radar_market_llm_analysis_bad_json_fallback_is_user_friendly(monkeypatch):
    result = main.score_radar_contract(radar_instrument(), radar_ticker(), radar_candles(), main.Decimal("1000000"))
    market_summary = main.build_radar_market_summary(
        {
            "data": [result],
            "filters": main.RadarScanRequest().model_dump(),
            "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
            "ts": 123000,
        },
        [result],
    )
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key", "temperature": 0.2, "maxTokens": 800},
    )
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *_args, **_kwargs: {"content": '{"marketRegime":"trend" "confidence":70}'},
    )

    analysis = main.run_radar_market_llm_analysis(market_summary)

    assert analysis["source"] == "metric-fallback"
    assert "返回格式不稳定" in analysis["warnings"][0]
    assert "Expecting" not in analysis["warnings"][0]


def test_radar_market_analysis_reports_not_configured_state(monkeypatch):
    """No LLM configured => no rule-generated content masquerading as AI output."""
    result = main.score_radar_contract(radar_instrument(), radar_ticker(), radar_candles(), main.Decimal("1000000"))
    market_summary = main.build_radar_market_summary(
        {
            "data": [result],
            "filters": main.RadarScanRequest().model_dump(),
            "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
            "ts": 123000,
        },
        [result],
    )
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})

    analysis = main.run_radar_market_llm_analysis(market_summary)

    assert analysis["status"] == "not-configured"
    assert analysis["source"] == "llm-not-configured"
    assert analysis["summary"] == ""
    assert analysis["highlights"] == []
    assert analysis["watchlist"] == []
    assert analysis["riskWarnings"] == []
    assert analysis["suggestedFilters"] == []
    guide = analysis["setupGuide"]
    assert guide["settingsPath"] == "#/settings/llm"
    assert len(guide["steps"]) >= 3
    assert "API Key" in guide["requiredFields"]
    assert analysis["warnings"]


def test_radar_market_analysis_llm_failure_keeps_labelled_rule_fallback(monkeypatch):
    """Configured but failing LLM still yields rule output, labelled as fallback."""
    result = main.score_radar_contract(radar_instrument(), radar_ticker(), radar_candles(), main.Decimal("1000000"))
    market_summary = main.build_radar_market_summary(
        {
            "data": [result],
            "filters": main.RadarScanRequest().model_dump(),
            "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
            "ts": 123000,
        },
        [result],
    )
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key", "temperature": 0.2, "maxTokens": 800},
    )

    def fail(*_args, **_kwargs):
        raise main.LlmCompletionError("连接超时")

    monkeypatch.setattr(main, "llm_chat_completion", fail)

    analysis = main.run_radar_market_llm_analysis(market_summary)

    assert analysis["source"] == "metric-fallback"
    assert analysis["warnings"]
    assert "指标分析" in analysis["warnings"][0]


def test_radar_cached_analysis_skips_sentiment_when_not_configured(monkeypatch):
    stored = {}

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored.get(key)

        def set_app_setting(self, key, value, ts):
            stored[key] = value

    request = main.RadarScanRequest()
    result = main.score_radar_contract(radar_instrument(), radar_ticker(), radar_candles(), main.Decimal("1000000"))
    radar_payload = {
        "data": [result],
        "filters": request.model_dump(),
        "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
        "source": "okx-radar",
        "ts": 100000,
        "cacheAgeMs": 0,
    }
    radar_payload["marketSummary"] = main.build_radar_market_summary(radar_payload, [result])
    calls = {"enrich": 0}

    def fake_enrich(payload):
        calls["enrich"] += 1
        return payload.get("marketSummary") or {}

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})
    monkeypatch.setattr(main, "enrich_radar_sentiment", fake_enrich)
    with main.radar_analysis_cache_lock:
        main.radar_analysis_cache["payload"] = None
        main.radar_analysis_cache["ts"] = 0
        main.radar_analysis_cache["cacheKey"] = ""

    response = main.cached_radar_market_analysis(request, radar_payload, force=True)

    assert response["status"] == "not-configured"
    assert response["source"] == "llm-not-configured"
    assert calls["enrich"] == 0
    assert main.RADAR_ANALYSIS_CACHE_KEY not in stored


def test_radar_cached_analysis_ignores_stale_not_configured_snapshot(monkeypatch):
    stored = {}

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored.get(key)

        def set_app_setting(self, key, value, ts):
            stored[key] = value

    request = main.RadarScanRequest()
    result = main.score_radar_contract(radar_instrument(), radar_ticker(), radar_candles(), main.Decimal("1000000"))
    radar_payload = {
        "data": [result],
        "filters": request.model_dump(),
        "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
        "source": "okx-radar",
        "ts": 100000,
        "cacheAgeMs": 0,
    }
    radar_payload["marketSummary"] = main.build_radar_market_summary(radar_payload, [result])
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "now_ms", lambda: 100001)
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key"})
    monkeypatch.setattr(main, "enrich_radar_sentiment", lambda _payload: {})
    monkeypatch.setattr(main, "run_radar_market_llm_analysis", lambda _summary: {"source": "llm-market-analysis", "summary": "ok"})
    with main.radar_analysis_cache_lock:
        main.radar_analysis_cache["payload"] = None
        main.radar_analysis_cache["ts"] = 0
        main.radar_analysis_cache["cacheKey"] = ""
    cache_key = main.radar_market_analysis_key(request, radar_payload)
    main.save_radar_analysis_snapshot(cache_key, main.radar_llm_not_configured_payload(), 100000)

    response = main.cached_radar_market_analysis(request, radar_payload, force=False)

    assert response["source"] == "llm-market-analysis"

    # Disabling the LLM must win over any cached analysis payload.
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})
    disabled = main.cached_radar_market_analysis(request, radar_payload, force=False)
    assert disabled["status"] == "not-configured"
    assert disabled["watchlist"] == []


def test_radar_analysis_cache_preserves_origin_source():
    result = main.radar_analysis_payload_with_cache_meta(
        {"source": "metric-fallback", "summary": "x"}, "radar-analysis-cache", 1000
    )
    assert result["originSource"] == "metric-fallback"
    assert result["source"] == "radar-analysis-cache"


def test_radar_market_analysis_cache_reuses_fresh_snapshot(monkeypatch):
    stored = {}

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored.get(key)

        def set_app_setting(self, key, value, ts):
            stored[key] = value

    request = main.RadarScanRequest()
    result = main.score_radar_contract(radar_instrument(), radar_ticker(), radar_candles(), main.Decimal("1000000"))
    radar_payload = {
        "data": [result],
        "filters": request.model_dump(),
        "summary": {"total": 1, "candidates": 1, "returned": 1, "explained": 0},
        "source": "okx-radar",
        "ts": 100000,
        "cacheAgeMs": 0,
    }
    radar_payload["marketSummary"] = main.build_radar_market_summary(radar_payload, [result])
    calls = {"count": 0}

    def fake_analysis(market_summary):
        calls["count"] += 1
        return main.fallback_radar_market_analysis(market_summary)

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "now_ms", lambda: 100000)
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key"})
    monkeypatch.setattr(main, "run_radar_market_llm_analysis", fake_analysis)
    monkeypatch.setattr(main.client, "get_funding_rate", lambda *_args: None)
    monkeypatch.setattr(main.client, "get_open_interest_bulk", lambda *_args: {})
    with main.radar_analysis_cache_lock:
        main.radar_analysis_cache["payload"] = None
        main.radar_analysis_cache["ts"] = 0
        main.radar_analysis_cache["cacheKey"] = ""

    first = main.cached_radar_market_analysis(request, radar_payload, force=True)
    second = main.cached_radar_market_analysis(request, radar_payload, force=False)

    assert first["source"] == "metric-fallback"
    assert second["source"] == "radar-analysis-cache"
    assert calls["count"] == 1


def test_radar_market_analysis_does_not_mutate_ranking(monkeypatch):
    stored = {}

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored.get(key)

        def set_app_setting(self, key, value, ts):
            stored[key] = value

    request = main.RadarScanRequest()
    radar_payload = {
        "data": [
            {"instId": "AAA-USDT-SWAP", "scores": {"opportunity": 90, "dataQuality": 100}, "metrics": {"candleCount": 40}, "riskLevel": "low", "volatilityLevel": "high", "tradabilityStatus": "playable", "liquidity": {"value": "100000000", "comparable": True}, "tags": [], "warnings": []},
            {"instId": "BBB-USDT-SWAP", "scores": {"opportunity": 80, "dataQuality": 100}, "metrics": {"candleCount": 40}, "riskLevel": "low", "volatilityLevel": "medium", "tradabilityStatus": "playable", "liquidity": {"value": "90000000", "comparable": True}, "tags": [], "warnings": []},
        ],
        "filters": request.model_dump(),
        "summary": {"total": 2, "candidates": 2, "returned": 2, "explained": 0},
        "source": "okx-radar",
        "ts": 123000,
        "cacheAgeMs": 0,
    }
    radar_payload["marketSummary"] = main.build_radar_market_summary(radar_payload)
    before = [item["instId"] for item in radar_payload["data"]]
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})
    monkeypatch.setattr(main.client, "get_funding_rate", lambda *_args: None)
    monkeypatch.setattr(main.client, "get_open_interest_bulk", lambda *_args: {})

    main.cached_radar_market_analysis(request, radar_payload, force=True)

    assert [item["instId"] for item in radar_payload["data"]] == before


def _radar_row_with_sentiment(inst_id, funding_rate=None, open_interest=None):
    result = main.score_radar_contract(
        radar_instrument(inst_id),
        radar_ticker(inst_id, volume="50000000", last="100"),
        radar_candles(),
        main.Decimal("1000000"),
    )
    result["fundingRate"] = main.Decimal(funding_rate) if funding_rate is not None else None
    result["openInterestUsd"] = main.Decimal(open_interest) if open_interest is not None else None
    return result


def test_radar_market_summary_aggregates_sentiment():
    rows = [
        _radar_row_with_sentiment("COIN0-USDT-SWAP", "0.0001", "1000000"),
        _radar_row_with_sentiment("COIN1-USDT-SWAP", "-0.0002", "2000000"),
        _radar_row_with_sentiment("COIN2-USDT-SWAP", None, None),
    ]
    payload = {
        "data": rows,
        "filters": main.RadarScanRequest().model_dump(),
        "summary": {"total": 3, "candidates": 3, "returned": 3, "explained": 0},
        "ts": 123000,
    }

    summary = main.build_radar_market_summary(payload, rows)

    sentiment = summary["sentiment"]
    assert sentiment["funding"]["sampled"] == 2
    assert sentiment["funding"]["positive"] == 1
    assert sentiment["funding"]["negative"] == 1
    assert sentiment["funding"]["neutral"] == 0
    assert sentiment["openInterest"]["sampled"] == 2
    assert "fundingRate" in summary["leaders"][0]
    assert "openInterestUsd" in summary["leaders"][0]


def test_radar_enrich_sentiment_fetches_and_rebuilds(monkeypatch):
    captured = {}

    def fake_funding(inst_id):
        captured.setdefault("fr", []).append(inst_id)
        return {"fundingRate": "0.0001"}

    def fake_oi_bulk():
        captured["oi_bulk_called"] = True
        return {
            "COIN0-USDT-SWAP": "1234567.89",
            "COIN1-USDT-SWAP": "2234567.89",
            "COIN2-USDT-SWAP": "3234567.89",
        }

    # Reset module-level caches so the assertions are deterministic.
    monkeypatch.setattr(main, "_radar_sentiment_funding_cache", {})
    monkeypatch.setattr(main, "_radar_sentiment_oi_bulk_cache", None)
    monkeypatch.setattr(main.client, "get_funding_rate", fake_funding)
    monkeypatch.setattr(main.client, "get_open_interest_bulk", fake_oi_bulk)

    rows = [
        _radar_row_with_sentiment(f"COIN{index}-USDT-SWAP")
        for index in range(3)
    ]
    payload = {
        "data": rows,
        "filters": main.RadarScanRequest().model_dump(),
        "summary": {"total": 3, "candidates": 3, "returned": 3, "explained": 0},
        "ts": 123000,
    }

    summary = main.enrich_radar_sentiment(payload)

    assert summary["sentiment"]["funding"]["sampled"] == 3
    assert summary["sentiment"]["funding"]["positive"] == 3
    assert summary["leaders"][0]["fundingRate"] != ""
    assert all(row.get("fundingRate") is not None for row in rows)
    assert captured["fr"] == ["COIN0-USDT-SWAP", "COIN1-USDT-SWAP", "COIN2-USDT-SWAP"]
    assert captured["oi_bulk_called"] is True
    assert all(row.get("openInterestUsd") is not None for row in rows)


def test_radar_clean_direction():
    assert main.radar_clean_direction("long") == "long"
    assert main.radar_clean_direction("SHORT") == "short"
    assert main.radar_clean_direction("买多") == "long"
    assert main.radar_clean_direction("做空") == "short"
    assert main.radar_clean_direction("neutral") == "neutral"
    assert main.radar_clean_direction("garbage") == "neutral"


def test_radar_rule_direction():
    assert main.radar_rule_direction({"riskLevel": "high", "change24hPct": "5"}) == "neutral"
    assert main.radar_rule_direction({"riskLevel": "low", "change24hPct": "2.0"}) == "long"
    assert main.radar_rule_direction({"riskLevel": "low", "change24hPct": "-3"}) == "short"
    assert main.radar_rule_direction({"riskLevel": "low", "change24hPct": "0.5"}) == "neutral"
    assert main.radar_rule_direction({"riskLevel": "low"}) == "neutral"


def _radar_market_summary_with_prices():
    return {
        "scan": {"analyzed": 10, "ts": 1},
        "breadth": {"rising": 8, "falling": 1, "medianChange24hPct": "1.0"},
        "liquidity": {"playable": 5, "lowLiquidity": 1, "comparableCount": 5},
        "volatility": {"high": 1},
        "risk": {"high": 0, "abnormalMoves": 0},
        "leaders": [
            {
                "instId": "BTC-USDT-SWAP",
                "score": 80,
                "last": "60000",
                "high24h": "61000",
                "low24h": "59000",
                "change24hPct": "1.5",
                "volatilityLevel": "medium",
                "tradabilityStatus": "playable",
                "entryAssessment": {"summary": "ok"},
                "fundingRate": "0.0001",
                "openInterestUsd": "1000000",
            }
        ],
    }


def test_radar_parse_market_analysis_bias_and_direction():
    market_summary = _radar_market_summary_with_prices()
    parsed = {
        "marketRegime": "trend",
        "marketBias": "long",
        "confidence": 70,
        "summary": "偏多环境",
        "highlights": ["a"],
        "watchlist": [
            {
                "instId": "BTC-USDT-SWAP",
                "reason": "成交充足",
                "riskNote": "注意止损",
                "direction": "long",
                "entryZone": "回踩 59000~60000 分批",
            }
        ],
        "riskWarnings": [],
        "suggestedFilters": [],
    }
    result = main.parse_radar_market_llm_analysis(parsed, market_summary)
    assert result["marketBias"] == "long"
    item = result["watchlist"][0]
    assert item["direction"] == "long"
    assert "59000" in item["entryZone"]


def test_radar_parse_market_analysis_entry_zone_validation():
    market_summary = _radar_market_summary_with_prices()
    parsed = {
        "marketRegime": "mixed",
        "watchlist": [
            {"instId": "BTC-USDT-SWAP", "direction": "long", "entryZone": "在 999999 附近买入"}
        ],
    }
    result = main.parse_radar_market_llm_analysis(parsed, market_summary)
    item = result["watchlist"][0]
    assert item["direction"] == "long"
    assert "999999" not in item["entryZone"]
    assert "59000" in item["entryZone"]


def test_radar_fallback_includes_bias_and_direction():
    market_summary = _radar_market_summary_with_prices()
    result = main.fallback_radar_market_analysis(market_summary)
    assert result["marketBias"] == "long"
    assert result["watchlist"][0]["direction"] == "long"
    assert "59000" in result["watchlist"][0]["entryZone"]


def _explain_result(inst_id, last, high, low):
    return {
        "instId": inst_id,
        "scores": {"opportunity": 70},
        "riskLevel": "low",
        "volatilityLevel": "medium",
        "reasons": [],
        "warnings": [],
        "last": str(last),
        "high24h": str(high),
        "low24h": str(low),
    }


def _explain_llm_config(monkeypatch):
    monkeypatch.setattr(
        main,
        "stored_llm_config",
        lambda: {"enabled": True, "baseUrl": "https://example.test/v1", "model": "demo", "apiKey": "key"},
    )


def test_radar_explain_embeds_direction_and_entry_zone(monkeypatch):
    _explain_llm_config(monkeypatch)
    results = [_explain_result("X-USDT-SWAP", 100, 110, 90)]
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *_a, **_k: {
            "content": '{"items":[{"instId":"X-USDT-SWAP","reasons":["r"],"warnings":[],"direction":"long","entryZone":"回踩 90~100 分批"}]}',
        },
    )
    explained, warning = main.explain_radar_results_with_llm(results)
    assert warning == ""
    assert explained[0]["direction"] == "long"
    assert explained[0]["entryZone"] == "回踩 90~100 分批"
    assert explained[0]["explainedBy"] == "llm"


def test_radar_explain_entry_zone_out_of_bounds_falls_back(monkeypatch):
    _explain_llm_config(monkeypatch)
    results = [_explain_result("X-USDT-SWAP", 100, 110, 90)]
    monkeypatch.setattr(
        main,
        "llm_chat_completion",
        lambda *_a, **_k: {
            "content": '{"items":[{"instId":"X-USDT-SWAP","direction":"short","entryZone":"在 999999 附近做空"}]}',
        },
    )
    explained, _ = main.explain_radar_results_with_llm(results)
    assert explained[0]["direction"] == "short"
    assert "999999" not in explained[0]["entryZone"]
    assert "110" in explained[0]["entryZone"]
