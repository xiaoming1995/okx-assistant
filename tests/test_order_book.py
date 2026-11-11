from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi import HTTPException

from backend.app import main
from backend.app.okx import OkxError


INST = "ETH-USDT-SWAP"


def raw_book(ts, asks=None, bids=None):
    return {
        "ts": str(ts),
        "asks": asks if asks is not None else [["101.2", "2", "0", "1"], ["101.1", "3", "0", "1"]],
        "bids": bids if bids is not None else [["100.9", "4", "0", "1"], ["100.8", "5", "0", "1"]],
    }


@pytest.fixture(autouse=True)
def clear_order_book_cache():
    with main.order_book_cache_condition:
        main.order_book_cache.clear()
    yield
    with main.order_book_cache_condition:
        main.order_book_cache.clear()


def test_normalization_orders_levels_keeps_decimal_strings_and_reports_spread():
    result = main.normalize_public_order_book(
        INST,
        raw_book(100_000, asks=[["101.2", "2.5"], ["101.1", "3.25"], ["bad", "1"], ["101.1", "9"]], bids=[["100.8", "5"], ["100.9", "4"]]),
        100_100,
    )

    assert result["asks"] == [
        {"price": "101.1", "size": "3.25", "cumulative": "3.25"},
        {"price": "101.2", "size": "2.5", "cumulative": "5.75"},
    ]
    assert result["bids"][0] == {"price": "100.9", "size": "4", "cumulative": "4"}
    assert result["spread"]["absolute"] == "0.2"
    assert result["ts"] == 100_000


def test_empty_one_sided_and_crossed_books_do_not_claim_normal_spread():
    empty = main.normalize_public_order_book(INST, raw_book(100_000, asks=[], bids=[]), 100_000)
    one_side = main.normalize_public_order_book(INST, raw_book(100_000, bids=[]), 100_000)
    crossed = main.normalize_public_order_book(INST, raw_book(100_000, asks=[["100", "1"]], bids=[["101", "1"]]), 100_000)

    assert empty["asks"] == empty["bids"] == []
    assert empty["spread"] is None
    assert one_side["spread"] is None and "单侧" in one_side["warning"]
    assert crossed["spread"] is None and "交叉" in crossed["warning"]


def test_cache_reuses_fresh_snapshot_and_hides_expired_data_after_failure(monkeypatch):
    clock = {"now": 100_000}
    calls = []

    def fetch_book(inst_id, depth):
        calls.append((inst_id, depth))
        if len(calls) > 1:
            raise OkxError("private transport failure details")
        return raw_book(clock["now"])

    monkeypatch.setattr(main, "now_ms", lambda: clock["now"])
    monkeypatch.setattr(main.client, "get_order_book", fetch_book)

    first = main.cached_order_book(INST)
    clock["now"] += 1_000
    second = main.cached_order_book(INST)
    assert first["state"] == second["state"] == "fresh"
    assert calls == [(INST, 10)]

    clock["now"] += 2_000
    retained = main.cached_order_book(INST)
    assert retained["state"] == "cached" and retained["data"] is not None
    assert "private transport" not in str(retained)

    clock["now"] += 16_000
    expired = main.cached_order_book(INST)
    assert expired["data"] is None and expired["state"] == "unavailable"


def test_concurrent_requests_coalesce_while_first_snapshot_is_loading(monkeypatch):
    entered, release = Event(), Event()
    calls = []
    monkeypatch.setattr(main, "now_ms", lambda: 100_000)

    def fetch_book(inst_id, depth):
        calls.append((inst_id, depth))
        entered.set()
        assert release.wait(5)
        return raw_book(100_000)

    monkeypatch.setattr(main.client, "get_order_book", fetch_book)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(main.cached_order_book, INST)
        assert entered.wait(5)
        pending = main.cached_order_book(INST)
        release.set()
        complete = first.result(timeout=5)

    assert pending["state"] == "loading" and pending["data"] is None
    assert complete["state"] == "fresh"
    assert calls == [(INST, 10)]


def test_endpoint_rejects_unknown_or_invalid_contract(monkeypatch):
    monkeypatch.setattr(main.database, "list_instruments", lambda **kwargs: [])
    with pytest.raises(HTTPException) as invalid:
        main.market_order_book("BTC-USDT")
    with pytest.raises(HTTPException) as unknown:
        main.market_order_book(INST)
    assert invalid.value.status_code == 400
    assert unknown.value.status_code == 404


def test_public_client_caps_depth_and_never_requests_auth(monkeypatch):
    observed = []

    def fake_request(method, path, **kwargs):
        observed.append((method, path, kwargs))
        return {"data": [raw_book(100_000)]}

    monkeypatch.setattr(main.client, "_request", fake_request)
    book = main.client.get_order_book(INST, 50)

    assert book["ts"] == "100000"
    assert observed == [("GET", "/api/v5/market/books", {"query": {"instId": INST, "sz": "10"}, "auth": False})]
