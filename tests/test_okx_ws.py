import base64
import hashlib
import hmac

import pytest

from backend.app.config import Settings
from backend.app.okx_ws import (
    candle_channel,
    okx_ws_error_from_payload,
    private_login_payload,
    private_subscribe_args,
    public_candle_subscribe_args,
    public_ticker_subscribe_args,
)


def test_candle_channel_maps_supported_bars():
    assert candle_channel("1m") == "candle1m"
    assert candle_channel("1H") == "candle1H"
    assert candle_channel("1D") == "candle1D"


def test_candle_channel_rejects_unsupported_bar():
    with pytest.raises(RuntimeError, match="Unsupported K-line interval"):
        candle_channel("30m")


def test_public_ticker_subscribe_args_normalizes_unique_instruments():
    assert public_ticker_subscribe_args([" btc-usdt-swap ", "BTC-USDT-SWAP", "eth-usdt-swap"]) == [
        {"channel": "tickers", "instId": "BTC-USDT-SWAP"},
        {"channel": "tickers", "instId": "ETH-USDT-SWAP"},
    ]


def test_public_candle_subscribe_args_uses_candle_channel():
    assert public_candle_subscribe_args(" btc-usdt-swap ", "1m") == [
        {"channel": "candle1m", "instId": "BTC-USDT-SWAP"}
    ]


def test_okx_ws_error_from_payload_extracts_invalid_ticker_instrument():
    error = okx_ws_error_from_payload(
        {
            "event": "error",
            "code": "60018",
            "msg": (
                "Subscribe failed, wrong URL or channel:tickers,instId:0G-USDT-SWAP doesn't exist. "
                "Please use the correct URL, channel and parameters referring to API document."
            ),
        }
    )

    assert error.code == "60018"
    assert error.channel == "tickers"
    assert error.inst_id == "0G-USDT-SWAP"


def test_private_subscribe_args_maps_supported_topics():
    assert private_subscribe_args({"account", "positions", "orders"}) == [
        {"channel": "account"},
        {"channel": "positions", "instType": "ANY"},
        {"channel": "orders", "instType": "ANY"},
    ]


def test_private_login_payload_uses_ws_verify_signature():
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
        ws_demo_public_url="wss://wspap.okx.com:8443/ws/v5/public",
        ws_private_url="wss://ws.okx.com:8443/ws/v5/private",
        ws_demo_private_url="wss://wspap.okx.com:8443/ws/v5/private",
        simulated_trading=False,
        default_trading_environment="live",
        live_trading_enabled=False,
        timeout_seconds=10,
        database_url="sqlite:///:memory:",
        ticker_cache_seconds=15,
        ticker_stale_seconds=300,
        account_cache_seconds=20,
        account_stale_seconds=600,
    )

    payload = private_login_payload(settings, timestamp="1538054050")

    assert payload["op"] == "login"
    assert payload["args"][0]["apiKey"] == "key"
    assert payload["args"][0]["passphrase"] == "pass"
    assert payload["args"][0]["timestamp"] == "1538054050"
    expected = base64.b64encode(
        hmac.new(b"secret", b"1538054050GET/users/self/verify", hashlib.sha256).digest()
    ).decode("utf-8")
    assert payload["args"][0]["sign"] == expected
