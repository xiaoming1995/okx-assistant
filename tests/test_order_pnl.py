import json
import sqlite3

from backend.app import main, order_pnl
from backend.app.db import Database, sim_order_event_row


def _position(**overrides):
    row = {
        "instId": "BTC-USDT-SWAP",
        "posSide": "net",
        "pos": "1",
        "avgPx": "64825.9",
        "markPx": "64790.77",
        "upl": "-0.3513",
        "uplRatio": "-0.0542",
        "notionalUsd": "647.467",
    }
    row.update(overrides)
    return row


def test_to_decimal_rejects_dirty_values():
    assert order_pnl.to_decimal("-0.35") is not None
    assert order_pnl.to_decimal("") is None
    assert order_pnl.to_decimal(None) is None
    assert order_pnl.to_decimal("not-a-number") is None


def test_price_change_pct_follows_position_direction():
    long_pct = order_pnl.price_change_pct(_position(pos="1", avgPx="100", markPx="102"))
    short_pct = order_pnl.price_change_pct(_position(pos="-1", avgPx="100", markPx="102"))
    assert float(long_pct) == 2
    assert float(short_pct) == -2
    assert order_pnl.price_change_pct(_position(avgPx="0")) is None


def test_position_pnl_prefers_okx_upl_and_marks_basis():
    pnl = order_pnl.position_pnl(_position())
    assert pnl["pnl_usd"] == "-0.35"
    assert pnl["pnl_basis"] == order_pnl.PNL_BASIS_OKX
    assert float(pnl["pnl_pct"]) < 0


def test_position_pnl_estimates_from_price_when_upl_missing():
    pnl = order_pnl.position_pnl(_position(upl=None, uplRatio=None))
    assert pnl["pnl_basis"] == order_pnl.PNL_BASIS_ESTIMATED
    assert float(pnl["pnl_usd"]) < 0
    assert order_pnl.position_pnl({}) == {}


def test_select_position_uses_hint_then_account_snapshot():
    hint = _position()
    assert order_pnl.select_position({"positions": []}, "BTC-USDT-SWAP", position_hint=hint) is hint
    payload = {"positions": [_position(instId="ETH-USDT-SWAP"), _position()]}
    assert order_pnl.select_position(payload, "BTC-USDT-SWAP")["upl"] == "-0.3513"
    assert order_pnl.select_position({"positions": []}, "BTC-USDT-SWAP") is None


def test_derive_close_pnl_marks_cached_snapshot():
    payload = {"positions": [_position()]}
    fresh = order_pnl.derive_close_pnl(payload, "BTC-USDT-SWAP", position_hint=_position())
    cached = order_pnl.derive_close_pnl(payload, "BTC-USDT-SWAP", cached=True)
    assert fresh["pnl_basis"] == order_pnl.PNL_BASIS_OKX
    assert cached["pnl_basis"] == order_pnl.PNL_BASIS_CACHED


def _signal(signal_id, strategy_id, action, raw):
    return {
        "id": signal_id,
        "strategy_id": strategy_id,
        "strategy_name": f"策略 {strategy_id}",
        "action": action,
        "raw_json": json.dumps(raw, ensure_ascii=False),
    }


def test_signal_pnl_links_indexes_order_ids_and_pnl():
    raw = {
        "action": "stop_loss",
        "profit_pct": "-0.0542",
        "position": _position(),
        "execution_payload": {
            "execution_payload": {
                "steps": [
                    {
                        "result": {
                            "event": {
                                "cl_ord_id": "OKXQ-CLOSE-1",
                                "ord_id": "ORD-CLOSE-1",
                            }
                        }
                    }
                ]
            }
        },
    }
    links = order_pnl.signal_pnl_links([_signal(8, 3, "stop_loss", raw)])
    assert links["OKXQ-CLOSE-1"]["strategy_id"] == 3
    assert links["OKXQ-CLOSE-1"]["signal_id"] == 8
    assert links["OKXQ-CLOSE-1"]["pnl_usd"] == "-0.35"
    assert links["OKXQ-CLOSE-1"]["pnl_basis"] == order_pnl.PNL_BASIS_SIGNAL
    assert links["ORD-CLOSE-1"]["pnl_usd"] == "-0.35"


def test_signal_pnl_links_open_signal_has_no_pnl():
    raw = {
        "notional": "654.702",
        "execution_payload": {
            "execution_payload": {
                "steps": [{"result": {"event": {"cl_ord_id": "OKXQ-OPEN-1"}}}]
            }
        },
    }
    links = order_pnl.signal_pnl_links([_signal(1, 1, "short", raw)])
    assert links["OKXQ-OPEN-1"]["strategy_id"] == 1
    assert "pnl_usd" not in links["OKXQ-OPEN-1"]


def test_nearest_snapshot_pnl_respects_window_and_instrument():
    event = {"ts": 1_000, "inst_id": "BTC-USDT-SWAP", "action": "close-position"}
    snapshots = [
        {"ts": 1_100, "inst_id": "BTC-USDT-SWAP", "pos": "1", "upl": "9", "avg_px": "10", "mark_px": "11", "pos_side": "long"},
        {"ts": 990, "inst_id": "ETH-USDT-SWAP", "pos": "-1", "upl": "-5", "avg_px": "10", "mark_px": "11", "pos_side": "short"},
        {"ts": 980, "inst_id": "BTC-USDT-SWAP", "pos": "1", "upl": "1.25", "avg_px": "10", "mark_px": "11", "pos_side": "long"},
    ]
    pnl = order_pnl.nearest_snapshot_pnl(event, snapshots)
    assert pnl["pnl_usd"] == "1.25"
    assert pnl["pnl_basis"] == order_pnl.PNL_BASIS_SNAPSHOT
    too_old = dict(event, ts=1_000 + order_pnl.SNAPSHOT_WINDOW_MS + 1_000)
    assert order_pnl.nearest_snapshot_pnl(too_old, snapshots) == {}


def test_attach_order_pnl_backfills_and_summarizes():
    events = [
        {"id": 1, "ts": 100, "action": "place", "cl_ord_id": "OPEN-1", "state": "accepted", "pnl_usd": ""},
        {"id": 2, "ts": 200, "action": "close-position", "cl_ord_id": "CLOSE-1", "state": "close_requested", "pnl_usd": ""},
        {"id": 3, "ts": 300, "action": "close-position", "cl_ord_id": "CLOSE-2", "state": "close_requested", "pnl_usd": ""},
        {"id": 4, "ts": 400, "action": "close-position", "cl_ord_id": "CLOSE-3", "state": "failed", "pnl_usd": ""},
    ]
    links = {
        "OPEN-1": {"strategy_id": 1, "strategy_name": "策略 1", "signal_id": 7},
        "CLOSE-1": {"strategy_id": 3, "strategy_name": "策略 3", "signal_id": 8, "pnl_usd": "-0.35", "pnl_pct": "-0.0542", "pnl_basis": "signal-snapshot"},
    }
    snapshots = [{"ts": 295, "inst_id": "BTC-USDT-SWAP", "pos": "1", "upl": "0.50", "avg_px": "10", "mark_px": "10.1", "pos_side": "long"}]
    events[2]["inst_id"] = "BTC-USDT-SWAP"
    summary = order_pnl.attach_order_pnl(events, links, snapshots)

    assert events[0]["strategy_id"] == 1
    assert events[1]["pnl_usd"] == "-0.35"
    assert events[2]["pnl_usd"] == "0.50"
    assert events[2]["pnl_basis"] == order_pnl.PNL_BASIS_SNAPSHOT
    assert "pnl_note" not in events[3]
    assert summary == {"pageRealizedTotal": "0.15", "pricedCloses": 2, "closeCount": 2}


def test_attach_order_pnl_marks_missing_snapshot():
    events = [{"id": 9, "ts": 900, "action": "close-position", "state": "close_requested", "pnl_usd": ""}]
    summary = order_pnl.attach_order_pnl(events, {}, [])
    assert summary == {"pageRealizedTotal": "0.00", "pricedCloses": 0, "closeCount": 1}
    assert "无法计算盈亏" in events[0]["pnl_note"]


def test_sim_order_event_persists_close_pnl(monkeypatch):
    stored = []
    monkeypatch.setattr(main.database, "insert_sim_order_event", lambda event: stored.append(dict(event)))
    monkeypatch.setattr(main, "broadcast_realtime_event", lambda *args, **kwargs: None)
    event = main.sim_order_event(
        "simulated",
        "close-position",
        {"instId": "BTC-USDT-SWAP", "posSide": "net"},
        {"code": "0", "msg": "", "data": [{"clOrdId": "C-1", "sCode": "0"}]},
        "close_requested",
        close_pnl={"pnl_usd": "-0.35", "pnl_pct": "-0.0542", "pnl_basis": "cached-upl"},
    )
    assert event["pnl_usd"] == "-0.35"
    assert stored[0]["pnl_basis"] == "cached-upl"
    assert len(sim_order_event_row(event)) == 22


def test_close_pnl_for_request_reads_cached_position(monkeypatch):
    payload = {"positions": [_position()]}
    monkeypatch.setattr(main, "account_cache_values", lambda environment: (payload, 0, False, 0, 0))
    pnl = main.close_pnl_for_request("simulated", {"instId": "BTC-USDT-SWAP", "posSide": "net"})
    assert pnl["pnl_usd"] == "-0.35"
    assert pnl["pnl_basis"] == order_pnl.PNL_BASIS_CACHED


def test_close_pnl_for_request_never_blocks_on_snapshot_error(monkeypatch):
    def broken(environment):
        raise RuntimeError("account cache unavailable")

    monkeypatch.setattr(main, "account_cache_values", broken)
    assert main.close_pnl_for_request("simulated", {"instId": "BTC-USDT-SWAP"}) == {}


def test_orders_for_environment_enriches_events_without_credentials(monkeypatch):
    class FakeDatabase:
        def list_sim_order_events(self, **kwargs):
            return [
                {"id": 2, "ts": 200, "action": "close-position", "state": "close_requested", "cl_ord_id": "C-1", "inst_id": "BTC-USDT-SWAP", "pnl_usd": ""},
                {"id": 1, "ts": 100, "action": "place", "state": "accepted", "cl_ord_id": "O-1", "inst_id": "BTC-USDT-SWAP", "pnl_usd": ""},
            ]

        def count_sim_order_events(self, **kwargs):
            return 2

        def list_automation_signals(self, **kwargs):
            raw = {
                "action": "stop_loss",
                "profit_pct": "-0.0542",
                "position": _position(),
                "execution_payload": {"execution_payload": {"steps": [{"result": {"event": {"cl_ord_id": "C-1"}}}]}},
            }
            return [_signal(8, 3, "stop_loss", raw)]

        def position_snapshot_rows_between(self, environment, from_ts, to_ts):
            return []

    class FakeSettings:
        live_trading_enabled = False

        def has_credentials_for_environment(self, environment):
            return False

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "settings", FakeSettings())

    payload = main.orders_for_environment("simulated")
    assert payload["pnlSummary"] == {"pageRealizedTotal": "-0.35", "pricedCloses": 1, "closeCount": 1}
    assert payload["events"][0]["pnl_usd"] == "-0.35"
    assert payload["events"][0]["strategy_id"] == 3
    assert payload["events"][0]["signal_id"] == 8


def test_sqlite_migration_adds_pnl_columns_and_roundtrip(tmp_path):
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
    conn.commit()
    conn.close()

    db = Database(f"sqlite:///{path}")
    db.init()
    row = {
        "environment": "simulated", "ts": 1, "action": "close-position",
        "inst_id": "BTC-USDT-SWAP", "cl_ord_id": "C-1", "state": "close_requested",
        "code": "0", "message": "", "request_json": "{}", "response_json": "{}",
        "pnl_usd": "-0.35", "pnl_pct": "-0.0542", "pnl_basis": "cached-upl",
    }
    db.insert_sim_order_event(row)
    loaded = db.list_sim_order_events("simulated")[0]
    assert loaded["pnl_usd"] == "-0.35"
    assert loaded["pnl_basis"] == "cached-upl"


def test_position_snapshot_rows_between_filters_window(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'snap.sqlite3'}")
    db.init()
    db.insert_position_snapshots(
        "simulated", 100, [_position()], json.dumps({"data": [_position()]}, ensure_ascii=False)
    )
    db.insert_position_snapshots(
        "simulated", 300, [_position(instId="ETH-USDT-SWAP")], json.dumps({"data": []}, ensure_ascii=False)
    )
    rows = db.position_snapshot_rows_between("simulated", 90, 200)
    assert len(rows) == 1
    assert rows[0]["inst_id"] == "BTC-USDT-SWAP"
    assert rows[0]["upl"] == "-0.3513"


def test_index_bills_by_order_aggregates_gross_fee_and_net():
    bills = [
        {"clOrdId": "C-1", "pnl": "0.20", "fee": "-0.10", "px": "100", "sz": "1"},
        {"clOrdId": "C-1", "pnl": "0.05", "fee": "-0.03", "px": "101", "sz": "1"},
        {"clOrdId": "C-2", "pnl": "-0.30", "fee": "-0.02", "px": "50", "sz": "2"},
        {"clOrdId": "", "pnl": "1", "fee": "0"},
    ]
    index = order_pnl.index_bills_by_order(bills)
    first = index["C-1"]
    assert first["pnl_usd"] == "0.12"  # (0.20+0.05) + (-0.10-0.03)
    assert first["pnl_gross"] == "0.25"
    assert first["pnl_fee"] == "-0.13"
    assert first["pnl_basis"] == order_pnl.PNL_BASIS_BILLS
    assert first["bill_count"] == 2
    assert index["C-2"]["pnl_usd"] == "-0.32"
    assert "" not in index


def test_settle_order_pnl_overrides_estimate_and_marks_settled():
    event = {"cl_ord_id": "C-1", "pnl_usd": "0.25", "pnl_basis": "cached-upl", "pnl_pct": "0.04"}
    index = {
        "C-1": {
            "pnl_usd": "-0.12",
            "pnl_gross": "0.20",
            "pnl_fee": "-0.32",
            "pnl_basis": order_pnl.PNL_BASIS_BILLS,
            "bill_count": 3,
            "notional": __import__("decimal").Decimal("6475"),
        }
    }
    assert order_pnl.settle_order_pnl(event, index) is True
    assert event["pnl_usd"] == "-0.12"
    assert event["pnl_gross"] == "0.20"
    assert event["pnl_fee"] == "-0.32"
    assert event["pnl_basis"] == order_pnl.PNL_BASIS_BILLS
    assert event["bill_count"] == 3
    assert event["pnl_pct"]  # 由结算金额与名义金额反推
    # 未命中时保留原值
    other = {"cl_ord_id": "MISS", "pnl_usd": "0.25", "pnl_basis": "cached-upl"}
    assert order_pnl.settle_order_pnl(other, index) is False
    assert other["pnl_usd"] == "0.25"


def test_apply_settled_pnl_only_touches_close_events_and_recomputes_summary():
    events = [
        {"action": "place", "state": "accepted", "cl_ord_id": "OPEN", "pnl_usd": ""},
        {"action": "close-position", "state": "close_requested", "cl_ord_id": "C-1", "pnl_usd": "0.25", "pnl_basis": "cached-upl"},
        {"action": "close-position", "state": "close_requested", "cl_ord_id": "MISS", "pnl_usd": "-0.86", "pnl_basis": "position-snapshot"},
        {"action": "close-position", "state": "failed", "cl_ord_id": "C-1", "pnl_usd": ""},
    ]
    index = {
        "C-1": {
            "pnl_usd": "-0.12", "pnl_gross": "0.20", "pnl_fee": "-0.32",
            "pnl_basis": order_pnl.PNL_BASIS_BILLS, "bill_count": 3, "notional": None,
        }
    }
    summary = order_pnl.apply_settled_pnl(events, index)
    assert events[0].get("pnl_settled") is None  # 开仓单不参与
    assert events[1]["pnl_usd"] == "-0.12" and events[1]["pnl_settled"] is True
    assert events[2]["pnl_usd"] == "-0.86" and events[2].get("pnl_settled") is None
    assert events[3].get("pnl_settled") is None  # failed 不参与
    assert summary["closeCount"] == 2  # failed 平仓单不计
    assert summary["settledCloses"] == 1
    assert summary["pricedCloses"] == 2
    assert summary["pageRealizedTotal"] == "-0.98"  # -0.12 + -0.86


def test_index_bills_ignores_dirty_rows():
    bills = [None, "x", {"clOrdId": "C"}, {"clOrdId": "C", "pnl": "abc", "fee": ""}]
    assert order_pnl.index_bills_by_order(bills) == {}


def _signal_row(signal_id, strategy_id, action, decision, ts, inst_id="BTC-USDT-SWAP"):
    return {
        "id": signal_id,
        "strategy_id": strategy_id,
        "strategy_name": f"策略{strategy_id}",
        "action": action,
        "decision": decision,
        "ts": ts,
        "inst_id": inst_id,
    }


def test_automation_open_signals_keeps_only_submitted_longs_and_shorts():
    signals = [
        _signal_row(1, 1, "long", "submitted", 100),
        _signal_row(2, 1, "long", "blocked", 110),
        _signal_row(3, 1, "hold", "observed", 120),
        _signal_row(4, 2, "short", "submitted", 90),
        _signal_row(5, 2, "stop_loss", "submitted", 130),
        {"id": 6, "strategy_id": 3, "action": "long", "decision": "submitted", "ts": "170"},
    ]
    opens = order_pnl.automation_open_signals(signals)
    # 缺合约的信号无法归属到具体仓位，直接跳过。
    assert [item["ts"] for item in opens] == [90, 100]
    assert [item["action"] for item in opens] == ["short", "long"]
    assert all(item["inst_id"] == "BTC-USDT-SWAP" for item in opens)


def test_close_strategy_attribution_uses_nearest_preceding_open_on_same_contract():
    signals = [
        _signal_row(1, 1, "long", "submitted", 1_000, "BTC-USDT-SWAP"),
        _signal_row(2, 4, "short", "submitted", 2_000, "ETH-USDT-SWAP"),
        _signal_row(3, 4, "short", "submitted", 2_100, "BTC-USDT-SWAP"),
    ]
    events = [
        {"action": "close-position", "ts": 2_500, "inst_id": "BTC-USDT-SWAP", "side": None},
        {"action": "close-position", "ts": 2_600, "inst_id": "ETH-USDT-SWAP", "side": "buy"},
        {"action": "place", "ts": 2_700, "inst_id": "BTC-USDT-SWAP"},
    ]
    assert order_pnl.close_strategy_attribution(events, signals) == 2
    assert events[0]["close_strategy_id"] == 4
    assert events[0]["close_strategy_name"] == "策略4"
    assert events[1]["close_strategy_id"] == 4
    assert "close_strategy_id" not in events[2]


def test_close_strategy_attribution_respects_window_and_open_side():
    signals = [_signal_row(1, 1, "long", "submitted", 1_000, "BTC-USDT-SWAP")]
    stale = [{"action": "close-position", "ts": 1_000 + order_pnl.ATTRIBUTION_WINDOW_MS + 1, "inst_id": "BTC-USDT-SWAP"}]
    assert order_pnl.close_strategy_attribution(stale, signals) == 0
    assert "close_strategy_id" not in stale[0]

    wrong_side = [{"action": "close-position", "ts": 2_000, "inst_id": "BTC-USDT-SWAP", "side": "buy"}]
    assert order_pnl.close_strategy_attribution(wrong_side, signals) == 0

    right_side = [{"action": "close-position", "ts": 2_000, "inst_id": "BTC-USDT-SWAP", "side": "sell"}]
    assert order_pnl.close_strategy_attribution(right_side, signals) == 1


def test_close_strategy_attribution_ignores_other_contracts_and_empty_inputs():
    signals = [_signal_row(1, 1, "long", "submitted", 1_000, "BTC-USDT-SWAP")]
    events = [{"action": "close-position", "ts": 2_000, "inst_id": "ETH-USDT-SWAP"}]
    assert order_pnl.close_strategy_attribution(events, signals) == 0
    assert order_pnl.close_strategy_attribution([], signals) == 0
    assert order_pnl.close_strategy_attribution(events, []) == 0
    assert order_pnl.automation_open_signals(None) == []


def test_orders_for_environment_marks_which_strategy_position_was_closed(monkeypatch):
    class FakeDatabase:
        def list_sim_order_events(self, **kwargs):
            return [
                {
                    "id": 2,
                    "ts": 2_500,
                    "action": "close-position",
                    "state": "close_requested",
                    "cl_ord_id": "MANUAL-1",
                    "inst_id": "BTC-USDT-SWAP",
                    "origin": "manual",
                }
            ]

        def count_sim_order_events(self, **kwargs):
            return 1

        def sim_order_event_origin_counts(self, **kwargs):
            return {"manual": 1}

        def list_automation_signals(self, limit=100):
            return [_signal_row(9, 4, "short", "submitted", 2_100, "BTC-USDT-SWAP")]

        def position_snapshot_rows_between(self, environment, from_ts, to_ts):
            return []

    class FakeSettings:
        live_trading_enabled = False

        def has_credentials_for_environment(self, environment):
            return False

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "settings", FakeSettings())

    payload = main.orders_for_environment("simulated")
    event = payload["events"][0]
    assert event["origin"] == "manual"
    assert event["close_strategy_id"] == 4
