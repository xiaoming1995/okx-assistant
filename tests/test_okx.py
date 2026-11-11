import http.client
import json

from backend.app.config import Settings
from backend.app.okx import OkxClient, OkxError, net_mode_retry_payload, parse_okx_candles


def test_parse_okx_candles_returns_ascending_rows():
    rows = [
        ["2000", "2", "3", "1", "2.5", "10", "20", "25", "0"],
        ["1000", "1", "2", "0.5", "1.5", "8", "12", "14", "1"],
    ]

    parsed = parse_okx_candles(rows)

    assert [item["ts"] for item in parsed] == ["1000", "2000"]
    assert parsed[0]["close"] == "1.5"
    assert parsed[1]["confirm"] == "0"


def test_history_candles_uses_the_market_history_endpoint(monkeypatch):
    settings = Settings(
        api_key="",
        api_secret="",
        passphrase="",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=False,
        default_trading_environment="live",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    client = OkxClient(settings)
    captured = {}

    def request(method, path, *, query, auth):
        captured.update({"method": method, "path": path, "query": query, "auth": auth})
        return {"data": [["2000", "2", "3", "1", "2.5", "10", "20", "25", "1"]]}

    monkeypatch.setattr(client, "_request", request)

    candles = client.get_history_candles("BTC-USDT-SWAP", "15m", 80)

    assert captured == {
        "method": "GET",
        "path": "/api/v5/market/history-candles",
        "query": {"instId": "BTC-USDT-SWAP", "bar": "15m", "limit": "80"},
        "auth": False,
    }
    assert candles[0]["volumeQuote"] == "25"


def test_place_order_posts_to_trade_endpoint_with_simulated_header(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[{"ordId":"1","clOrdId":"abc","sCode":"0"}]}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["timeout"] = timeout
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)

    response = OkxClient(settings).place_order(
        {
            "instId": "BTC-USDT-SWAP",
            "tdMode": "cross",
            "side": "buy",
            "ordType": "limit",
            "px": "100",
            "sz": "1",
            "clOrdId": "abc",
        }
    )

    assert captured["url"] == "https://openapi.okx.com/api/v5/trade/order"
    assert captured["method"] == "POST"
    assert captured["body"]["instId"] == "BTC-USDT-SWAP"
    assert captured["headers"]["x-simulated-trading"] == "1"
    assert captured["timeout"] == 7
    assert response["data"][0]["ordId"] == "1"


def test_close_position_posts_to_close_position_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[{"instId":"BTC-USDT-SWAP","posSide":"long","clOrdId":"abc"}]}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["timeout"] = timeout
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)

    response = OkxClient(settings).close_position(
        {
            "instId": "BTC-USDT-SWAP",
            "mgnMode": "cross",
            "posSide": "long",
            "autoCxl": False,
            "clOrdId": "abc",
        }
    )

    assert captured["url"] == "https://openapi.okx.com/api/v5/trade/close-position"
    assert captured["method"] == "POST"
    assert captured["body"]["mgnMode"] == "cross"
    assert captured["body"]["posSide"] == "long"
    assert captured["headers"]["x-simulated-trading"] == "1"
    assert captured["timeout"] == 7
    assert response["data"][0]["posSide"] == "long"


def test_leverage_info_fetches_account_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[{"instId":"BTC-USDT-SWAP","lever":"50","mgnMode":"cross","posSide":"net"}]}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["timeout"] = timeout
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)

    response = OkxClient(settings).get_leverage_info("BTC-USDT-SWAP", "cross")

    assert captured["url"] == "https://openapi.okx.com/api/v5/account/leverage-info?instId=BTC-USDT-SWAP&mgnMode=cross"
    assert captured["method"] == "GET"
    assert captured["headers"]["x-simulated-trading"] == "1"
    assert captured["timeout"] == 7
    assert response["data"][0]["lever"] == "50"


def test_contract_trading_statistics_fetch_public_rubik_endpoints(monkeypatch):
    captured_urls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[["1701417600000","1.2","3","4"]]}'

    def fake_urlopen(request, timeout):
        captured_urls.append(request.full_url)
        return FakeResponse()

    settings = Settings(
        api_key="",
        api_secret="",
        passphrase="",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=False,
        default_trading_environment="live",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)
    client = OkxClient(settings)

    client.get_contract_long_short_account_ratio("BTC-USDT-SWAP", "5m", 20)
    client.get_contract_taker_volume("BTC-USDT-SWAP", "5m", 20, unit="2")
    client.get_contract_open_interest_history("BTC-USDT-SWAP", "5m", 20)

    assert captured_urls == [
        "https://openapi.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract?instId=BTC-USDT-SWAP&period=5m&limit=20",
        "https://openapi.okx.com/api/v5/rubik/stat/taker-volume-contract?instId=BTC-USDT-SWAP&period=5m&limit=20&unit=2",
        "https://openapi.okx.com/api/v5/rubik/stat/contracts/open-interest-history?instId=BTC-USDT-SWAP&period=5m&limit=20",
    ]


def test_earn_client_fetches_read_only_finance_endpoints(monkeypatch):
    captured = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[{"productId":"4005","ccy":"USDT"}]}'

    def fake_urlopen(request, timeout):
        captured.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "headers": {key.lower(): value for key, value in request.header_items()},
                "timeout": timeout,
            }
        )
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)
    client = OkxClient(settings)

    client.get_staking_defi_offers(ccy="USDT", protocol_type="defi")
    client.get_staking_defi_active_orders(ccy="DOT", state="1")
    client.get_staking_defi_order_history(product_id="4005", limit=50)
    client.get_eth_staking_product_info()
    client.get_eth_staking_balance()
    client.get_eth_staking_history(request_type="purchase", status="success", limit=20)
    client.get_sol_staking_product_info()
    client.get_sol_staking_balance()
    client.get_sol_staking_history(request_type="redeem", status="pending", limit=20)

    assert [item["method"] for item in captured] == ["GET"] * 9
    assert captured[0]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/offers?protocolType=defi&ccy=USDT"
    assert captured[1]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/orders-active?ccy=DOT&state=1"
    assert captured[2]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/orders-history?productId=4005&limit=50"
    assert captured[3]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/eth/product-info"
    assert captured[4]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/eth/balance"
    assert captured[5]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/eth/purchase-redeem-history?type=purchase&status=success&limit=20"
    assert captured[6]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/sol/product-info"
    assert captured[7]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/sol/balance"
    assert captured[8]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/sol/purchase-redeem-history?type=redeem&status=pending&limit=20"
    assert all("ok-access-key" in item["headers"] for item in captured)
    assert all(item["headers"]["x-simulated-trading"] == "1" for item in captured)


def test_earn_client_fetches_public_staking_apy_endpoints(monkeypatch):
    captured = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[{"rate":"0.026","ts":"1700000000000"}]}'

    def fake_urlopen(request, timeout):
        captured.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "headers": {key.lower(): value for key, value in request.header_items()},
                "timeout": timeout,
            }
        )
        return FakeResponse()

    settings = Settings(
        api_key="",
        api_secret="",
        passphrase="",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=False,
        default_trading_environment="live",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)
    client = OkxClient(settings)

    client.get_eth_staking_apy_history(30)
    client.get_sol_staking_apy_history(30)

    assert captured[0]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/eth/apy-history?days=30"
    assert captured[1]["url"] == "https://openapi.okx.com/api/v5/finance/staking-defi/sol/apy-history?days=30"
    assert all("ok-access-key" not in item["headers"] for item in captured)


def test_announcement_client_fetches_public_support_endpoints_with_language(monkeypatch):
    captured = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            if "announcement-types" in captured[-1]["url"]:
                return b'{"code":"0","data":[{"annType":"announcements-api","annTypeDesc":"API announcements"}]}'
            return (
                b'{"code":"0","data":[{"details":[{"annType":"announcements-api","title":"API update",'
                b'"url":"https://www.okx.com/help/api-update","pTime":"1700000000000",'
                b'"businessPTime":"1700000100000"}],"totalPage":"2"}]}'
            )

    def fake_urlopen(request, timeout):
        captured.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "headers": {key.lower(): value for key, value in request.header_items()},
                "timeout": timeout,
            }
        )
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)
    client = OkxClient(settings)

    types = client.get_announcement_types("zh-CN")
    announcements = client.get_announcements("announcements-api", 2, "zh-CN")

    assert types[0]["annType"] == "announcements-api"
    assert announcements["totalPage"] == "2"
    assert captured[0]["url"] == "https://openapi.okx.com/api/v5/support/announcement-types"
    assert captured[1]["url"] == "https://openapi.okx.com/api/v5/support/announcements?annType=announcements-api&page=2"
    assert [item["method"] for item in captured] == ["GET", "GET"]
    assert all(item["headers"]["accept-language"] == "zh-CN" for item in captured)
    assert all("ok-access-key" not in item["headers"] for item in captured)
    assert all("x-simulated-trading" not in item["headers"] for item in captured)


def test_set_leverage_posts_to_account_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"code":"0","data":[{"instId":"BTC-USDT-SWAP","lever":"20","mgnMode":"isolated","posSide":"long"}]}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["timeout"] = timeout
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)

    response = OkxClient(settings).set_leverage(
        {
            "instId": "BTC-USDT-SWAP",
            "mgnMode": "isolated",
            "posSide": "long",
            "lever": "20",
        }
    )

    assert captured["url"] == "https://openapi.okx.com/api/v5/account/set-leverage"
    assert captured["method"] == "POST"
    assert captured["body"]["lever"] == "20"
    assert captured["body"]["posSide"] == "long"
    assert captured["headers"]["x-simulated-trading"] == "1"
    assert captured["timeout"] == 7
    assert response["data"][0]["lever"] == "20"


def test_okx_error_includes_order_row_rejection_detail(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return (
                b'{"code":"1","msg":"All operations failed","data":'
                b'[{"clOrdId":"abc","ordId":"","sCode":"51008",'
                b'"sMsg":"Order failed. Insufficient USDT balance in account","subCode":"1000"}]}'
            )

    def fake_urlopen(_request, timeout):
        assert timeout == 7
        return FakeResponse()

    settings = Settings(
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=True,
        default_trading_environment="simulated",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)

    try:
        OkxClient(settings).place_order(
            {
                "instId": "BTC-USDT-SWAP",
                "tdMode": "cross",
                "side": "buy",
                "ordType": "limit",
                "px": "100",
                "sz": "1",
                "clOrdId": "abc",
            }
        )
    except OkxError as exc:
        assert "51008/1000" in str(exc)
        assert "Insufficient USDT balance" in str(exc)
        assert exc.payload is not None
        assert exc.payload["data"][0]["sCode"] == "51008"
    else:
        raise AssertionError("Expected OKX error")


def test_okx_client_uses_valid_json_from_incomplete_read(monkeypatch):
    payload = b'{"code":"0","data":[{"instId":"BTC-USDT-SWAP","last":"64000"}]}'
    calls = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            calls["count"] += 1
            raise http.client.IncompleteRead(payload, 128)

    def fake_urlopen(_request, timeout=None):
        assert timeout == 7
        return FakeResponse()

    settings = Settings(
        api_key="",
        api_secret="",
        passphrase="",
        demo_api_key="",
        demo_api_secret="",
        demo_passphrase="",
        live_api_key="",
        live_api_secret="",
        live_passphrase="",
        base_url="https://openapi.okx.com",
        ws_public_url="wss://ws.okx.com:8443/ws/v5/public",
        simulated_trading=False,
        default_trading_environment="live",
        live_trading_enabled=False,
        timeout_seconds=7,
        database_url="sqlite:///ignored.sqlite3",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )
    monkeypatch.setattr("backend.app.okx.urlopen", fake_urlopen)

    response = OkxClient(settings).get_tickers()

    assert response[0]["instId"] == "BTC-USDT-SWAP"
    assert calls["count"] == 1


def test_net_mode_retry_payload_removes_long_short_pos_side():
    request_payload = {
        "instId": "BTC-USDT-SWAP",
        "tdMode": "cross",
        "side": "buy",
        "posSide": "long",
        "ordType": "limit",
        "px": "64000",
        "sz": "1",
    }
    exc = OkxError(
        "OKX API error 1: 51000: Parameter posSide error",
        {"code": "1", "data": [{"sCode": "51000", "sMsg": "Parameter posSide error "}]},
    )

    retry_payload = net_mode_retry_payload(request_payload, exc)

    assert retry_payload is not None
    assert "posSide" not in retry_payload
    assert request_payload["posSide"] == "long"
