import pytest

from backend.app import main
from backend.app.okx import OkxError


def reset_earn_cache():
    with main.earn_cache_lock:
        main.earn_cache.clear()


def test_earn_product_and_order_normalization_preserves_raw_state():
    product = main.normalize_earn_product(
        {
            "ccy": "dot",
            "productId": "101",
            "protocol": "Polkadot",
            "protocolType": "defi",
            "term": "0",
            "apy": "0.1767",
            "earlyRedeem": False,
            "state": "purchasable",
            "investData": [{"ccy": "DOT", "bal": "5", "minAmt": "2", "maxAmt": "10"}],
            "earningData": [{"ccy": "DOT", "earningType": "0"}],
            "redeemPeriod": ["28D", "28D"],
            "fastRedemptionDailyLimit": "",
        }
    )
    active = main.normalize_earn_order(
        {
            "ordId": "2413499",
            "ccy": "DOT",
            "productId": "101",
            "state": "1",
            "protocol": "Polkadot",
            "protocolType": "defi",
            "term": "0",
            "apy": "0.1014",
            "investData": [{"ccy": "DOT", "amt": "2"}],
            "earningData": [{"ccy": "DOT", "earningType": "0", "earnings": "0.10615025"}],
        }
    )
    history = main.normalize_earn_order({"ordId": "1579252", "ccy": "DOT", "state": "3"}, historical=True)

    assert product["stateLabel"] == "可申购"
    assert product["investData"][0]["minAmt"] == "2"
    assert product["redeemPeriod"] == ["28D", "28D"]
    assert active["stateLabel"] == "收益中"
    assert active["earningData"][0]["earningTypeLabel"] == "预估收益"
    assert history["stateLabel"] == "已完成"
    assert history["state"] == "3"


def test_earn_validation_rejects_unsupported_protocol_and_state():
    assert main.normalize_earn_protocol_type("STAKING") == "staking"
    assert main.normalize_earn_protocol_type("defi") == "defi"
    assert main.normalize_earn_protocol_type("") == ""
    with pytest.raises(Exception):
        main.normalize_earn_protocol_type("savings")
    with pytest.raises(Exception):
        main.normalize_earn_active_state("3")
    with pytest.raises(Exception):
        main.normalize_earn_staking_history_status("done")


def test_earn_unconfigured_response_is_section_scoped(monkeypatch):
    reset_earn_cache()

    class FakeSettings:
        def has_credentials_for_environment(self, environment):
            return False

    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "current_earn_environment", lambda: "live")

    payload = main.build_earn_active_orders("", "defi", "", "", force=True)

    assert payload["configured"] is False
    assert payload["section"] == "active-orders"
    assert payload["source"] == "not-configured"
    assert payload["data"] == []
    assert "真实盘 API Key 未配置" in payload["message"]


def test_earn_environment_is_live_even_when_trading_environment_is_simulated():
    previous = main.active_trading_environment
    try:
        main.active_trading_environment = "simulated"
        earn_client = main.earn_client_for_environment(main.current_earn_environment())

        assert main.current_earn_environment() == "live"
        assert earn_client.settings.simulated_trading is False
    finally:
        main.active_trading_environment = previous


def test_earn_cache_returns_stale_data_when_refresh_fails(monkeypatch):
    reset_earn_cache()

    class FakeSettings:
        def has_credentials_for_environment(self, environment):
            return True

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_staking_defi_active_orders(self, *_args):
            self.calls += 1
            if self.calls == 1:
                return [{"ordId": "1", "ccy": "USDT", "state": "1"}]
            raise OkxError("rate limited")

    fake_client = FakeClient()
    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "current_earn_environment", lambda: "live")
    monkeypatch.setattr(main, "earn_client_for_environment", lambda environment: fake_client)
    monkeypatch.setattr(main, "now_ms", lambda: 100000)

    first = main.build_earn_active_orders("", "defi", "", "", force=True)
    second = main.build_earn_active_orders("", "defi", "", "", force=True)

    assert first["source"] == "okx-earn-active-orders"
    assert second["source"] == "earn-active-orders-stale-cache"
    assert second["data"][0]["ordId"] == "1"
    assert any("rate limited" in warning for warning in second["warnings"])


def test_earn_staking_overview_keeps_public_data_without_credentials(monkeypatch):
    reset_earn_cache()

    class FakeSettings:
        def has_credentials_for_environment(self, environment):
            return False

    class FakeClient:
        def get_eth_staking_product_info(self):
            raise AssertionError("product info must not be requested without credentials")

        def get_eth_staking_apy_history(self, days):
            return [{"rate": "0.0269", "ts": "1734195600000"}]

        def get_eth_staking_balance(self):
            raise AssertionError("balance must not be requested without credentials")

        def get_eth_staking_history(self, *_args):
            raise AssertionError("history must not be requested without credentials")

    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "current_earn_environment", lambda: "live")
    monkeypatch.setattr(main, "earn_client_for_environment", lambda environment: FakeClient())

    payload = main.build_earn_staking_overview("ETH", "", "", "", "", 100, 30, force=True)

    assert payload["configured"] is False
    assert payload["productInfo"] == {}
    assert payload["apyPoints"][0]["rate"] == "0.0269"
    assert payload["balances"] == []
    assert payload["history"] == []
    assert any("产品信息、余额和申购赎回记录不可用" in warning for warning in payload["warnings"])


def test_earn_routes_are_get_only():
    earn_routes = [route for route in main.app.routes if getattr(route, "path", "").startswith("/api/earn")]

    assert earn_routes
    assert {route.path for route in earn_routes} == {
        "/api/earn/offers",
        "/api/earn/orders/active",
        "/api/earn/orders/history",
        "/api/earn/eth",
        "/api/earn/sol",
    }
    assert all(getattr(route, "methods", set()) == {"GET"} for route in earn_routes)
