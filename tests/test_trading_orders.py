from backend.app import main


def test_orders_for_environment_returns_filtered_paging(monkeypatch):
    calls = []

    class FakeDatabase:
        def list_sim_order_events(self, **kwargs):
            calls.append(("list", kwargs))
            return [{"ord_id": "BTC-3", "inst_id": "BTC-USDT-SWAP", "state": "accepted"}]

        def count_sim_order_events(self, **kwargs):
            calls.append(("count", kwargs))
            return 7

    class FakeSettings:
        live_trading_enabled = False

        def has_credentials_for_environment(self, environment):
            return False

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "settings", FakeSettings())

    payload = main.orders_for_environment(
        "simulated",
        instId="btc-usdt-swap",
        limit=2,
        offset=4,
        q="btc-3",
        action="place",
        state="accepted",
    )

    assert payload["events"][0]["ord_id"] == "BTC-3"
    assert payload["paging"] == {
        "limit": 2,
        "offset": 4,
        "hasMore": True,
        "total": 7,
        "page": 3,
        "pageCount": 4,
    }
    assert calls[0] == (
        "list",
        {
            "environment": "simulated",
            "inst_id": "BTC-USDT-SWAP",
            "limit": 2,
            "offset": 4,
            "keyword": "btc-3",
            "action": "place",
            "state": "accepted",
            "origin": "",
        },
    )
    assert calls[1] == (
        "count",
        {
            "environment": "simulated",
            "inst_id": "BTC-USDT-SWAP",
            "keyword": "btc-3",
            "action": "place",
            "state": "accepted",
            "origin": "",
        },
    )
