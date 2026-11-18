import pytest

from backend.app import main
from backend.app.okx import OkxError


@pytest.fixture(autouse=True)
def reset_volume_history_cache():
    with main.volume_history_cache_lock:
        main.volume_history_cache.update(snapshot=None, receivedAt=0, refreshing=False, nextRetryAt=0)
    yield
    with main.volume_history_cache_lock:
        main.volume_history_cache.update(snapshot=None, receivedAt=0, refreshing=False, nextRetryAt=0)


class FakeDatabase:
    def __init__(self):
        self.settings = {}

    def list_instruments(self, query="", limit=200):
        rows = [
            {"inst_id": f"COIN{i}-USDT-SWAP", "settle_ccy": "USDT", "inst_type": "SWAP"}
            for i in range(10)
        ]
        rows.append({"inst_id": "BTC-USD-SWAP", "settle_ccy": "BTC", "inst_type": "SWAP"})
        return rows

    def set_app_setting(self, key, value, ts):
        self.settings[key] = value

    def get_app_setting(self, key):
        return self.settings.get(key)


def fake_tickers():
    rows = []
    for i in range(10):
        rows.append({
            "instId": f"COIN{i}-USDT-SWAP",
            "last": "100",
            "volCcy24h": str(1000 - i * 10),
        })
    rows.append({"instId": "BTC-USD-SWAP", "last": "70000", "vol24h": "999999"})
    rows.append({"instId": "TESTA-USDT-SWAP", "last": "1", "volCcy24h": "99999999"})
    return {"data": rows}


def test_history_candles_passes_after_cursor(monkeypatch):
    captured = {}

    def request(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return {"data": []}

    monkeypatch.setattr(main.client, "_request", request)
    main.client.get_history_candles("BTC-USDT-SWAP", "1D", 100, after="1794585600000")
    assert captured["path"] == "/api/v5/market/history-candles"
    assert captured["query"] == {
        "instId": "BTC-USDT-SWAP",
        "bar": "1D",
        "limit": "100",
        "after": "1794585600000",
    }


def test_history_candles_without_after_keeps_original_query(monkeypatch):
    captured = {}

    def request(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return {"data": []}

    monkeypatch.setattr(main.client, "_request", request)
    main.client.get_history_candles("BTC-USDT-SWAP", "1D", 100)
    assert "after" not in captured["query"]


def test_day_label_uses_shanghai_time():
    # 1794585600000 is 2026-11-14 00:00 in UTC+8 but 2026-11-13 16:00 UTC.
    assert main.volume_history_day_label(1794585600000) == "2026-11-14"


def test_universe_excludes_coin_settled_and_test_contracts(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "cached_tickers", lambda: fake_tickers())
    ids, coverage, universe = main.volume_history_instrument_universe()
    assert ids == [f"COIN{i}-USDT-SWAP" for i in range(10)]
    assert universe == 10
    assert coverage == pytest.approx(100.0)


def test_build_snapshot_sums_real_daily_quotes(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "cached_tickers", lambda: fake_tickers())
    monkeypatch.setattr(main, "VOLUME_HISTORY_TOP_N", 10)

    def candles(inst_id, bar, limit):
        assert bar == "1D"
        index = int(inst_id.replace("COIN", "").split("-")[0])
        return [
            {"ts": "1794499200000", "volumeQuote": str(100 + index), "confirm": "1"},
            {"ts": "1794585600000", "volumeQuote": str(200 + index), "confirm": "0"},
        ]

    monkeypatch.setattr(main.client, "get_candles", candles)
    monkeypatch.setattr(main.client, "get_history_candles", lambda *args, **kwargs: [])
    snapshot = main.build_volume_history_snapshot()
    by_date = {row["date"]: row for row in snapshot["daily"]}
    assert list(by_date) == ["2026-11-13", "2026-11-14"]
    assert float(by_date["2026-11-13"]["volUsd"]) == pytest.approx(sum(100 + i for i in range(10)))
    assert float(by_date["2026-11-14"]["volUsd"]) == pytest.approx(sum(200 + i for i in range(10)))
    assert by_date["2026-11-14"]["confirm"] == "0"
    assert by_date["2026-11-13"]["count"] == 10
    assert snapshot["instrumentCount"] == 10
    assert snapshot["coveragePct"] == pytest.approx(100.0)
    assert snapshot["source"] == "okx-1d-candles-volumeQuote"


def test_build_snapshot_tolerates_partial_candle_failure(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "cached_tickers", lambda: fake_tickers())
    monkeypatch.setattr(main, "VOLUME_HISTORY_TOP_N", 10)

    def candles(inst_id, bar, limit):
        if inst_id == "COIN0-USDT-SWAP":
            raise OkxError("transient")
        return [{"ts": "1794499200000", "volumeQuote": "10", "confirm": "1"}]

    monkeypatch.setattr(main.client, "get_candles", candles)
    monkeypatch.setattr(main.client, "get_history_candles", lambda *args, **kwargs: [])
    snapshot = main.build_volume_history_snapshot()
    assert snapshot["instrumentCount"] == 9
    assert snapshot["requestedCount"] == 10
    assert float(snapshot["daily"][0]["volUsd"]) == pytest.approx(90)


def test_build_snapshot_rejects_too_few_usable_contracts(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "cached_tickers", lambda: {"data": [
        {"instId": "COIN0-USDT-SWAP", "last": "100", "volCcy24h": "1000"}
    ]})
    monkeypatch.setattr(main, "VOLUME_HISTORY_TOP_N", 10)
    with pytest.raises(ValueError, match="Not enough active"):
        main.build_volume_history_snapshot()


def test_snapshot_persists_and_reloads(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(main, "database", fake_db)
    payload = {"daily": [{"date": "2026-11-14", "volUsd": "123"}], "instrumentCount": 10}
    main.save_volume_history_snapshot(payload, 1_800_000)
    with main.volume_history_cache_lock:
        main.volume_history_cache.update(snapshot=None, receivedAt=0)
    reloaded = main.load_volume_history_snapshot()
    assert reloaded == payload
    with main.volume_history_cache_lock:
        assert main.volume_history_cache["receivedAt"] == 1_800_000


def test_response_states_never_fabricate_numbers(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "now_ms", lambda: 1_800_000)
    empty = main.volume_history_response(1_800_000)
    assert empty["state"] == "unavailable"
    assert empty["data"] is None

    payload = {"daily": [{"date": "2026-11-14", "volUsd": "123"}]}
    main.save_volume_history_snapshot(payload, 1_800_000)
    fresh = main.volume_history_response(1_800_000)
    assert fresh["state"] == "fresh"
    assert fresh["data"] == payload

    cached = main.volume_history_response(1_800_000 + main.VOLUME_HISTORY_CACHE_MS + 1)
    assert cached["state"] == "cached"
    assert cached["data"] == payload

    expired = main.volume_history_response(1_800_000 + main.VOLUME_HISTORY_MAX_AGE_MS + 1)
    assert expired["state"] == "unavailable"
    assert expired["data"] is None


def test_endpoint_accepts_force_flag(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "now_ms", lambda: 1_800_000)
    monkeypatch.setattr(main, "start_volume_history_refresh", lambda: True)
    response = main.market_overview_volume_history(force=True)
    assert response["state"] == "unavailable"
    assert response["data"] is None
    assert "source" in response
