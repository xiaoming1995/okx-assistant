from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


REALTIME_TOPICS = {
    "market",
    "market.ticker",
    "market.candles",
    "account",
    "positions",
    "orders",
    "automation",
    "automation.status",
    "automation.alert",
    "automation.signal",
}

PRIVATE_TOPICS = {"account", "positions", "orders"}
AUTOMATION_TOPICS = {"automation", "automation.status", "automation.alert", "automation.signal"}
MARKET_TOPICS = {"market", "market.ticker", "market.candles"}


@dataclass
class RealtimeSession:
    session_id: str
    websocket: WebSocket
    topics: set[str] = field(default_factory=set)
    environment: str = "simulated"


def now_ms() -> int:
    return int(time.time() * 1000)


def event_topic(event: dict[str, Any]) -> str:
    return str(event.get("topic") or event.get("type") or "")


def topic_matches(subscription: str, topic: str) -> bool:
    if subscription == topic:
        return True
    if subscription in {"market", "automation"} and topic.startswith(f"{subscription}."):
        return True
    return False


def normalize_subscription_message(payload: dict[str, Any]) -> tuple[set[str], list[str]]:
    raw_topics = payload.get("topics")
    if isinstance(raw_topics, str):
        candidates = [raw_topics]
    elif isinstance(raw_topics, list):
        candidates = raw_topics
    else:
        candidates = []

    topics: set[str] = set()
    errors: list[str] = []
    for candidate in candidates:
        topic = str(candidate or "").strip()
        if not topic:
            continue
        if topic not in REALTIME_TOPICS:
            errors.append(topic)
            continue
        topics.add(topic)
    return topics, errors


def normalize_inst_ids(payload: dict[str, Any]) -> list[str]:
    raw_inst_ids = payload.get("instIds")
    if isinstance(raw_inst_ids, str):
        candidates = [raw_inst_ids]
    elif isinstance(raw_inst_ids, list):
        candidates = raw_inst_ids
    else:
        candidates = []
    inst_id = str(payload.get("instId") or "").strip()
    if inst_id:
        candidates.append(inst_id)
    normalized = sorted({str(item or "").strip().upper() for item in candidates if str(item or "").strip()})
    return normalized[:80]


class RealtimeHub:
    def __init__(self) -> None:
        self._sessions: dict[str, RealtimeSession] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def attach_loop(self) -> None:
        self._loop = asyncio.get_running_loop()

    async def connect(self, websocket: WebSocket) -> RealtimeSession:
        session = RealtimeSession(session_id=uuid.uuid4().hex, websocket=websocket)
        async with self._lock:
            self._sessions[session.session_id] = session
        return session

    async def disconnect(self, session: RealtimeSession) -> None:
        async with self._lock:
            self._sessions.pop(session.session_id, None)

    async def update_subscription(self, session: RealtimeSession, topics: set[str], environment: str) -> None:
        session.topics = topics
        session.environment = environment
        async with self._lock:
            self._sessions[session.session_id] = session

    async def send(self, session: RealtimeSession, event: dict[str, Any]) -> bool:
        try:
            await session.websocket.send_json(event)
            return True
        except (WebSocketDisconnect, RuntimeError):
            await self.disconnect(session)
            return False

    async def broadcast(self, event: dict[str, Any], topic: str | None = None) -> None:
        resolved_topic = topic or event_topic(event)
        async with self._lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            if not any(topic_matches(subscription, resolved_topic) for subscription in session.topics):
                continue
            await self.send(session, event)

    def broadcast_threadsafe(self, event: dict[str, Any], topic: str | None = None) -> None:
        loop = self._loop
        if not loop or loop.is_closed():
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(event, topic=topic), loop)

    def active_session_count(self) -> int:
        return len(self._sessions)


async def cancel_tasks(tasks: list[asyncio.Task[Any]]) -> None:
    for task in tasks:
        task.cancel()
    for task in tasks:
        with contextlib.suppress(asyncio.CancelledError):
            await task
