import asyncio

import pytest
from fastapi import WebSocketDisconnect

from backend.app import main
from backend.app.okx_ws import OkxWsError
from backend.app.realtime import normalize_inst_ids, normalize_subscription_message, topic_matches


class NoCredentialSettings:
    base_url = "https://openapi.okx.com"
    database_label = "sqlite:///:memory:"
    ws_public_url = "wss://public.example/ws"
    ws_business_url = "wss://business.example/ws"
    account_cache_seconds = 20
    account_stale_seconds = 600
    live_trading_enabled = False

    def has_credentials_for_environment(self, environment):
        return False

    def ws_public_url_for_environment(self, environment):
        return "wss://demo-public.example/ws" if environment == "simulated" else "wss://public.example/ws"

    def ws_business_url_for_environment(self, environment):
        return "wss://demo-business.example/ws" if environment == "simulated" else "wss://business.example/ws"

    def ws_private_url_for_environment(self, environment):
        return "wss://demo-private.example/ws" if environment == "simulated" else "wss://private.example/ws"

    def for_environment(self, environment):
        return self

    def require_credentials(self):
        raise ValueError("missing credentials")


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def receive_json(self):
        if not self.messages:
            await asyncio.sleep(0.01)
            raise WebSocketDisconnect()
        return self.messages.pop(0)

    async def send_json(self, payload):
        self.sent.append(payload)


def candle(timestamp: int, close: str = "2"):
    return {
        "ts": str(timestamp),
        "open": "1",
        "high": "3",
        "low": "0.5",
        "close": close,
        "volume": "10",
    }


def test_realtime_subscription_helpers_validate_topics_and_instruments():
    topics, errors = normalize_subscription_message(
        {"topics": ["market.ticker", "orders", "unknown"], "instIds": [" btc-usdt-swap ", "BTC-USDT-SWAP"]}
    )

    assert topics == {"market.ticker", "orders"}
    assert errors == ["unknown"]
    assert normalize_inst_ids({"instIds": [" btc-usdt-swap ", "BTC-USDT-SWAP"], "instId": "eth-usdt-swap"}) == [
        "BTC-USDT-SWAP",
        "ETH-USDT-SWAP",
    ]
    assert topic_matches("automation", "automation.alert")
    assert topic_matches("market", "market.ticker")
    assert not topic_matches("orders", "account")


@pytest.mark.anyio
async def test_realtime_feed_rejects_unsupported_topic_and_keeps_connection(monkeypatch):
    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    websocket = FakeWebSocket([
        {"op": "subscribe", "topics": ["unknown-topic"]},
        {"op": "ping"},
    ])

    await main.realtime_socket(websocket)

    assert websocket.accepted is True
    assert websocket.sent[0]["type"] == "status"
    assert any(item["type"] == "error" and item["topic"] == "unknown-topic" for item in websocket.sent)
    assert any(item["type"] == "pong" for item in websocket.sent)


@pytest.mark.anyio
async def test_realtime_private_topic_without_credentials_sends_disabled_state(monkeypatch):
    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    websocket = FakeWebSocket([
        {"op": "subscribe", "topics": ["account"], "environment": "simulated"},
    ])

    await main.realtime_socket(websocket)

    assert websocket.sent[0]["type"] == "status"
    status = next(item for item in websocket.sent if item.get("topics") == ["account"])
    disabled = next(item for item in websocket.sent if item.get("type") == "disabled")

    assert status["type"] == "status"
    assert disabled["topic"] == "account"
    assert disabled["refreshRequired"] is True


@pytest.mark.anyio
async def test_realtime_candles_use_primary_instrument_when_tickers_subscribe_to_visible_list(monkeypatch):
    calls = []

    async def fake_candle_sender(session, environment, inst_id, bar):
        calls.append(("candles", environment, inst_id, bar))

    async def fake_ticker_sender(session, environment, inst_ids):
        calls.append(("ticker", environment, inst_ids))

    monkeypatch.setattr(main, "realtime_public_candle_sender", fake_candle_sender)
    monkeypatch.setattr(main, "realtime_public_ticker_sender", fake_ticker_sender)

    tasks = main.realtime_tasks_for_subscription(
        None,
        {
            "topics": ["market.candles", "market.ticker"],
            "instId": "btc-usdt-swap",
            "instIds": ["ach-usdt-swap", "btc-usdt-swap"],
            "bar": "1m",
            "environment": "simulated",
        },
        {"market.candles", "market.ticker"},
    )
    await asyncio.gather(*tasks)

    assert ("candles", "simulated", "BTC-USDT-SWAP", "1m") in calls
    assert ("ticker", "simulated", ["BTC-USDT-SWAP", "ACH-USDT-SWAP"]) in calls


@pytest.mark.anyio
async def test_realtime_candle_sender_uses_business_websocket_url(monkeypatch):
    calls = []
    sent = []

    class FakeClient:
        def get_candles(self, inst_id, bar, limit):
            return []

    class FakeHub:
        async def send(self, session, payload):
            sent.append(payload)
            return payload.get("type") != "status"

    async def fake_stream_public_candles(ws_url, inst_id, bar):
        calls.append((ws_url, inst_id, bar))
        yield {"type": "status", "topic": "market.candles", "source": "okx-ws", "message": "subscribed", "ts": 1}

    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    monkeypatch.setattr(main, "client_for_environment", lambda environment: FakeClient())
    monkeypatch.setattr(main.database, "latest_candles", lambda inst_id, bar, limit: [])
    monkeypatch.setattr(main.database, "upsert_candles", lambda inst_id, bar, rows: None)
    monkeypatch.setattr(main, "stream_public_candles", fake_stream_public_candles)
    monkeypatch.setattr(main, "realtime_hub", FakeHub())

    await main.realtime_public_candle_sender(None, "simulated", "BTC-USDT-SWAP", "1m")

    assert calls == [("wss://demo-business.example/ws", "BTC-USDT-SWAP", "1m")]
    assert sent[0]["source"] == "cache-degraded"
    assert sent[0]["snapshot"]["instId"] == "BTC-USDT-SWAP"
    assert sent[0]["snapshot"]["bar"] == "1m"


def test_candle_batch_normalization_and_suitability_filters_invalid_duplicate_and_gapped_rows():
    interval = main.CANDLE_BAR_MILLISECONDS["15m"]
    base = 1_700_000_000_000
    normalized = main.normalize_candle_batch([
        candle(base + interval, "3"),
        {"ts": "invalid"},
        candle(base, "1"),
        candle(base + interval, "4"),
        candle(-1),
    ])

    assert [row["ts"] for row in normalized] == [str(base), str(base + interval)]
    assert normalized[-1]["close"] == "4"
    assert main.candle_batch_issue(normalized, "15m", current_ms=base + (2 * interval)) is None
    assert main.candle_batch_issue(
        [candle(base), candle(base + (3 * interval))], "15m", current_ms=base + (3 * interval)
    ) == "gap"
    assert main.candle_batch_issue([candle(base)], "15m", current_ms=base + (4 * interval)) == "stale"


@pytest.mark.anyio
async def test_realtime_candle_sender_skips_unsuitable_cache_until_rest_seed(monkeypatch):
    interval = main.CANDLE_BAR_MILLISECONDS["15m"]
    current = 1_700_000_000_000
    cached = [candle(current - (4 * interval)), candle(current)]
    fresh = [candle(current - interval), candle(current)]
    sent = []

    class FakeClient:
        def get_candles(self, inst_id, bar, limit):
            return fresh

    class FakeHub:
        async def send(self, session, payload):
            sent.append(payload)
            return payload.get("type") != "status"

    async def fake_stream_public_candles(ws_url, inst_id, bar):
        yield {"type": "status", "topic": "market.candles", "source": "okx-ws", "message": "subscribed", "ts": current}

    monkeypatch.setattr(main, "now_ms", lambda: current)
    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    monkeypatch.setattr(main, "client_for_environment", lambda environment: FakeClient())
    monkeypatch.setattr(main.database, "latest_candles", lambda inst_id, bar, limit: cached)
    monkeypatch.setattr(main.database, "upsert_candles", lambda inst_id, bar, rows: None)
    monkeypatch.setattr(main, "stream_public_candles", fake_stream_public_candles)
    monkeypatch.setattr(main, "realtime_hub", FakeHub())

    await main.realtime_public_candle_sender(None, "simulated", "BTC-USDT-SWAP", "15m")

    assert not any(payload.get("source") == "cache-seed" for payload in sent)
    rest_seed = next(payload for payload in sent if payload.get("source") == "rest-seed")
    assert rest_seed["data"] == fresh
    assert rest_seed["snapshot"]["candleCount"] == len(fresh)
    assert rest_seed["snapshot"]["source"] == "rest-seed"


@pytest.mark.anyio
async def test_realtime_candle_sender_marks_only_persisted_gap_as_degraded(monkeypatch):
    interval = main.CANDLE_BAR_MILLISECONDS["15m"]
    current = 1_700_000_000_000
    cached = [candle(current - (4 * interval)), candle(current)]
    sent = []

    class FailingClient:
        def get_candles(self, inst_id, bar, limit):
            raise RuntimeError("OKX unavailable")

    class FakeHub:
        async def send(self, session, payload):
            sent.append(payload)
            return payload.get("source") != "cache-degraded"

    monkeypatch.setattr(main, "now_ms", lambda: current)
    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    monkeypatch.setattr(main, "client_for_environment", lambda environment: FailingClient())
    monkeypatch.setattr(main.database, "latest_candles", lambda inst_id, bar, limit: cached)
    monkeypatch.setattr(main, "realtime_hub", FakeHub())

    await main.realtime_public_candle_sender(None, "simulated", "BTC-USDT-SWAP", "15m")

    degraded = next(payload for payload in sent if payload.get("source") == "cache-degraded")
    assert degraded["data"] == cached
    assert "时间断层" in degraded["warning"]


@pytest.mark.anyio
async def test_realtime_ticker_sender_skips_invalid_ws_instrument_without_global_error(monkeypatch):
    calls = []
    sent = []

    class FakeHub:
        async def send(self, session, payload):
            sent.append(payload)
            return payload.get("source") != "partial-fallback"

    async def fake_stream_public_tickers(ws_url, inst_ids):
        calls.append((ws_url, list(inst_ids)))
        if "0G-USDT-SWAP" in inst_ids:
            raise OkxWsError(
                "OKX WebSocket error 60018: Subscribe failed, wrong URL or channel:tickers,instId:0G-USDT-SWAP doesn't exist.",
                code="60018",
                channel="tickers",
                inst_id="0G-USDT-SWAP",
            )
        await asyncio.sleep(0.01)
        yield {"type": "status", "topic": "market.ticker", "source": "okx-ws", "message": "subscribed", "ts": 1}

    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    monkeypatch.setattr(main, "stream_public_tickers", fake_stream_public_tickers)
    monkeypatch.setattr(main, "realtime_hub", FakeHub())

    await main.realtime_public_ticker_sender(None, "simulated", ["0G-USDT-SWAP", "BTC-USDT-SWAP"])

    assert ("wss://demo-public.example/ws", ["0G-USDT-SWAP"]) in calls
    assert ("wss://demo-public.example/ws", ["BTC-USDT-SWAP"]) in calls
    partial = next(item for item in sent if item.get("source") == "partial-fallback")
    assert partial["type"] == "status"
    assert partial["topic"] == "market.ticker"
    assert partial["skippedInstIds"] == ["0G-USDT-SWAP"]
    assert not any(item["type"] == "error" and item.get("topic") == "market.ticker" for item in sent)


def test_settings_status_exposes_non_secret_realtime_metadata(monkeypatch):
    monkeypatch.setattr(main, "settings", NoCredentialSettings())
    monkeypatch.setattr(main, "current_trading_environment", lambda: "simulated")

    payload = main.settings_status()

    assert payload["realtime"]["endpoint"] == "/ws/realtime"
    assert payload["realtime"]["hasPrivateCredentials"] is False
    assert "market.ticker" in payload["realtime"]["publicTopics"]
    assert "orders" in payload["realtime"]["privateTopics"]
