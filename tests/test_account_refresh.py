from backend.app import main
from backend.app.okx import OkxError


class FakeSettings:
    account_cache_seconds = 20
    account_stale_seconds = 600
    timeout_seconds = 1

    def has_credentials_for_environment(self, environment):
        return environment == "live"


def account_payload(ts, source="okx"):
    return {
        "configured": True,
        "environment": "live",
        "summary": {"totalEq": "10"},
        "positions": [{"instId": "BTC-USDT-SWAP", "pos": "1", "upl": "2"}],
        "source": source,
        "ts": ts,
        "cacheAgeMs": 0,
    }


def reset_account_cache(payload=None, ts=0, refreshing=False, failure_count=0, next_retry_at=0):
    with main.account_cache_condition:
        main.account_cache.clear()
        main.account_cache.update(
            {
                "environment": "live" if payload else "",
                "payload": payload,
                "ts": ts,
                "refreshing": refreshing,
                "failureCount": failure_count,
                "nextRetryAt": next_retry_at,
            }
        )


def configure_live_account(monkeypatch, now):
    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "current_trading_environment", lambda: "live")
    monkeypatch.setattr(main, "now_ms", lambda: now)


def test_retained_account_snapshot_hides_raw_incomplete_read_and_observes_backoff(monkeypatch):
    now = 1_000_000
    reset_account_cache(
        payload=account_payload(now - 30_000),
        ts=now - 30_000,
        failure_count=2,
        next_retry_at=now + 10_000,
    )
    configure_live_account(monkeypatch, now)
    started = []
    monkeypatch.setattr(main, "start_account_refresh", lambda *args, **kwargs: started.append(True) or False)

    response = main.cached_account(force=True)

    assert response["positions"][0]["instId"] == "BTC-USDT-SWAP"
    assert response["source"] == "okx-stale-cache"
    assert response["refresh"]["state"] == "backing_off"
    assert response["refresh"]["nextRetryAt"] == now + 10_000
    assert response["warning"] == "账户和持仓暂沿用最近完整快照，稍后自动重试"
    assert "IncompleteRead" not in str(response)
    assert started == []


def test_persisted_account_snapshot_is_returned_with_safe_refresh_state(monkeypatch):
    now = 2_000_000
    reset_account_cache()
    configure_live_account(monkeypatch, now)
    monkeypatch.setattr(main, "load_account_from_database", lambda environment: account_payload(now - 30_000, "database-cache"))
    monkeypatch.setattr(main, "start_account_refresh", lambda *args, **kwargs: False)

    response = main.cached_account(force=True)

    assert response["source"] == "database-cache"
    assert response["refresh"]["state"] == "stale"
    assert response["warning"] == "账户和持仓暂沿用最近完整快照"
    assert "IncompleteRead" not in str(response)


def test_missing_account_snapshot_returns_safe_unavailable_state(monkeypatch):
    now = 3_000_000
    reset_account_cache()
    configure_live_account(monkeypatch, now)
    monkeypatch.setattr(main, "load_account_from_database", lambda environment: None)
    monkeypatch.setattr(main, "start_account_refresh", lambda *args, **kwargs: False)

    response = main.cached_account()

    assert response["configured"] is True
    assert response["positions"] == []
    assert response["source"] == "okx-unavailable"
    assert response["refresh"]["state"] == "unavailable"
    assert response["warning"] == "账户和持仓暂不可用，正在等待完整快照"
    assert "IncompleteRead" not in str(response)


def test_background_account_failure_sets_backoff_without_retaining_raw_exception(monkeypatch):
    now = 4_000_000
    reset_account_cache(payload=account_payload(now - 30_000), ts=now - 30_000, refreshing=True)
    configure_live_account(monkeypatch, now)
    monkeypatch.setattr(main, "refresh_account_cache_sync", lambda environment: (_ for _ in ()).throw(OkxError("IncompleteRead(12 bytes read)")))

    main.refresh_account_cache_background("live")
    payload, ts, refreshing, failures, retry_at = main.account_cache_values("live")

    assert payload["positions"][0]["instId"] == "BTC-USDT-SWAP"
    assert ts == now - 30_000
    assert refreshing is False
    assert failures == 1
    assert retry_at == now + main.ACCOUNT_REFRESH_BACKOFF_BASE_MS


def test_successful_account_refresh_clears_retry_state(monkeypatch):
    now = 5_000_000
    reset_account_cache(payload=account_payload(now - 30_000), ts=now - 30_000, failure_count=3, next_retry_at=now + 10_000)
    configure_live_account(monkeypatch, now)

    class FakeClient:
        def get_balance(self):
            return {"data": [{"totalEq": "12"}]}

        def get_positions(self):
            return {"data": [{"instId": "ETH-USDT-SWAP", "pos": "1", "upl": "3"}]}

    class FakeDatabase:
        def insert_account_snapshot(self, *args):
            return None

        def insert_position_snapshots(self, *args):
            return None

    monkeypatch.setattr(main, "client_for_environment", lambda environment: FakeClient())
    monkeypatch.setattr(main, "database", FakeDatabase())

    response = main.refresh_account_cache_sync("live")
    _payload, _ts, _refreshing, failures, retry_at = main.account_cache_values("live")

    assert response["source"] == "okx"
    assert response["refresh"]["state"] == "fresh"
    assert response["positions"][0]["instId"] == "ETH-USDT-SWAP"
    assert failures == 0
    assert retry_at == 0
