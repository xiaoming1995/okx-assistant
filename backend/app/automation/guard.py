"""自动化交易执行闸门：并发互斥 + 业务幂等键 + 确定性 clOrdId。

解决的问题：
- 后台轮询 / 手动 run / 单策略 run 可能对同一根 K 线并发评估并重复下单；
- force=True 会绕过 last_eval_ts 去重，导致同一信号反复提交；
- clOrdId 原先每次随机生成，OKX 侧无法据此拒绝重复订单。

幂等键只在真正下单前占位，执行成功后才提交；失败会释放占位以便重试，
但执行记录不可用时一律拒绝执行（fail-closed）。
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Callable

from .risk import EXIT_ACTIONS

MAX_COMMITTED_KEYS = 256
EXIT_BUCKET_MS = 60_000
CL_ORD_ID_PREFIX = "OKXQA"


def execution_key(
    strategy_id: Any,
    action: Any,
    candle_ts: Any,
    side: Any = "",
    pos_side: Any = "",
    inst_id: Any = "",
) -> str:
    """生成业务幂等键。

    开仓按 K 线时间戳精确去重；止盈止损的 candle_ts 是触发时刻，按分钟
    归桶，既拦住短时间内的重复平仓，也允许下一分钟在持仓仍在时重试。
    多合约策略必须把 inst_id 纳入键，否则同一根 K 线上不同合约会互相
    误判为重复信号。inst_id 为空时保持历史键格式，兼容既有记录与测试。
    """
    normalized_action = str(action or "unknown").strip().lower()
    try:
        timestamp = int(candle_ts or 0)
    except (TypeError, ValueError):
        timestamp = 0
    bucket = timestamp // EXIT_BUCKET_MS if normalized_action in EXIT_ACTIONS else timestamp
    parts = [
        str(int(strategy_id or 0)),
        normalized_action,
        str(bucket),
        str(side or ""),
        str(pos_side or ""),
    ]
    normalized_inst_id = str(inst_id or "").strip().upper()
    if normalized_inst_id:
        parts.append(normalized_inst_id)
    return "|".join(parts)


def client_order_id_for_execution(key: str) -> str:
    """由幂等键派生确定性 clOrdId（32 字符，符合 OKX 限制）。"""
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:27].upper()
    return f"{CL_ORD_ID_PREFIX}{digest}"


class AutomationExecutionError(Exception):
    """执行链路失败，steps 保留已经发生的动作，供审计与人工补偿。"""

    def __init__(
        self,
        message: str,
        *,
        steps: list[dict[str, Any]] | None = None,
        compensation_required: bool = False,
    ) -> None:
        super().__init__(message)
        self.steps = list(steps or [])
        self.compensation_required = bool(compensation_required)


class ExecutionGuard:
    def __init__(
        self,
        load: Callable[[], str | None],
        save: Callable[[str], None],
        logger: logging.Logger | None = None,
        max_keys: int = MAX_COMMITTED_KEYS,
    ) -> None:
        self._load = load
        self._save = save
        self._logger = logger or logging.getLogger(__name__)
        self._max_keys = max(16, int(max_keys))
        self._lock = threading.RLock()
        self._strategy_locks: dict[int, threading.RLock] = {}
        self._inflight: set[str] = set()
        self._committed: OrderedDict[str, int] = OrderedDict()

    def strategy_lock(self, strategy_id: Any) -> threading.RLock:
        """返回按策略隔离的可重入锁，覆盖「评估 → 风控 → 下单 → 记录」全程。"""
        key = int(strategy_id or 0)
        with self._lock:
            lock = self._strategy_locks.get(key)
            if lock is None:
                lock = threading.RLock()
                self._strategy_locks[key] = lock
            return lock

    def _read_persisted(self) -> bool:
        try:
            raw = self._load()
        except Exception as exc:
            self._logger.error("自动化幂等记录读取失败，拒绝本次执行: %s", exc)
            return False
        if not raw:
            return True
        try:
            rows = json.loads(raw)
        except (TypeError, ValueError):
            self._logger.error("自动化幂等记录损坏，拒绝本次执行")
            return False
        if not isinstance(rows, list):
            self._logger.error("自动化幂等记录格式异常，拒绝本次执行")
            return False
        for item in rows:
            if isinstance(item, str):
                self._committed[item] = 0
            elif isinstance(item, (list, tuple)) and item:
                try:
                    committed_at = int(item[1]) if len(item) > 1 else 0
                except (TypeError, ValueError):
                    committed_at = 0
                self._committed[str(item[0])] = committed_at
        return True

    def try_claim(self, key: str) -> tuple[bool, str]:
        with self._lock:
            if key in self._inflight:
                return False, "同一信号正在执行中，已拦截重复请求。"
            if not self._read_persisted():
                return False, "幂等记录不可用，为防止重复下单已拒绝执行。"
            if key in self._committed:
                return False, "该信号已执行过，已拦截重复下单。"
            self._inflight.add(key)
            return True, ""

    def commit(self, key: str) -> None:
        with self._lock:
            self._inflight.discard(key)
            self._committed[key] = int(time.time() * 1000)
            while len(self._committed) > self._max_keys:
                self._committed.popitem(last=False)
            try:
                rows = [[item, int(ts)] for item, ts in self._committed.items()]
                self._save(json.dumps(rows, separators=(",", ":")))
            except Exception as exc:
                self._logger.error("自动化幂等记录写入失败: %s", exc)

    def release(self, key: str) -> None:
        """执行失败时只释放占位，允许在状态恢复后重试。"""
        with self._lock:
            self._inflight.discard(key)

    def reset(self) -> None:
        """仅用于测试：清空进程内状态。"""
        with self._lock:
            self._inflight.clear()
            self._committed.clear()
            self._strategy_locks.clear()
