"""订单来源（手动 / 自动化）区分的端到端单测。"""

import json
import sqlite3

from backend.app import main
from backend.app.db import Database


def _event(inst_id: str = "BTC-USDT-SWAP", cl_ord_id: str = "C-1", **overrides):
    row = {
        "environment": "simulated",
        "ts": 100,
        "action": "place",
        "inst_id": inst_id,
        "td_mode": "cross",
        "side": "buy",
        "pos_side": "long",
        "ord_type": "market",
        "px": "",
        "sz": "1",
        "reduce_only": False,
        "cl_ord_id": cl_ord_id,
        "ord_id": "ORD-1",
        "state": "accepted",
        "code": "0",
        "message": "",
        "request_json": "{}",
        "response_json": "{}",
    }
    row.update(overrides)
    return row


class FakeSettings:
    live_trading_enabled = False

    def has_credentials_for_environment(self, environment):
        return False


# ---------- 数据库层 ----------


def test_new_order_event_defaults_to_manual_origin(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'origin.sqlite3'}")
    db.init()
    db.insert_sim_order_event(_event())

    events = db.list_sim_order_events("simulated")
    assert events[0]["origin"] == "manual"


def test_origin_filter_and_counts_split_manual_and_automation(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'origin.sqlite3'}")
    db.init()
    db.insert_sim_order_event(_event(cl_ord_id="M-1"))
    db.insert_sim_order_event(_event(cl_ord_id="M-2", ts=200))
    db.insert_sim_order_event(_event(cl_ord_id="A-1", ts=300, origin="automation"))

    manual = db.list_sim_order_events("simulated", origin="manual")
    automation = db.list_sim_order_events("simulated", origin="automation")
    assert [row["cl_ord_id"] for row in manual] == ["M-2", "M-1"]
    assert [row["cl_ord_id"] for row in automation] == ["A-1"]
    assert db.count_sim_order_events("simulated", origin="automation") == 1
    assert db.count_sim_order_events("simulated") == 3

    counts = db.sim_order_event_origin_counts("simulated")
    assert counts == {"manual": 2, "automation": 1}


def test_origin_counts_respects_other_filters(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'origin.sqlite3'}")
    db.init()
    db.insert_sim_order_event(_event(cl_ord_id="M-1", inst_id="BTC-USDT-SWAP"))
    db.insert_sim_order_event(_event(cl_ord_id="A-1", inst_id="ETH-USDT-SWAP", origin="automation"))

    assert db.sim_order_event_origin_counts("simulated", inst_id="ETH-USDT-SWAP") == {"automation": 1}


def test_mark_origin_backfills_only_matching_rows_and_is_idempotent(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'origin.sqlite3'}")
    db.init()
    db.insert_sim_order_event(_event(cl_ord_id="A-1"))
    db.insert_sim_order_event(_event(cl_ord_id="M-1", ts=200))
    db.insert_sim_order_event(_event(cl_ord_id="", ts=300))

    assert db.mark_sim_order_event_origin(["A-1", "MISSING", ""], "automation") == 1
    assert db.mark_sim_order_event_origin(["A-1"], "automation") == 0
    assert db.sim_order_event_origin_counts("simulated") == {"manual": 2, "automation": 1}


def test_origin_for_cl_ord_id_reads_latest_row(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'origin.sqlite3'}")
    db.init()
    db.insert_sim_order_event(_event(cl_ord_id="A-1", origin="automation"))

    assert db.sim_order_event_origin_for("simulated", "A-1") == "automation"
    assert db.sim_order_event_origin_for("simulated", "NOPE") == ""
    assert db.sim_order_event_origin_for("simulated", "") == ""


def test_legacy_database_gains_origin_column_with_manual_default(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE sim_order_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment TEXT NOT NULL DEFAULT 'simulated',
            ts INTEGER NOT NULL,
            action TEXT NOT NULL,
            inst_id TEXT NOT NULL,
            td_mode TEXT, side TEXT, pos_side TEXT, ord_type TEXT, px TEXT, sz TEXT,
            reduce_only INTEGER NOT NULL DEFAULT 0,
            cl_ord_id TEXT, ord_id TEXT, state TEXT, code TEXT, message TEXT,
            request_json TEXT NOT NULL, response_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO sim_order_events (
            environment, ts, action, inst_id, cl_ord_id, ord_id, state, code, message,
            request_json, response_json
        ) VALUES ('simulated', 1, 'place', 'BTC-USDT-SWAP', 'OLD-1', 'ORD', 'accepted', '0', '', '{}', '{}')
        """
    )
    conn.commit()
    conn.close()

    db = Database(f"sqlite:///{path}")
    db.init()
    rows = db.list_sim_order_events("simulated")
    assert rows[0]["origin"] == "manual"


# ---------- 事件写入 ----------


def test_sim_order_event_defaults_to_manual_and_accepts_automation(monkeypatch):
    stored = []
    monkeypatch.setattr(main.database, "insert_sim_order_event", lambda event: stored.append(event))
    monkeypatch.setattr(main, "broadcast_realtime_event", lambda *args, **kwargs: None)

    manual = main.sim_order_event(
        "simulated",
        "place",
        {"instId": "BTC-USDT-SWAP", "clOrdId": "M-1"},
        {"code": "0", "data": [{"clOrdId": "M-1", "ordId": "1", "sCode": "0"}]},
        "accepted",
    )
    auto = main.sim_order_event(
        "simulated",
        "place",
        {"instId": "BTC-USDT-SWAP", "clOrdId": "A-1"},
        {"code": "0", "data": [{"clOrdId": "A-1", "ordId": "2", "sCode": "0"}]},
        "accepted",
        origin=main.ORDER_ORIGIN_AUTOMATION,
    )

    assert manual["origin"] == "manual"
    assert auto["origin"] == "automation"
    assert [row["origin"] for row in stored] == ["manual", "automation"]


def test_sim_order_event_rejects_unknown_origin(monkeypatch):
    monkeypatch.setattr(main.database, "insert_sim_order_event", lambda event: None)
    monkeypatch.setattr(main, "broadcast_realtime_event", lambda *args, **kwargs: None)

    event = main.sim_order_event(
        "simulated",
        "place",
        {"instId": "BTC-USDT-SWAP"},
        {"code": "0", "data": []},
        "accepted",
        origin="robot",
    )
    assert event["origin"] == "manual"


def test_ws_order_update_inherits_origin_from_existing_event(monkeypatch):
    monkeypatch.setattr(main.database, "insert_sim_order_event", lambda event: None)
    monkeypatch.setattr(main, "invalidate_order_cache", lambda *args: None)
    monkeypatch.setattr(
        main.database, "sim_order_event_origin_for", lambda environment, cl_ord_id: "automation"
    )

    event = main.record_private_order_update(
        "simulated",
        {"instId": "BTC-USDT-SWAP", "clOrdId": "A-1", "ordId": "9", "state": "filled", "sz": "1"},
        {"arg": {"channel": "orders"}},
    )
    assert event["origin"] == "automation"


def test_ws_order_update_falls_back_to_manual_when_lookup_fails(monkeypatch):
    monkeypatch.setattr(main.database, "insert_sim_order_event", lambda event: None)
    monkeypatch.setattr(main, "invalidate_order_cache", lambda *args: None)

    def broken(environment, cl_ord_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(main.database, "sim_order_event_origin_for", broken)
    event = main.record_private_order_update(
        "simulated",
        {"instId": "BTC-USDT-SWAP", "clOrdId": "X-1", "ordId": "9", "state": "filled", "sz": "1"},
        {},
    )
    assert event["origin"] == "manual"


def test_order_event_origin_helper_normalizes_unknown_value(monkeypatch):
    monkeypatch.setattr(main.database, "sim_order_event_origin_for", lambda environment, cl_ord_id: "weird")
    assert main.order_event_origin("simulated", "A-1") == "manual"
    assert main.order_event_origin("simulated", "") == "manual"


# ---------- 历史回填 ----------


def test_backfill_marks_orders_referenced_by_automation_signals(monkeypatch):
    marked = {}

    class FakeDatabase:
        def list_automation_signals(self, limit=100):
            raw = {"execution_payload": {"steps": [{"result": {"event": {"cl_ord_id": "A-1"}}}]}}
            return [{"id": 1, "strategy_id": 2, "action": "long", "raw_json": json.dumps(raw)}]

        def mark_sim_order_event_origin(self, cl_ord_ids, origin):
            marked["ids"] = list(cl_ord_ids)
            marked["origin"] = origin
            return 1

    monkeypatch.setattr(main, "database", FakeDatabase())
    assert main.backfill_automation_order_origins() == 1
    assert marked["ids"] == ["A-1"]
    assert marked["origin"] == "automation"


def test_backfill_is_safe_when_database_misses_capability(monkeypatch):
    class FakeDatabase:
        pass

    monkeypatch.setattr(main, "database", FakeDatabase())
    assert main.backfill_automation_order_origins() == 0


# ---------- 列表接口 ----------


def test_orders_for_environment_filters_by_origin_and_reports_counts(monkeypatch):
    calls = []

    class FakeDatabase:
        def list_sim_order_events(self, **kwargs):
            calls.append(("list", kwargs))
            return [
                {"id": 1, "ts": 100, "action": "place", "state": "accepted", "cl_ord_id": "A-1", "inst_id": "BTC-USDT-SWAP", "origin": "manual"},
            ]

        def count_sim_order_events(self, **kwargs):
            calls.append(("count", kwargs))
            return 1

        def sim_order_event_origin_counts(self, **kwargs):
            calls.append(("counts", kwargs))
            return {"manual": 3, "automation": 1}

        def list_automation_signals(self, limit=100):
            raw = {"execution_payload": {"steps": [{"result": {"event": {"cl_ord_id": "A-1"}}}]}}
            return [{"id": 7, "strategy_id": 2, "action": "long", "raw_json": json.dumps(raw)}]

        def position_snapshot_rows_between(self, environment, from_ts, to_ts):
            return []

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "settings", FakeSettings())

    payload = main.orders_for_environment("simulated", origin="automation")

    assert payload["origin"] == "automation"
    assert payload["originCounts"] == {"manual": 3, "automation": 1, "all": 4}
    assert calls[0][1]["origin"] == "automation"
    assert calls[1][1]["origin"] == "automation"
    # 来源计数不带 origin 过滤，否则一切换就只剩当前分类的条数。
    assert "origin" not in calls[2][1]
    # 能对上自动化信号的订单强制归为自动化，避免历史空值误判。
    assert payload["events"][0]["origin"] == "automation"


def test_orders_for_environment_ignores_unknown_origin_filter(monkeypatch):
    calls = []

    class FakeDatabase:
        def list_sim_order_events(self, **kwargs):
            calls.append(kwargs)
            return []

        def count_sim_order_events(self, **kwargs):
            return 0

        def sim_order_event_origin_counts(self, **kwargs):
            return {}

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "settings", FakeSettings())

    payload = main.orders_for_environment("simulated", origin="robot")
    assert payload["origin"] == ""
    assert calls[0]["origin"] == ""


def test_orders_for_environment_survives_origin_counts_failure(monkeypatch):
    class FakeDatabase:
        def list_sim_order_events(self, **kwargs):
            return []

        def count_sim_order_events(self, **kwargs):
            return 0

        def sim_order_event_origin_counts(self, **kwargs):
            raise RuntimeError("counts unavailable")

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "settings", FakeSettings())

    payload = main.orders_for_environment("simulated")
    assert payload["originCounts"]["all"] == 0
