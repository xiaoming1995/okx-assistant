"""多合约策略与每日仓位额度的回归测试。"""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from backend.app import main
from backend.app.automation import ExecutionGuard, execution_key
from backend.app.db import Database

UTC8 = timezone(timedelta(hours=8))

INSTRUMENTS = [
    {"inst_id": "BTC-USDT-SWAP", "ct_val": "0.01"},
    {"inst_id": "ETH-USDT-SWAP", "ct_val": "0.1"},
    {"inst_id": "SOL-USDT-SWAP", "ct_val": "1"},
]

ACCOUNT = {"summary": {"totalEq": "10000", "availEq": "8000"}, "positions": []}

ACCOUNT_WITH_POSITION = {
    "summary": {"totalEq": "10000"},
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
}

LONG_SIGNAL = {
    "action": "long",
    "side": "buy",
    "pos_side": "long",
    "price": "64000",
    "candle_ts": 12345,
    "reason": "fast crossed above slow",
}


def make_strategy(**overrides):
    strategy = {
        "id": 7,
        "name": "多合约策略",
        "enabled": True,
        "archived": False,
        "inst_id": "BTC-USDT-SWAP",
        "inst_ids": json.dumps(["BTC-USDT-SWAP", "ETH-USDT-SWAP"]),
        "daily_position_pct": "0",
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
        "cooldown_seconds": 0,
        "take_profit_pct": "0",
        "stop_loss_pct": "0",
        "last_eval_ts": None,
        "created_at": 1,
        "updated_at": 1,
    }
    strategy.update(overrides)
    return strategy


class FakeSettings:
    def has_credentials_for_environment(self, environment):
        return True


class FakeDatabase:
    def __init__(self, instruments=None, signals=None, global_state=None):
        self.instruments = instruments if instruments is not None else INSTRUMENTS
        self.signals = list(signals or [])
        self.global_state = global_state or {}
        self.settings = {}
        self.last_eval = []

    def get_app_setting(self, key):
        if key == main.AUTOMATION_GLOBAL_STATE_KEY:
            return json.dumps(self.global_state)
        return self.settings.get(key)

    def set_app_setting(self, key, value, ts):
        self.settings[key] = value

    def list_instruments(self, query="", limit=20):
        return [item for item in self.instruments if item["inst_id"] == str(query).upper()][:limit]

    def list_automation_signals_since(self, strategy_id, since_ts):
        return [
            row
            for row in self.signals
            if int(row.get("strategy_id") or 0) == strategy_id
            and int(row.get("ts") or 0) >= since_ts
        ]

    def list_automation_signals(self, strategy_id=0, limit=100):
        return [row for row in self.signals if not strategy_id or row.get("strategy_id") == strategy_id][:limit]

    def latest_actionable_automation_signal(self, strategy_id):
        return None

    def set_automation_strategy_last_eval(self, strategy_id, candle_ts, updated_at):
        self.last_eval.append((strategy_id, candle_ts))

    def insert_automation_signal(self, payload):
        row = {"id": len(self.signals) + 1, **payload}
        self.signals.append(row)
        return row


@pytest.fixture
def runtime(monkeypatch):
    state = {"places": [], "alerts": [], "breakers": []}

    def patch_db(db):
        monkeypatch.setattr(main, "database", db)

    guard = ExecutionGuard(load=lambda: None, save=lambda value: None)
    monkeypatch.setattr(main, "automation_execution_guard", guard)
    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})
    monkeypatch.setattr(main, "broadcast_realtime_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "create_automation_alert", lambda *args, **kwargs: state["alerts"].append(args))
    monkeypatch.setattr(
        main,
        "trigger_automation_circuit_breaker",
        lambda reason, **kwargs: state["breakers"].append(reason) or {},
    )
    monkeypatch.setattr(main, "ma_cross_signal", lambda strategy: dict(LONG_SIGNAL))
    monkeypatch.setattr(main, "close_position_for_environment", lambda environment, order, origin="manual": {"ok": True})

    def fake_place(environment, order, cl_ord_id=None, origin="manual"):
        state["places"].append((environment, order.instId, cl_ord_id))
        return {"ok": True}

    monkeypatch.setattr(main, "place_order_for_environment", fake_place)
    state["patch_db"] = patch_db
    state["account"] = ACCOUNT
    monkeypatch.setattr(main, "refresh_account_cache_sync", lambda environment: state["account"])
    return state


# ---------- 多合约 ----------


def test_execution_key_separates_instruments_without_changing_legacy_format():
    assert execution_key(7, "long", 12345, "buy", "long") == "7|long|12345|buy|long"
    assert execution_key(7, "long", 12345, "buy", "long", "BTC-USDT-SWAP") != execution_key(
        7, "long", 12345, "buy", "long", "ETH-USDT-SWAP"
    )


def test_multi_instrument_places_one_order_per_contract(runtime):
    runtime["patch_db"](FakeDatabase())
    results = main.evaluate_automation_strategy_all(make_strategy(), force=True)

    assert len(results) == 2
    assert [row["inst_id"] for row in results] == ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    assert [row["decision"] for row in results] == ["submitted", "submitted"]
    assert [item[1] for item in runtime["places"]] == ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    assert runtime["places"][0][2] != runtime["places"][1][2]


def test_legacy_strategy_without_inst_ids_still_evaluates(runtime):
    runtime["patch_db"](FakeDatabase())
    strategy = make_strategy()
    strategy.pop("inst_ids")

    results = main.evaluate_automation_strategy_all(strategy, force=True)

    assert len(results) == 1
    assert results[0]["inst_id"] == "BTC-USDT-SWAP"


def test_kline_dedup_is_tracked_per_contract(runtime):
    fake_db = FakeDatabase()
    runtime["patch_db"](fake_db)
    strategy = make_strategy()

    first = main.evaluate_automation_strategy_all(strategy, force=False)
    assert len(first) == 2

    second = main.evaluate_automation_strategy_all(strategy, force=False)
    assert second == []

    extended = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"])
    )
    third = main.evaluate_automation_strategy_all(extended, force=False)
    assert [row["inst_id"] for row in third] == ["SOL-USDT-SWAP"]


def test_normalize_strategy_validates_instruments_and_daily_pct():
    normalized = main.normalize_automation_strategy(
        main.AutomationStrategyRequest(
            instIds=["btc-usdt-swap", "BTC-USDT-SWAP", "eth-usdt-swap"],
            dailyPositionPct="20",
        )
    )
    assert json.loads(normalized["inst_ids"]) == ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    assert normalized["inst_id"] == "BTC-USDT-SWAP"
    assert normalized["daily_position_pct"] == "20"

    with pytest.raises(HTTPException):
        main.normalize_automation_strategy(
            main.AutomationStrategyRequest(instIds=["BTC-USDT"], instId="")
        )
    with pytest.raises(HTTPException):
        main.normalize_automation_strategy(
            main.AutomationStrategyRequest(instIds=[], dailyPositionPct="101")
        )


def test_normalize_strategy_caps_instrument_count():
    ids = [f"COIN{i}-USDT-SWAP" for i in range(20)]
    normalized = main.normalize_automation_strategy(
        main.AutomationStrategyRequest(instIds=ids, instId="")
    )
    assert len(json.loads(normalized["inst_ids"])) == main.AUTOMATION_MAX_INST_IDS


# ---------- 每日仓位额度 ----------


def test_daily_start_uses_utc_plus_8_calendar_day():
    morning = int(datetime(2026, 11, 15, 0, 30, tzinfo=UTC8).timestamp() * 1000)
    midnight = int(datetime(2026, 11, 15, 0, 0, tzinfo=UTC8).timestamp() * 1000)
    previous_evening = int(datetime(2026, 11, 14, 23, 30, tzinfo=UTC8).timestamp() * 1000)

    assert main.daily_start_ms(morning) == midnight
    assert main.daily_start_ms(previous_evening) == midnight - 24 * 3600 * 1000


def test_daily_cap_passes_and_records_notional(runtime):
    runtime["patch_db"](FakeDatabase())
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="50"
    )

    result = main.evaluate_automation_strategy(strategy, force=True)
    raw = json.loads(result["raw_json"])

    assert result["decision"] == "submitted"
    # 2 张 × 0.01 BTC/张 × 64000 = 1280 USDT
    assert Decimal(raw["notional"]) == Decimal("1280")


def test_daily_cap_blocks_when_cumulative_notional_exceeds_limit(runtime):
    used_signal = {
        "id": 90,
        "strategy_id": 7,
        "ts": main.daily_start_ms() + 1000,
        "decision": "submitted",
        "action": "long",
        "raw_json": json.dumps({"notional": "900"}),
    }
    runtime["patch_db"](FakeDatabase(signals=[used_signal]))
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="2"
    )

    result = main.evaluate_automation_strategy(strategy, force=True)
    checks = json.loads(result["raw_json"])["execution_payload"]["risk_snapshot"]["checks"]

    assert result["decision"] == "blocked"
    assert any(item["key"] == "daily_limit" and item["status"] == "block" for item in checks)
    assert runtime["places"] == []


def test_daily_cap_ignores_signals_from_previous_day(runtime):
    old_signal = {
        "id": 91,
        "strategy_id": 7,
        "ts": main.daily_start_ms() - 24 * 3600 * 1000,
        "decision": "submitted",
        "action": "long",
        "raw_json": json.dumps({"notional": "999999"}),
    }
    runtime["patch_db"](FakeDatabase(signals=[old_signal]))
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="20"
    )

    result = main.evaluate_automation_strategy(strategy, force=True)

    assert result["decision"] == "submitted"


def test_daily_cap_is_shared_across_contracts(runtime):
    runtime["patch_db"](FakeDatabase())
    # 10000 × 20% = 2000；第一笔 BTC 占 1280，第二笔 ETH 预计 12800 会超额。
    strategy = make_strategy(daily_position_pct="20")

    results = main.evaluate_automation_strategy_all(strategy, force=True)

    assert [row["decision"] for row in results] == ["submitted", "blocked"]
    assert len(runtime["places"]) == 1


def test_daily_cap_blocks_when_equity_unavailable(runtime):
    runtime["patch_db"](FakeDatabase())
    runtime["account"] = {"summary": {}, "positions": []}
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="10"
    )

    preview = main.automation_risk_preview(strategy, LONG_SIGNAL)

    assert preview["allowed"] is False
    assert any(item["key"] == "daily_limit" and item["status"] == "block" for item in preview["checks"])


def test_daily_cap_blocks_when_contract_value_unknown(runtime):
    runtime["patch_db"](FakeDatabase(instruments=[]))
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="50"
    )

    preview = main.automation_risk_preview(strategy, LONG_SIGNAL)

    assert any(item["key"] == "daily_limit" and item["status"] == "block" for item in preview["checks"])


def test_exit_signal_is_exempt_from_daily_cap(runtime):
    runtime["patch_db"](FakeDatabase())
    runtime["account"] = ACCOUNT_WITH_POSITION
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="1", stop_loss_pct="1"
    )
    exit_signal = {
        "action": "stop_loss",
        "side": None,
        "pos_side": "long",
        "price": "98",
        "candle_ts": main.now_ms(),
        "position": ACCOUNT_WITH_POSITION["positions"][0],
    }

    preview = main.automation_risk_preview(strategy, exit_signal)
    daily = next(item for item in preview["checks"] if item["key"] == "daily_limit")

    assert preview["allowed"] is True
    assert daily["status"] == "pass"


def test_daily_cap_shows_usage_even_without_an_open_signal(runtime):
    used_signal = {
        "id": 92,
        "strategy_id": 7,
        "ts": main.daily_start_ms() + 1000,
        "decision": "submitted",
        "action": "long",
        "raw_json": json.dumps({"notional": "300"}),
    }
    runtime["patch_db"](FakeDatabase(signals=[used_signal]))
    strategy = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="20"
    )

    preview = main.automation_risk_preview(strategy, {"action": "hold", "candle_ts": 12345})
    daily = next(item for item in preview["checks"] if item["key"] == "daily_limit")

    assert daily["status"] == "pass"
    assert preview["dailyLimit"] == "2000.00"
    assert preview["dailyUsed"] == "300.00"
    assert "300.00 / 2000.00" in daily["value"]


def test_zero_daily_pct_disables_the_cap(runtime):
    runtime["patch_db"](FakeDatabase())
    strategy = make_strategy(inst_ids=json.dumps(["BTC-USDT-SWAP"]), daily_position_pct="0")

    preview = main.automation_risk_preview(strategy, LONG_SIGNAL)
    daily = next(item for item in preview["checks"] if item["key"] == "daily_limit")

    assert preview["allowed"] is True
    assert daily["status"] == "pass"
    assert "未启用" in daily["message"]


# ---------- 数据层 ----------


def test_strategy_new_columns_roundtrip_and_legacy_defaults(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'automation.sqlite3'}")
    db.init()

    payload = make_strategy(
        inst_ids=json.dumps(["BTC-USDT-SWAP", "ETH-USDT-SWAP"]),
        daily_position_pct="20",
    )
    row = db.create_automation_strategy(payload)
    assert json.loads(row["inst_ids"]) == ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    assert row["daily_position_pct"] == "20"
    assert main.strategy_inst_ids(row) == ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]

    legacy = make_strategy()
    legacy.pop("inst_ids")
    legacy.pop("daily_position_pct")
    legacy_row = db.create_automation_strategy(legacy)
    assert legacy_row["inst_ids"] == "[]"
    assert legacy_row["daily_position_pct"] == "0"
    assert main.strategy_inst_ids(legacy_row) == ["BTC-USDT-SWAP"]


def test_list_signals_since_filters_by_strategy_and_timestamp(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'automation.sqlite3'}")
    db.init()
    db.create_automation_strategy(make_strategy())
    for signal_id, ts in enumerate((1000, 5000, 9000), start=1):
        db.insert_automation_signal(
            {
                "strategy_id": 7,
                "ts": ts,
                "environment": "simulated",
                "inst_id": "BTC-USDT-SWAP",
                "bar": "5m",
                "template": "ma_cross",
                "action": "long",
                "side": "buy",
                "pos_side": "long",
                "price": "64000",
                "sz": "2",
                "decision": "submitted",
                "reason": "",
                "message": "",
                "raw_json": json.dumps({"notional": "100"}),
            }
        )

    rows = db.list_automation_signals_since(7, 5000)
    assert [int(row["ts"]) for row in rows] == [9000, 5000]
    assert db.list_automation_signals_since(8, 0) == []
