import pytest

from backend.app import main
from backend.app.okx import OkxError


def reset_market_stats_cache():
    with main.market_stats_cache_lock:
        main.market_stats_cache["payload"] = None
        main.market_stats_cache["ts"] = 0
        main.market_stats_cache["cacheKey"] = ""
        main.market_stats_metric_cache.clear()


def test_market_stats_normalizes_contract_metrics():
    long_short = main.normalize_long_short_account_ratio(
        [
            ["2000", "1.20"],
            ["1000", "0.90"],
        ]
    )
    taker = main.normalize_taker_volume([["1000", "200", "380"]])
    open_interest = main.normalize_open_interest_history(
        [
            ["1000", "100", "10", "1000"],
            ["2000", "110", "11", "1300"],
        ]
    )

    assert long_short["latest"] == "1.2"
    assert long_short["bias"] == "more_long_accounts"
    assert [point["ts"] for point in long_short["points"]] == [1000, 2000]

    assert taker["buyVol"] == "380"
    assert taker["sellVol"] == "200"
    assert taker["buySharePct"] == "65.52"
    assert taker["buySellRatio"] == "1.9"
    assert taker["dominance"] == "active_buying_stronger"

    assert open_interest["oiUsd"] == "1300"
    assert open_interest["change"] == "300"
    assert open_interest["changePct"] == "30"
    assert open_interest["trend"] == "increasing"


def test_market_stats_taker_volume_avoids_invalid_zero_side_ratio():
    taker = main.normalize_taker_volume([["1000", "0", "25"]])

    assert taker["buyVol"] == "25"
    assert taker["sellVol"] == "0"
    assert taker["buySharePct"] == "100"
    assert taker["buySellRatio"] == ""
    assert taker["dominance"] == "active_buying_stronger"


def test_market_stats_period_and_instrument_validation():
    assert main.normalize_market_stats_period("1m") == "5m"
    assert main.normalize_market_stats_period("15m") == "15m"
    assert main.normalize_market_stats_inst_id("btc-usdt-swap") == "BTC-USDT-SWAP"

    with pytest.raises(Exception):
        main.normalize_market_stats_inst_id("BTC-USDT")


def test_market_stats_api_caches_by_contract_period_and_limit(monkeypatch):
    reset_market_stats_cache()
    monkeypatch.setattr(main, "now_ms", lambda: 100000)
    calls = {"count": 0}

    def fake_build(inst_id, requested_period, period, limit):
        calls["count"] += 1
        return main.empty_market_stats_payload(inst_id, requested_period, period, limit)

    monkeypatch.setattr(main, "build_market_stats", fake_build)

    first = main.cached_market_stats("BTC-USDT-SWAP", "1m", "5m", 50, force=False)
    second = main.cached_market_stats("BTC-USDT-SWAP", "1m", "5m", 50, force=False)

    assert calls["count"] == 1
    assert first["source"] == "okx-market-stats"
    assert second["source"] == "market-stats-cache"
    assert second["period"] == "5m"
    assert second["requestedPeriod"] == "1m"


def test_market_stats_partial_metric_failure_keeps_successful_metrics(monkeypatch):
    reset_market_stats_cache()

    class FakeClient:
        def get_contract_long_short_account_ratio(self, inst_id, period, limit):
            return [["1000", "1.10"]]

        def get_contract_taker_volume(self, inst_id, period, limit, unit="2"):
            raise OkxError("rate limited")

        def get_contract_open_interest_history(self, inst_id, period, limit):
            return [["1000", "10", "2", "100"], ["2000", "12", "3", "130"]]

    monkeypatch.setattr(main, "client", FakeClient())

    payload = main.cached_market_stats("BTC-USDT-SWAP", "5m", "5m", 20, force=True)

    assert payload["source"] == "okx-market-stats-partial"
    assert payload["longShortAccountRatio"]["latest"] == "1.1"
    assert payload["openInterest"]["changePct"] == "30"
    assert payload["takerVolume"]["points"] == []
    assert any("主动买卖量本次刷新失败，暂无可用缓存" in warning for warning in payload["warnings"])


def test_market_stats_partial_metric_failure_uses_matching_stale_metric_cache(monkeypatch):
    reset_market_stats_cache()
    monkeypatch.setattr(main, "now_ms", lambda: 200000)
    calls = {"count": 0}

    class FakeClient:
        def get_contract_long_short_account_ratio(self, inst_id, period, limit):
            return [["1000", "1.10"]]

        def get_contract_taker_volume(self, inst_id, period, limit, unit="2"):
            calls["count"] += 1
            if calls["count"] == 1:
                return [["1000", "100", "300"]]
            raise OkxError("OKX response was incomplete after retries: IncompleteRead(0 bytes read)")

        def get_contract_open_interest_history(self, inst_id, period, limit):
            return [["1000", "10", "2", "100"], ["2000", "12", "3", "130"]]

    monkeypatch.setattr(main, "client", FakeClient())

    first = main.cached_market_stats("BTC-USDT-SWAP", "5m", "5m", 20, force=True)
    second = main.cached_market_stats("BTC-USDT-SWAP", "5m", "5m", 20, force=True)

    assert first["takerVolume"]["buySharePct"] == "75"
    assert second["source"] == "okx-market-stats-partial"
    assert second["takerVolume"]["buySharePct"] == "75"
    assert second["takerVolume"]["points"]
    assert any("主动买卖量本次刷新失败，显示上次缓存" in warning for warning in second["warnings"])
    assert any("OKX 本次返回中断，已重试" in warning for warning in second["warnings"])
