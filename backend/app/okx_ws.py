from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import re
import time
from typing import Any, AsyncIterator

import websockets

from .config import Settings
from .okx import parse_okx_candles


BAR_TO_CHANNEL = {
    "1m": "candle1m",
    "5m": "candle5m",
    "15m": "candle15m",
    "1H": "candle1H",
    "4H": "candle4H",
    "1D": "candle1D",
}


class OkxWsError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        okx_message: str | None = None,
        channel: str | None = None,
        inst_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.okx_message = okx_message
        self.channel = channel
        self.inst_id = inst_id


def candle_channel(bar: str) -> str:
    try:
        return BAR_TO_CHANNEL[bar]
    except KeyError as exc:
        raise OkxWsError(f"Unsupported K-line interval for WebSocket: {bar}") from exc


def public_ticker_subscribe_args(inst_ids: list[str]) -> list[dict[str, str]]:
    normalized = sorted({inst_id.strip().upper() for inst_id in inst_ids if inst_id.strip()})
    return [{"channel": "tickers", "instId": inst_id} for inst_id in normalized]


def public_candle_subscribe_args(inst_id: str, bar: str) -> list[dict[str, str]]:
    normalized = inst_id.strip().upper()
    if not normalized:
        raise OkxWsError("No instrument provided for candle subscription")
    return [{"channel": candle_channel(bar), "instId": normalized}]


def okx_ws_error_from_payload(payload: dict[str, Any]) -> OkxWsError:
    code = str(payload.get("code") or "")
    message = str(payload.get("msg") or "")
    channel_match = re.search(r"channel:([^,\s]+)", message)
    inst_match = re.search(r"instId:([^,\s]+)", message)
    return OkxWsError(
        f"OKX WebSocket error {code}: {message}",
        code=code,
        okx_message=message,
        channel=channel_match.group(1) if channel_match else None,
        inst_id=inst_match.group(1).upper() if inst_match else None,
    )


def private_subscribe_args(topics: set[str] | list[str], inst_type: str = "ANY") -> list[dict[str, str]]:
    requested = set(topics)
    args: list[dict[str, str]] = []
    if "account" in requested:
        args.append({"channel": "account"})
    if "positions" in requested:
        args.append({"channel": "positions", "instType": inst_type})
    if "orders" in requested:
        args.append({"channel": "orders", "instType": inst_type})
    return args


def private_login_payload(settings: Settings, timestamp: str | None = None) -> dict[str, Any]:
    settings.require_credentials()
    ts = timestamp or str(time.time())
    message = f"{ts}GET/users/self/verify"
    signature = base64.b64encode(
        hmac.new(settings.api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    return {
        "op": "login",
        "args": [
            {
                "apiKey": settings.api_key,
                "passphrase": settings.passphrase,
                "timestamp": ts,
                "sign": signature,
            }
        ],
    }


async def stream_public_candles(ws_url: str, inst_id: str, bar: str) -> AsyncIterator[dict[str, Any]]:
    channel = candle_channel(bar)
    args = public_candle_subscribe_args(inst_id, bar)
    subscribe = {"op": "subscribe", "args": args}
    try:
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10, close_timeout=2) as ws:
            await ws.send(json.dumps(subscribe, separators=(",", ":")))
            subscribed = False
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    await ws.send("ping")
                    continue

                if raw == "pong":
                    continue

                payload = json.loads(raw)
                if payload.get("event") == "error":
                    raise okx_ws_error_from_payload(payload)
                if payload.get("event") == "subscribe":
                    arg = payload.get("arg", {})
                    if arg.get("channel") == channel and str(arg.get("instId") or "").upper() == inst_id.upper():
                        subscribed = True
                        yield {
                            "type": "status",
                            "topic": "market.candles",
                            "message": f"OKX WebSocket subscribed: {inst_id} {channel}",
                            "source": "okx-ws",
                            "ts": int(time.time() * 1000),
                        }
                    continue
                if payload.get("event") in {"unsubscribe", "channel-conn-count"}:
                    continue

                arg = payload.get("arg", {})
                data = payload.get("data", [])
                if not data:
                    continue

                if arg.get("channel") == channel:
                    if not subscribed:
                        subscribed = True
                        yield {
                            "type": "status",
                            "topic": "market.candles",
                            "message": f"OKX WebSocket subscribed: {inst_id} {channel}",
                            "source": "okx-ws",
                            "ts": int(time.time() * 1000),
                        }
                    yield {"type": "candle", "data": parse_okx_candles(data)}
    except OkxWsError:
        raise
    except Exception as exc:
        raise OkxWsError(f"OKX candle WebSocket connection failed: {exc}") from exc


async def stream_market_data(
    candle_ws_url: str,
    inst_id: str,
    bar: str,
    ticker_ws_url: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    tasks: list[asyncio.Task[None]] = []

    async def forward(events: AsyncIterator[dict[str, Any]]) -> None:
        async for event in events:
            await queue.put(event)

    tasks.append(asyncio.create_task(forward(stream_public_candles(candle_ws_url, inst_id, bar))))
    tasks.append(asyncio.create_task(forward(stream_public_tickers(ticker_ws_url or candle_ws_url, [inst_id]))))
    try:
        while True:
            queue_task = asyncio.create_task(queue.get())
            done, _ = await asyncio.wait([queue_task, *tasks], return_when=asyncio.FIRST_COMPLETED)
            if queue_task in done:
                yield queue_task.result()
                continue

            queue_task.cancel()
            await asyncio.gather(queue_task, return_exceptions=True)
            for task in done:
                if task.cancelled():
                    continue
                exc = task.exception()
                if exc:
                    raise exc
                raise OkxWsError("OKX WebSocket stream ended unexpectedly")
    except OkxWsError:
        raise
    except Exception as exc:
        raise OkxWsError(f"OKX WebSocket connection failed: {exc}") from exc
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def stream_public_tickers(ws_url: str, inst_ids: list[str]) -> AsyncIterator[dict[str, Any]]:
    args = public_ticker_subscribe_args(inst_ids)
    if not args:
        raise OkxWsError("No instruments provided for ticker subscription")
    subscribe = {"op": "subscribe", "args": args}
    try:
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10, close_timeout=2) as ws:
            await ws.send(json.dumps(subscribe, separators=(",", ":")))
            status_sent = False
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    await ws.send("ping")
                    continue

                if raw == "pong":
                    continue

                payload = json.loads(raw)
                if payload.get("event") == "error":
                    raise okx_ws_error_from_payload(payload)
                if payload.get("event") == "subscribe":
                    if not status_sent:
                        status_sent = True
                        yield {
                            "type": "status",
                            "topic": "market.ticker",
                            "message": f"OKX WebSocket subscribed: {len(args)} ticker channel(s)",
                            "source": "okx-ws",
                            "ts": int(time.time() * 1000),
                        }
                    continue
                if payload.get("event") in {"unsubscribe", "channel-conn-count"}:
                    continue

                arg = payload.get("arg", {})
                data = payload.get("data", [])
                if arg.get("channel") == "tickers" and data:
                    if not status_sent:
                        status_sent = True
                        yield {
                            "type": "status",
                            "topic": "market.ticker",
                            "message": f"OKX WebSocket subscribed: {len(args)} ticker channel(s)",
                            "source": "okx-ws",
                            "ts": int(time.time() * 1000),
                        }
                    yield {"type": "ticker", "instId": arg.get("instId"), "data": data[0]}
    except OkxWsError:
        raise
    except Exception as exc:
        raise OkxWsError(f"OKX ticker WebSocket connection failed: {exc}") from exc


async def stream_private_account_data(
    ws_url: str,
    env_settings: Settings,
    topics: set[str] | list[str],
    inst_type: str = "ANY",
) -> AsyncIterator[dict[str, Any]]:
    args = private_subscribe_args(topics, inst_type=inst_type)
    if not args:
        raise OkxWsError("No private topics provided for subscription")
    try:
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10, close_timeout=2) as ws:
            await ws.send(json.dumps(private_login_payload(env_settings), separators=(",", ":")))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                if raw == "pong":
                    continue
                payload = json.loads(raw)
                if payload.get("event") == "login" and str(payload.get("code") or "") == "0":
                    break
                if payload.get("event") == "error":
                    raise OkxWsError(f"OKX private WebSocket login failed {payload.get('code')}: {payload.get('msg')}")

            await ws.send(json.dumps({"op": "subscribe", "args": args}, separators=(",", ":")))
            yield {
                "type": "status",
                "topic": "private",
                "message": f"OKX private WebSocket subscribed: {', '.join(item['channel'] for item in args)}",
                "source": "okx-private-ws",
                "ts": int(time.time() * 1000),
            }

            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    await ws.send("ping")
                    continue

                if raw == "pong":
                    continue

                payload = json.loads(raw)
                if payload.get("event") == "error":
                    raise OkxWsError(f"OKX private WebSocket error {payload.get('code')}: {payload.get('msg')}")
                if payload.get("event") in {"subscribe", "unsubscribe", "channel-conn-count"}:
                    continue

                arg = payload.get("arg", {})
                channel = arg.get("channel")
                data = payload.get("data", [])
                if not channel or not data:
                    continue
                yield {
                    "type": str(channel),
                    "topic": str(channel),
                    "arg": arg,
                    "data": data,
                    "raw": payload,
                    "source": "okx-private-ws",
                    "ts": int(time.time() * 1000),
                }
    except OkxWsError:
        raise
    except Exception as exc:
        raise OkxWsError(f"OKX private WebSocket connection failed: {exc}") from exc
