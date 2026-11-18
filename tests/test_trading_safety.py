"""交易模块 P0 加固：环境隔离、撤单透传、手动幂等键。"""

import pytest
from fastapi import HTTPException

from backend.app import main


def test_resolve_request_environment_prefers_explicit(monkeypatch):
    monkeypatch.setattr(main, "current_trading_environment", lambda: "live")
    assert main.resolve_request_environment("simulated") == "simulated"
    assert main.resolve_request_environment("live") == "live"


def test_resolve_request_environment_falls_back_when_blank(monkeypatch):
    monkeypatch.setattr(main, "current_trading_environment", lambda: "simulated")
    assert main.resolve_request_environment(None) == "simulated"
    assert main.resolve_request_environment("") == "simulated"
    assert main.resolve_request_environment("   ") == "simulated"


def test_resolve_request_environment_rejects_invalid(monkeypatch):
    monkeypatch.setattr(main, "current_trading_environment", lambda: "simulated")
    with pytest.raises(HTTPException) as exc:
        main.resolve_request_environment("production")
    assert exc.value.status_code == 400


def test_place_route_uses_request_environment_and_cl_ord_id(monkeypatch):
    captured = {}

    def fake_place(env, order, cl_ord_id=None, origin=main.ORDER_ORIGIN_MANUAL):
        captured["env"] = env
        captured["cl_ord_id"] = cl_ord_id
        return {"ok": True, "environment": env, "event": {}}

    monkeypatch.setattr(main, "place_order_for_environment", fake_place)
    monkeypatch.setattr(main, "current_trading_environment", lambda: "live")

    order = main.PlaceSimOrderRequest(
        instId="BTC-USDT-SWAP",
        side="buy",
        ordType="market",
        sz="1",
        environment="simulated",
        clOrdId="OKXQTESTID0001",
    )
    main.place_trading_order(order)
    assert captured["env"] == "simulated"
    assert captured["cl_ord_id"] == "OKXQTESTID0001"


def test_place_route_falls_back_to_global_environment(monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "current_trading_environment", lambda: "live")

    def fake_place(env, order, cl_ord_id=None, origin=main.ORDER_ORIGIN_MANUAL):
        captured["env"] = env
        return {"ok": True}

    monkeypatch.setattr(main, "place_order_for_environment", fake_place)
    order = main.PlaceSimOrderRequest(
        instId="BTC-USDT-SWAP", side="buy", ordType="market", sz="1"
    )
    main.place_trading_order(order)
    assert captured["env"] == "live"


def test_cancel_route_uses_request_environment(monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "current_trading_environment", lambda: "live")

    def fake_cancel(env, order):
        captured["env"] = env
        return {"ok": True}

    monkeypatch.setattr(main, "cancel_order_for_environment", fake_cancel)
    order = main.CancelSimOrderRequest(
        instId="BTC-USDT-SWAP", ordId="ORD1", environment="simulated"
    )
    main.cancel_trading_order(order)
    assert captured["env"] == "simulated"


def test_close_route_uses_request_environment(monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "current_trading_environment", lambda: "simulated")

    def fake_close(env, order, origin=main.ORDER_ORIGIN_MANUAL):
        captured["env"] = env
        return {"ok": True}

    monkeypatch.setattr(main, "close_position_for_environment", fake_close)
    order = main.ClosePositionRequest(
        instId="BTC-USDT-SWAP", mgnMode="cross", environment="live"
    )
    main.close_trading_position(order)
    assert captured["env"] == "live"


def test_build_place_payload_keeps_provided_cl_ord_id():
    order = main.PlaceSimOrderRequest(
        instId="BTC-USDT-SWAP", side="buy", ordType="market", sz="1",
        clOrdId="OKXQMANUAL0001",
    )
    payload = main.build_place_order_payload(order, cl_ord_id=order.clOrdId)
    assert payload["clOrdId"] == "OKXQMANUAL0001"


def test_environment_is_not_forwarded_to_okx_payload():
    order = main.PlaceSimOrderRequest(
        instId="BTC-USDT-SWAP", side="buy", ordType="market", sz="1",
        environment="simulated", clOrdId="OKXQMANUAL0002",
    )
    payload = main.build_place_order_payload(order, cl_ord_id=order.clOrdId)
    assert "environment" not in payload
    assert payload["clOrdId"] == "OKXQMANUAL0002"


# ---------- P1-1：服务端下单规格强校验 ----------

def test_validate_order_spec_passes_when_spec_missing():
    payload = {"instId": "BTC-USDT-SWAP", "sz": "0.123", "px": "50000.123"}
    main.validate_order_spec(payload, None)  # 规格缺失应降级放行，不抛异常


def test_validate_order_spec_accepts_valid_order():
    spec = {"lot_sz": "1", "tick_sz": "0.1", "ct_val": "0.01"}
    payload = {"instId": "BTC-USDT-SWAP", "sz": "2", "px": "50000.5"}
    main.validate_order_spec(payload, spec)  # 2 是 1 的倍数，50000.5 是 0.1 的倍数，名义 1000 USDT


def test_validate_order_spec_rejects_non_multiple_size():
    spec = {"lot_sz": "1", "tick_sz": "0.1", "ct_val": "0.01"}
    payload = {"instId": "BTC-USDT-SWAP", "sz": "1.5", "px": "50000"}
    with pytest.raises(HTTPException) as exc:
        main.validate_order_spec(payload, spec)
    assert exc.value.status_code == 400
    assert "整数倍" in exc.value.detail
    assert "数量" in exc.value.detail


def test_validate_order_spec_rejects_non_multiple_price():
    spec = {"lot_sz": "1", "tick_sz": "0.1", "ct_val": "0.01"}
    payload = {"instId": "BTC-USDT-SWAP", "sz": "2", "px": "50000.05"}
    with pytest.raises(HTTPException) as exc:
        main.validate_order_spec(payload, spec)
    assert exc.value.status_code == 400
    assert "报价单位" in exc.value.detail


def test_validate_order_spec_rejects_tiny_notional():
    spec = {"lot_sz": "0.001", "tick_sz": "0.1", "ct_val": "0.0001"}
    payload = {"instId": "DOGE-USDT-SWAP", "sz": "0.001", "px": "0.1"}
    with pytest.raises(HTTPException) as exc:
        main.validate_order_spec(payload, spec)
    assert exc.value.status_code == 400
    assert "名义价值" in exc.value.detail


def test_validate_order_spec_skips_notional_for_market_order():
    spec = {"lot_sz": "1", "tick_sz": "0.1", "ct_val": "0.0001"}
    payload = {"instId": "BTC-USDT-SWAP", "sz": "1"}  # 市价单无 px，跳过名义价值校验
    main.validate_order_spec(payload, spec)


def test_resolve_instrument_spec_matches_by_inst_id(monkeypatch):
    class FakeDb:
        def list_instruments(self, query="", limit=200):
            return [
                {"inst_id": "ETH-USDT-SWAP", "lot_sz": "0.1"},
                {"inst_id": "BTC-USDT-SWAP", "lot_sz": "1", "tick_sz": "0.1", "ct_val": "0.01"},
            ]

    monkeypatch.setattr(main, "database", FakeDb())
    spec = main.resolve_instrument_spec("btc-usdt-swap")
    assert spec is not None and spec["lot_sz"] == "1"
    assert main.resolve_instrument_spec("unknown-swap") is None


def test_place_route_applies_spec_validation_before_okx(monkeypatch):
    """端到端：规格不满足时，下单链路在打 OKX 之前就抛 400。"""
    monkeypatch.setattr(main, "require_trading_enabled", lambda env: None)
    client_calls = []

    class FakeClient:
        def place_order(self, payload):
            client_calls.append(payload)
            return {"code": "0", "data": [{"sCode": "0"}]}

    monkeypatch.setattr(main, "client_for_environment", lambda env: FakeClient())
    monkeypatch.setattr(
        main, "resolve_instrument_spec",
        lambda inst: {"lot_sz": "1", "tick_sz": "0.1", "ct_val": "0.01"},
    )
    order = main.PlaceSimOrderRequest(
        instId="BTC-USDT-SWAP", side="buy", ordType="limit", sz="1.5", px="50000.05",
        environment="simulated",
    )
    with pytest.raises(HTTPException) as exc:
        main.place_order_for_environment("simulated", order)
    assert exc.value.status_code == 400
    assert client_calls == []  # OKX 未被调用


# ---------- P2-1：结算账单翻页接入 ----------

def test_settlement_index_uses_paged_bills(monkeypatch):
    main.settlement_cache.clear()
    calls = []

    class FakeClient:
        def get_all_trade_bills(self, bill_type="2", limit=100):
            calls.append((bill_type, limit))
            return [
                {"billId": "b1", "clOrdId": "ORD1", "pnl": "10", "fee": "-1"},
                {"billId": "b2", "clOrdId": "ORD2", "pnl": "5", "fee": "-0.5"},
            ]

    class FakeSettings:
        def has_credentials_for_environment(self, env):
            return True

    monkeypatch.setattr(main, "client_for_environment", lambda env: FakeClient())
    monkeypatch.setattr(main, "settings", FakeSettings())
    index = main.settlement_bills_index("simulated", force=True)
    assert calls and calls[0] == ("2", 100)
    assert "ORD1" in index and "ORD2" in index
    assert index["ORD1"]["pnl_gross"] == "10.00"


def test_settlement_index_falls_back_to_single_page_for_legacy_client(monkeypatch):
    main.settlement_cache.clear()
    calls = []

    class LegacyClient:
        def get_trade_bills(self, bill_type="2", limit=100):
            calls.append((bill_type, limit))
            return [{"billId": "b1", "clOrdId": "ORD1", "pnl": "3", "fee": "0"}]

    class FakeSettings:
        def has_credentials_for_environment(self, env):
            return True

    monkeypatch.setattr(main, "client_for_environment", lambda env: LegacyClient())
    monkeypatch.setattr(main, "settings", FakeSettings())
    index = main.settlement_bills_index("simulated", force=True)
    assert calls == [("2", 100)]
    assert "ORD1" in index
