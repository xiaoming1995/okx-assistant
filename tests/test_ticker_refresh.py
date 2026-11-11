from backend.app import main
from backend.app.okx import OkxError


def reset_ticker_cache(rows=None, ts=0, refreshing=False, failure_count=0, next_retry_at=0):
    with main.ticker_cache_condition:
        main.ticker_cache.clear()
        main.ticker_cache.update(
            {
                "data": rows or [],
                "ts": ts,
                "refreshing": refreshing,
                "warning": "",
                "failureCount": failure_count,
                "nextRetryAt": next_retry_at,
            }
        )


def test_retained_ticker_snapshot_hides_raw_incomplete_read_and_reports_backoff(monkeypatch):
    now = 1_000_000
    reset_ticker_cache(
        rows=[{"instId": "BTC-USDT-SWAP", "last": "100"}],
        ts=now - 30_000,
        failure_count=2,
        next_retry_at=now + 10_000,
    )
    monkeypatch.setattr(main, "now_ms", lambda: now)
    started = []
    monkeypatch.setattr(main, "start_ticker_refresh", lambda *args, **kwargs: started.append(True) or False)

    payload = main.cached_tickers(force=True)

    assert payload["data"][0]["instId"] == "BTC-USDT-SWAP"
    assert payload["source"] == "okx-stale-cache"
    assert payload["refresh"]["state"] == "backing_off"
    assert payload["refresh"]["nextRetryAt"] == now + 10_000
    assert payload["warning"] == ""
    assert "IncompleteRead" not in str(payload)
    assert started == []


def test_stale_ticker_snapshot_starts_one_background_refresh_after_backoff(monkeypatch):
    now = 2_000_000
    reset_ticker_cache(rows=[{"instId": "BTC-USDT-SWAP"}], ts=now - 30_000)
    monkeypatch.setattr(main, "now_ms", lambda: now)
    started = []

    def fake_start(started_now=None):
        started.append(started_now)
        with main.ticker_cache_condition:
            main.ticker_cache["refreshing"] = True
        return True

    monkeypatch.setattr(main, "start_ticker_refresh", fake_start)

    first = main.cached_tickers()
    second = main.cached_tickers()

    assert first["refresh"]["state"] == "refreshing"
    assert second["refresh"]["state"] == "refreshing"
    assert started == [now]


def test_first_load_without_snapshot_returns_explicit_safe_unavailable_state(monkeypatch):
    now = 3_000_000
    reset_ticker_cache()
    monkeypatch.setattr(main, "now_ms", lambda: now)
    monkeypatch.setattr(main, "load_ticker_snapshot", lambda: None)
    monkeypatch.setattr(main, "start_ticker_refresh", lambda *args, **kwargs: False)

    payload = main.cached_tickers()

    assert payload["data"] == []
    assert payload["source"] == "okx-unavailable"
    assert payload["refresh"]["state"] == "unavailable"
    assert payload["warning"] == "行情列表暂不可用，正在等待完整行情快照"


def test_background_ticker_failure_sets_backoff_without_retaining_raw_exception(monkeypatch):
    now = 4_000_000
    reset_ticker_cache(rows=[{"instId": "BTC-USDT-SWAP"}], ts=now - 30_000, refreshing=True)
    monkeypatch.setattr(main, "now_ms", lambda: now)
    monkeypatch.setattr(main, "refresh_ticker_cache_sync", lambda: (_ for _ in ()).throw(OkxError("IncompleteRead(12 bytes read)")))

    main.refresh_ticker_cache_background()
    rows, ts, refreshing, failures, retry_at = main.ticker_cache_values()

    assert rows[0]["instId"] == "BTC-USDT-SWAP"
    assert ts == now - 30_000
    assert refreshing is False
    assert failures == 1
    assert retry_at == now + main.TICKER_REFRESH_BACKOFF_BASE_MS
    assert main.ticker_cache["warning"] == ""
