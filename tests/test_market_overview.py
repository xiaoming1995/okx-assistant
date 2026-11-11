import pytest

from backend.app import main
from backend.app.okx import OkxError


@pytest.fixture(autouse=True)
def reset_platform_volume_cache():
    with main.platform_volume_cache_lock:
        main.platform_volume_cache.update(snapshot=None, receivedAt=0, refreshing=False, nextRetryAt=0)
    yield
    with main.platform_volume_cache_lock:
        main.platform_volume_cache.update(snapshot=None, receivedAt=0, refreshing=False, nextRetryAt=0)


def test_platform_volume_client_uses_public_production_endpoint(monkeypatch):
    captured = {}

    def request(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return {"data": [{"volUsd": "123456", "ts": "100000"}]}

    monkeypatch.setattr(main.client, "_request", request)
    assert main.client.get_platform_24_volume() == {"volUsd": "123456", "ts": "100000"}
    assert captured == {
        "method": "GET",
        "path": "/api/v5/market/platform-24-volume",
        "auth": False,
        "include_simulated_header": False,
    }


@pytest.mark.parametrize("raw", [
    None,
    {"volUsd": "", "ts": "100000"},
    {"volUsd": "NaN", "ts": "100000"},
    {"volUsd": "0", "ts": "100000"},
    {"volUsd": "123", "ts": "NaN"},
    {"volUsd": "123", "ts": "100.5"},
    {"volUsd": "123", "ts": "1000000"},
])
def test_platform_volume_rejects_missing_or_invalid_values(raw):
    with pytest.raises(ValueError):
        main.normalize_platform_24_volume(raw, 100_000)


def test_platform_volume_cache_retains_recent_snapshot_but_hides_expired_value(monkeypatch):
    clock = {"now": 1_800_000}
    calls = []

    def fetch():
        calls.append(clock["now"])
        if len(calls) > 1:
            raise OkxError("private transport details")
        return {"volUsd": "123456789", "ts": str(clock["now"])}

    monkeypatch.setattr(main, "now_ms", lambda: clock["now"])
    monkeypatch.setattr(main.client, "get_platform_24_volume", fetch)

    first = main.market_overview_volume()
    clock["now"] += 30_000
    reused = main.market_overview_volume()
    assert first["state"] == reused["state"] == "fresh"
    assert reused["data"]["volUsd"] == "123456789"
    assert len(calls) == 1

    clock["now"] += 31_000
    retained = main.market_overview_volume()
    assert retained["state"] == "cached"
    assert retained["ts"] == first["ts"]
    assert "private transport" not in str(retained)

    clock["now"] += main.PLATFORM_VOLUME_MAX_AGE_MS
    expired = main.market_overview_volume()
    assert expired["state"] == "unavailable"
    assert expired["data"] is None


def test_platform_volume_first_fetch_failure_has_no_fabricated_number(monkeypatch):
    monkeypatch.setattr(main, "now_ms", lambda: 1_800_000)
    monkeypatch.setattr(main.client, "get_platform_24_volume", lambda: {"volUsd": "", "ts": "1800000"})
    response = main.market_overview_volume()
    assert response["state"] == "unavailable"
    assert response["data"] is None
