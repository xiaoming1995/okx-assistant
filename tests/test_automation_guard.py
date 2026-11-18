"""自动化交易风控/幂等加固的回归测试。"""

import json
import threading

import pytest

from backend.app import main
from backend.app.automation import (
    EvaluationContext,
    ExecutionGuard,
    classify_signal_action,
    client_order_id_for_execution,
    decide,
    execution_key,
    global_block_from_state,
)
from backend.app.db import Database


def automation_strategy(**overrides):
    strategy = {
        "id": 7,
        "name": "BTC MA",
        "enabled": True,
        "inst_id": "BTC-USDT-SWAP",
        "bar": "5m",
        "template": "ma_cross",
        "execution_mode": "simulated_auto",
        "td_mode": "cross",
        "ord_type": "market",
        "sz": "2",
        "fast_window": 5,
        "slow_window": 20,
        "max_order_contracts": "2",
        "max_position_contracts": "5",
        "cooldown_seconds": 300,
        "take_profit_pct": "0",
        "stop_loss_pct": "0",
        "last_eval_ts": None,
        "created_at": 100,
        "updated_at": 100,
    }
    strategy.update(overrides)
    return strategy


STOP_LOSS_ACCOUNT = {
    "positions": [
        {
            "instId": "BTC-USDT-SWAP",
            "pos": "2",
            "posSide": "long",
            "avgPx": "100",
            "markPx": "98",
            "mgnMode": "cross",
        }
    ],
    "summary": {},
}


class FakeSettings:
    def has_credentials_for_environment(self, environment):
        return True


class FakeDatabase:
    def __init__(self, global_state=None, latest_signal=None, raise_on_get=False):
        self.global_state = global_state
        self.latest_signal = latest_signal
        self.raise_on_get = raise_on_get
        self.signals = []
        self.last_eval = None

    def get_app_setting(self, key):
        if self.raise_on_get and key == main.AUTOMATION_GLOBAL_STATE_KEY:
            raise RuntimeError("database unavailable")
        if key == main.AUTOMATION_GLOBAL_STATE_KEY and self.global_state is not None:
            return json.dumps(self.global_state)
        return None

    def set_app_setting(self, key, value, ts):
        return None

    def latest_actionable_automation_signal(self, strategy_id):
        return self.latest_signal

    def set_automation_strategy_last_eval(self, strategy_id, candle_ts, updated_at):
        self.last_eval = (strategy_id, candle_ts, updated_at)

    def insert_automation_signal(self, payload):
        row = {"id": len(self.signals) + 1, **payload}
        self.signals.append(row)
        return row


@pytest.fixture
def fresh_guard(monkeypatch):
    guard = ExecutionGuard(load=lambda: None, save=lambda value: None)
    monkeypatch.setattr(main, "automation_execution_guard", guard)
    return guard


def patch_runtime(monkeypatch, fake_db, account_payload):
    breaker = []
    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "database", fake_db)
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})
    monkeypatch.setattr(main, "refresh_account_cache_sync", lambda environment: account_payload)
    monkeypatch.setattr(
        main,
        "trigger_automation_circuit_breaker",
        lambda reason, **kwargs: breaker.append(reason) or {"circuitBreakerActive": True},
    )
    return breaker


def patch_long_signal(monkeypatch, candle_ts=12345):
    monkeypatch.setattr(
        main,
        "ma_cross_signal",
        lambda strategy: {
            "action": "long",
            "side": "buy",
            "pos_side": "long",
            "price": "64000",
            "candle_ts": candle_ts,
            "reason": "fast crossed above slow",
        },
    )


# ---------- 服务层纯逻辑 ----------


def test_execution_key_buckets_exits_by_minute_and_opens_by_candle():
    assert execution_key(2, "stop_loss", 1_700_000_000_000) == execution_key(
        2, "stop_loss", 1_700_000_000_001
    )
    assert execution_key(2, "stop_loss", 1_700_000_000_000) != execution_key(
        2, "stop_loss", 1_700_000_060_000
    )
    assert execution_key(2, "long", 1000) != execution_key(2, "long", 1001)
    assert execution_key(2, "long", 1000, "buy", "long") != execution_key(
        2, "short", 1000, "buy", "long"
    )


def test_client_order_id_is_deterministic_and_within_okx_limit():
    cl_ord_id = client_order_id_for_execution("7|long|12345|buy|long")
    assert len(cl_ord_id) == 32
    assert cl_ord_id.isalnum() and cl_ord_id.isupper()
    assert cl_ord_id == client_order_id_for_execution("7|long|12345|buy|long")


def test_guard_claim_commit_release_semantics():
    guard = ExecutionGuard(load=lambda: None, save=lambda value: None)
    assert guard.try_claim("key") == (True, "")
    assert guard.try_claim("key")[0] is False  # 执行中
    guard.release("key")
    assert guard.try_claim("key")[0] is True  # 失败后可重试
    guard.commit("key")
    assert guard.try_claim("key")[0] is False  # 成功后不可重复


def test_guard_persists_committed_keys_across_instances():
    stored = {}
    guard = ExecutionGuard(load=lambda: stored.get("guard"), save=lambda value: stored.update(guard=value))
    assert guard.try_claim("key")[0] is True
    guard.commit("key")
    restarted = ExecutionGuard(load=lambda: stored.get("guard"), save=lambda value: None)
    assert restarted.try_claim("key")[0] is False


def test_guard_fail_closed_when_execution_log_unavailable():
    def broken_load():
        raise RuntimeError("database unavailable")

    guard = ExecutionGuard(load=broken_load, save=lambda value: None)
    claimed, reason = guard.try_claim("key")
    assert claimed is False
    assert "拒绝执行" in reason


def test_guard_concurrent_claims_admit_only_one_thread():
    guard = ExecutionGuard(load=lambda: None, save=lambda value: None)
    barrier = threading.Barrier(4)
    outcomes = []

    def worker():
        barrier.wait()
        outcomes.append(guard.try_claim("same-key")[0])

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count(True) == 1


def test_guard_strategy_locks_are_isolated():
    guard = ExecutionGuard(load=lambda: None, save=lambda value: None)
    assert guard.strategy_lock(7) is guard.strategy_lock(7)
    assert guard.strategy_lock(7) is not guard.strategy_lock(8)


def test_global_state_fail_closed_and_pause_precedence():
    assert global_block_from_state({"stateAvailable": False})["key"] == "global_state"
    assert global_block_from_state({"globalPaused": True})["key"] == "global_pause"
    assert global_block_from_state({"circuitBreakerActive": True})["key"] == "circuit_breaker"
    assert global_block_from_state({"globalPaused": False}) is None
    assert global_block_from_state(None)["key"] == "global_state"


def test_decide_exit_ignores_open_only_but_honors_global_blocks():
    checks = [
        {"key": "llm", "status": "block", "message": "置信度不足"},
        {"key": "cooldown", "status": "block", "message": "冷却中"},
        {"key": "max_position", "status": "block", "message": "超仓位"},
    ]
    assert decide(checks=checks, execution_mode="simulated_auto", action_kind="exit")[0] is True
    assert decide(checks=checks, execution_mode="simulated_auto", action_kind="open")[0] is False
    checks.append({"key": "global_pause", "status": "block", "message": "已暂停"})
    assert decide(checks=checks, execution_mode="simulated_auto", action_kind="exit")[0] is False


def test_evaluation_context_loads_each_dependency_once():
    calls = []
    ctx = EvaluationContext()

    def account_loader(environment):
        calls.append(("account", environment))
        return {"positions": []}

    for _ in range(3):
        assert ctx.account(account_loader)[1] is None
        assert ctx.global_state(lambda: {"globalPaused": False}) == {"globalPaused": False}
        assert ctx.llm_config(lambda: {"enabled": False}) == {"enabled": False}
    assert calls == [("account", "simulated")]


def test_action_classification():
    assert classify_signal_action("long") == "open"
    assert classify_signal_action("stop_loss") == "exit"
    assert classify_signal_action("take_profit") == "exit"
    assert classify_signal_action("hold") == "observe"


# ---------- 编排层集成 ----------


def test_global_state_read_failure_pauses_automation(monkeypatch):
    monkeypatch.setattr(main, "database", FakeDatabase(raise_on_get=True))
    state = main.automation_global_state()
    assert state["stateAvailable"] is False
    assert state["globalPaused"] is True
    assert main.automation_global_block_check({}, {})["key"] == "global_state"


def test_place_order_payload_accepts_deterministic_client_order_id():
    order = main.PlaceSimOrderRequest(
        instId="BTC-USDT-SWAP",
        tdMode="cross",
        side="buy",
        posSide="long",
        ordType="market",
        sz="1",
        px=None,
        reduceOnly=False,
    )
    assert main.build_place_order_payload(order, cl_ord_id="OKXQAFIXED")["clOrdId"] == "OKXQAFIXED"
    assert main.build_place_order_payload(order)["clOrdId"] != main.build_place_order_payload(order)["clOrdId"]


def test_stop_loss_is_blocked_by_global_pause(monkeypatch, fresh_guard):
    fake_db = FakeDatabase(global_state={"globalPaused": True, "pauseReason": "人工暂停"})
    patch_runtime(monkeypatch, fake_db, STOP_LOSS_ACCOUNT)
    close_calls = []
    monkeypatch.setattr(
        main,
        "close_position_for_environment",
        lambda environment, order, origin="manual": close_calls.append(order) or {"ok": True},
    )

    result = main.evaluate_automation_strategy(
        automation_strategy(take_profit_pct="3", stop_loss_pct="1"), force=True
    )

    assert result["decision"] == "blocked"
    assert "人工暂停" in result["message"]
    assert close_calls == []


def test_stop_loss_is_not_blocked_by_open_cooldown(monkeypatch, fresh_guard):
    fake_db = FakeDatabase(global_state={}, latest_signal={"ts": main.now_ms()})
    patch_runtime(monkeypatch, fake_db, STOP_LOSS_ACCOUNT)
    close_calls = []
    monkeypatch.setattr(
        main,
        "close_position_for_environment",
        lambda environment, order, origin="manual": close_calls.append(order) or {"ok": True},
    )

    result = main.evaluate_automation_strategy(
        automation_strategy(take_profit_pct="3", stop_loss_pct="1"), force=True
    )
    raw = json.loads(result["raw_json"])

    assert result["decision"] == "submitted"
    assert len(close_calls) == 1
    assert raw["execution_payload"]["risk_snapshot"]["allowed"] is True


def test_stop_loss_without_position_is_not_submitted(monkeypatch, fresh_guard):
    fake_db = FakeDatabase(global_state={})
    patch_runtime(monkeypatch, fake_db, {"positions": [], "summary": {}})

    preview = main.automation_risk_preview(
        automation_strategy(take_profit_pct="3", stop_loss_pct="1"),
        {"action": "stop_loss", "side": None, "pos_side": "long", "candle_ts": 1},
    )

    assert preview["allowed"] is False
    assert any(item["key"] == "exit_position" and item["status"] == "block" for item in preview["checks"])


def test_force_run_on_same_candle_does_not_duplicate_order(monkeypatch, fresh_guard):
    fake_db = FakeDatabase(global_state={})
    patch_runtime(monkeypatch, fake_db, {"positions": [], "summary": {}})
    patch_long_signal(monkeypatch, candle_ts=12345)
    place_calls = []

    def fake_place(environment, order, cl_ord_id=None, origin="manual"):
        place_calls.append((environment, order.side, cl_ord_id))
        return {"ok": True}

    monkeypatch.setattr(main, "place_order_for_environment", fake_place)
    strategy = automation_strategy()

    first = main.evaluate_automation_strategy(strategy, force=True)
    second = main.evaluate_automation_strategy(strategy, force=True)

    assert first["decision"] == "submitted"
    assert second["decision"] == "skipped"
    assert len(place_calls) == 1
    assert place_calls[0][2] == client_order_id_for_execution(
        execution_key(7, "long", 12345, "buy", "long")
    )


def test_reverse_failure_preserves_close_steps_and_triggers_breaker(monkeypatch, fresh_guard):
    fake_db = FakeDatabase(global_state={})
    reverse_account = {
        "positions": [
            {"instId": "BTC-USDT-SWAP", "pos": "-2", "posSide": "net", "mgnMode": "cross"}
        ],
        "summary": {},
    }
    breaker = patch_runtime(monkeypatch, fake_db, reverse_account)
    patch_long_signal(monkeypatch, candle_ts=22222)
    monkeypatch.setattr(
        main, "close_position_for_environment", lambda environment, order, origin="manual": {"ok": True}
    )

    def fail_place(environment, order, cl_ord_id=None):
        raise RuntimeError("OKX 拒绝开仓")

    monkeypatch.setattr(main, "place_order_for_environment", fail_place)
    monkeypatch.setattr(main, "create_automation_alert", lambda *args, **kwargs: None)

    result = main.evaluate_automation_strategy(automation_strategy(), force=True)
    raw = json.loads(result["raw_json"])
    steps = raw["execution_payload"]["execution_steps"]

    assert result["decision"] == "failed"
    assert [item["action"] for item in steps] == ["close-position", "compensation-required"]
    assert raw["execution_payload"]["compensation_required"] is True
    assert raw["execution_steps"] == steps  # 审计载荷顶层可读，前端详情不再丢失
    assert breaker and "反向平仓" in breaker[0]


def test_latest_actionable_signal_excludes_exit_actions(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'automation.sqlite3'}")
    db.init()
    strategy = db.create_automation_strategy(
        {
            "name": "BTC MA",
            "enabled": True,
            "inst_id": "BTC-USDT-SWAP",
            "bar": "5m",
            "template": "ma_cross",
            "execution_mode": "simulated_auto",
            "td_mode": "cross",
            "ord_type": "market",
            "sz": "1",
            "fast_window": 5,
            "slow_window": 20,
            "max_order_contracts": "1",
            "max_position_contracts": "5",
            "cooldown_seconds": 300,
            "take_profit_pct": "0",
            "stop_loss_pct": "0",
            "last_eval_ts": None,
            "created_at": 100,
            "updated_at": 100,
        }
    )
    base = {
        "strategy_id": strategy["id"],
        "environment": "simulated",
        "inst_id": "BTC-USDT-SWAP",
        "bar": "5m",
        "template": "ma_cross",
        "side": "buy",
        "pos_side": "long",
        "price": "64000",
        "sz": "1",
        "reason": "test",
        "message": "test",
        "raw_json": "{}",
    }
    db.insert_automation_signal({**base, "action": "long", "ts": 100, "decision": "submitted"})
    db.insert_automation_signal({**base, "action": "stop_loss", "ts": 900, "decision": "submitted"})

    assert db.latest_actionable_automation_signal(strategy["id"])["action"] == "long"
