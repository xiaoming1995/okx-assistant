"""P2-2 交易所侧条件单：纯函数口径换算、payload 构造、数据层 CRUD。"""

from decimal import Decimal

from backend.app import main
from backend.app.db import SqliteDatabase


# ---------- 口径换算 ----------

def test_algo_trigger_prices_long():
    r = main.algo_trigger_prices("50000", "long", "2", "1", "0.1")
    assert r["tpTriggerPx"] == "51000"
    assert r["slTriggerPx"] == "49500"


def test_algo_trigger_prices_short():
    r = main.algo_trigger_prices("50000", "short", "2", "1", "0.1")
    assert r["tpTriggerPx"] == "49000"
    assert r["slTriggerPx"] == "50500"


def test_algo_trigger_prices_no_leverage_multiplier():
    # 关键：不乘杠杆。2% 就是 2%，与 20 倍无关。
    r = main.algo_trigger_prices("100", "long", "2", "2", "0.01")
    assert r["tpTriggerPx"] == "102"
    assert r["slTriggerPx"] == "98"


def test_algo_trigger_prices_rounds_to_favor_later_trigger():
    # tick=0.01，基准 100.05：
    # 做多止盈 1% = 101.0505 → 向上取整到 101.06（更贵才触发，晚于本地阈值）
    # 做多止损 1% = 99.0495 → 向下取整到 99.04（更便宜才触发，晚于本地阈值）
    r = main.algo_trigger_prices("100.05", "long", "1", "1", "0.01")
    assert r["tpTriggerPx"] == "101.06"
    assert r["slTriggerPx"] == "99.04"


def test_algo_trigger_prices_single_leg():
    r_tp = main.algo_trigger_prices("50000", "long", "2", "0", "1")
    assert r_tp["tpTriggerPx"] and not r_tp["slTriggerPx"]
    r_sl = main.algo_trigger_prices("50000", "long", "0", "1", "1")
    assert r_sl["slTriggerPx"] and not r_sl["tpTriggerPx"]


def test_algo_trigger_prices_disabled():
    r = main.algo_trigger_prices("50000", "long", "0", "0", "1")
    assert r == {"tpTriggerPx": "", "slTriggerPx": ""}


def test_algo_trigger_prices_invalid_avg():
    r = main.algo_trigger_prices("", "long", "2", "1", "1")
    assert r == {"tpTriggerPx": "", "slTriggerPx": ""}


def test_algo_trigger_prices_accepts_decimal():
    r = main.algo_trigger_prices(Decimal("50000"), "long", Decimal("2"), Decimal("1"), Decimal("0.1"))
    assert r["tpTriggerPx"] == "51000"


# ---------- payload 构造 ----------

def test_build_algo_payload_oco_long():
    trigger = {"tpTriggerPx": "51000", "slTriggerPx": "49500"}
    p = main.build_algo_order_payload("btc-usdt-swap", "cross", "long", "2", trigger, "OKXALGO0001")
    assert p["instId"] == "BTC-USDT-SWAP"
    assert p["side"] == "sell"  # 多头平仓=卖出
    assert p["posSide"] == "long"
    assert p["ordType"] == "oco"
    assert p["reduceOnly"] is True
    assert p["tpOrdPx"] == "-1" and p["slOrdPx"] == "-1"
    assert p["tpTriggerPxType"] == "mark" and p["slTriggerPxType"] == "mark"
    assert p["attachAlgoClOrdId"] == "OKXALGO0001"


def test_build_algo_payload_single_leg_short():
    trigger = {"tpTriggerPx": "", "slTriggerPx": "50500"}
    p = main.build_algo_order_payload("eth-usdt-swap", "isolated", "short", "1", trigger, "OKXALGO0002")
    assert p["side"] == "buy"  # 空头平仓=买入
    assert p["ordType"] == "conditional"
    assert "tpTriggerPx" not in p
    assert p["slTriggerPx"] == "50500"


def test_build_algo_payload_no_trigger_returns_none():
    assert main.build_algo_order_payload("BTC-USDT-SWAP", "cross", "long", "1", {}, "X") is None


# ---------- 数据层 CRUD ----------

def _db(tmp_path):
    db = SqliteDatabase(str(tmp_path / "algo.sqlite3"))
    db.init()
    return db


def test_algo_order_crud(tmp_path):
    db = _db(tmp_path)
    row = db.upsert_algo_order(
        {
            "algo_cl_ord_id": "A1", "strategy_id": 7, "inst_id": "BTC-USDT-SWAP",
            "pos_side": "long", "td_mode": "cross", "sz": "2", "main_ord_id": "ORD1",
            "avg_px": "50000", "state": "attached", "created_at": 100, "updated_at": 100,
        }
    )
    assert row["algo_cl_ord_id"] == "A1"
    assert db.get_algo_order_by_cl_id("A1")["state"] == "attached"
    assert len(db.list_algo_orders(strategy_id=7)) == 1
    assert len(db.list_algo_orders(strategy_id=99)) == 0
    assert len(db.list_algo_orders(states=["attached"])) == 1
    assert len(db.list_algo_orders(states=["cancelled"])) == 0


def test_algo_order_upsert_updates_state(tmp_path):
    db = _db(tmp_path)
    base = {"algo_cl_ord_id": "A2", "strategy_id": 7, "inst_id": "BTC-USDT-SWAP",
            "pos_side": "short", "created_at": 100, "updated_at": 100, "state": "pending"}
    db.upsert_algo_order(base)
    db.upsert_algo_order({**base, "state": "triggered", "updated_at": 200, "detail": "filled"})
    got = db.get_algo_order_by_cl_id("A2")
    assert got["state"] == "triggered"
    assert got["detail"] == "filled"
    assert len(db.list_algo_orders(strategy_id=7)) == 1  # upsert 不新增


def test_algo_order_delete(tmp_path):
    db = _db(tmp_path)
    db.upsert_algo_order({"algo_cl_ord_id": "A3", "strategy_id": 1, "inst_id": "X",
                          "pos_side": "long", "created_at": 1, "updated_at": 1})
    db.delete_algo_order("A3")
    assert db.get_algo_order_by_cl_id("A3") is None


# ---------- PR2：成交后补挂链路 ----------

def _strategy(enabled_mode=True):
    return {
        "id": 7, "inst_id": "BTC-USDT-SWAP", "td_mode": "cross", "sz": "2",
        "execution_mode": "simulated_auto" if enabled_mode else "signal_only",
        "take_profit_pct": "2", "stop_loss_pct": "1",
    }


class _FakeAlgoDb:
    def __init__(self):
        self.rows = {}

    def get_algo_order_by_cl_id(self, cl_id):
        return self.rows.get(cl_id)

    def upsert_algo_order(self, order):
        self.rows[order["algo_cl_ord_id"]] = dict(order)
        return order


class _FakeAlgoClient:
    def __init__(self, avg_px="50000", reject=False):
        self.avg_px = avg_px
        self.reject = reject
        self.algo_payloads = []

    def place_algo_order(self, payload):
        self.algo_payloads.append(payload)
        if self.reject:
            return {"code": "51000", "data": [], "msg": "mocked reject"}
        return {"code": "0", "data": [{"algoId": "ALGO1", "sCode": "0"}]}

    def get_order(self, ord_id, inst_id):
        return {"avgPx": self.avg_px} if self.avg_px else None


def _patch_common(monkeypatch, db, client, enabled=True):
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", enabled)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    monkeypatch.setattr(main, "resolve_instrument_spec", lambda inst: {"tick_sz": "0.1"})


def test_attach_skipped_when_switch_off(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient()
    _patch_common(monkeypatch, db, client, enabled=False)
    result = main.attach_algo_orders_for_fill(
        _strategy(), {}, {"data": [{"avgPx": "50000", "ordId": "O1"}]}, "long", "EXEC1"
    )
    assert result is None
    assert client.algo_payloads == []


def test_attach_skipped_when_not_simulated_auto(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient()
    _patch_common(monkeypatch, db, client)
    result = main.attach_algo_orders_for_fill(
        _strategy(enabled_mode=False), {}, {"data": [{"avgPx": "50000"}]}, "long", "EXEC1"
    )
    assert result is None
    assert client.algo_payloads == []


def test_attach_places_algo_and_persists(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient(avg_px="50000")
    _patch_common(monkeypatch, db, client)
    result = main.attach_algo_orders_for_fill(
        _strategy(), {}, {"data": [{"avgPx": "50000", "ordId": "O1"}]}, "long", "EXEC1"
    )
    assert result["status"] == "ok"
    assert len(client.algo_payloads) == 1
    p = client.algo_payloads[0]
    assert p["tpTriggerPx"] == "51000" and p["slTriggerPx"] == "49500"  # 2%/1%
    algo_id = p["attachAlgoClOrdId"]
    assert db.rows[algo_id]["state"] == "attached"


def test_attach_uses_get_order_when_response_has_no_avg(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient(avg_px="48000")
    _patch_common(monkeypatch, db, client)
    main.attach_algo_orders_for_fill(
        _strategy(), {}, {"data": [{"ordId": "O1"}]}, "long", "EXEC1"
    )
    assert len(client.algo_payloads) == 1
    # 48000 × 1.02 = 48960 → tick 0.1 整数倍，向上取整不变
    assert client.algo_payloads[0]["tpTriggerPx"] == "48960"


def test_attach_skips_when_no_avg_price(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient(avg_px="")
    _patch_common(monkeypatch, db, client)
    result = main.attach_algo_orders_for_fill(
        _strategy(), {}, {"data": [{"ordId": "O1"}]}, "long", "EXEC1"
    )
    assert result is not None
    assert result["status"] == "skipped"
    assert client.algo_payloads == []


def test_attach_rejection_does_not_raise(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient(reject=True)
    _patch_common(monkeypatch, db, client)
    result = main.attach_algo_orders_for_fill(
        _strategy(), {}, {"data": [{"avgPx": "50000", "ordId": "O1"}]}, "long", "EXEC1"
    )
    assert result is not None
    assert result["status"] == "skipped"
    assert len(client.algo_payloads) == 1
    algo_id = client.algo_payloads[0]["attachAlgoClOrdId"]
    assert "reject" in db.rows[algo_id]["detail"]


def test_attach_is_idempotent(monkeypatch):
    db = _FakeAlgoDb()
    client = _FakeAlgoClient()
    _patch_common(monkeypatch, db, client)
    order = {"data": [{"avgPx": "50000", "ordId": "O1"}]}
    main.attach_algo_orders_for_fill(_strategy(), {}, order, "long", "EXEC1")
    second = main.attach_algo_orders_for_fill(_strategy(), {}, order, "long", "EXEC1")
    assert len(client.algo_payloads) == 1
    assert second["status"] == "skipped"


# ---------- PR3：撤单协调与启动对账 ----------

class _AlgoDbWithList(_FakeAlgoDb):
    def __init__(self, rows=None):
        super().__init__()
        self.rows = {r["algo_cl_ord_id"]: dict(r) for r in (rows or [])}

    def list_algo_orders(self, strategy_id=0, states=None):
        return [
            dict(r) for r in self.rows.values()
            if (not strategy_id or r.get("strategy_id") == strategy_id)
            and (not states or r.get("state") in states)
        ]


class _CancelClient(_FakeAlgoClient):
    def __init__(self, live_algo_ids=None, reject_cancel=False):
        super().__init__()
        self.cancelled = []
        self.live_algo_ids = live_algo_ids if live_algo_ids is not None else []
        self.reject_cancel = reject_cancel

    def cancel_algo_order(self, payload):
        self.cancelled.append(payload)
        if self.reject_cancel:
            return {"code": "50000", "data": []}
        return {"code": "0", "data": [{"sCode": "0"}]}

    def get_algo_orders(self):
        return {"code": "0", "data": [{"algoClOrdId": i} for i in self.live_algo_ids]}


def _algo_row(cl_id, inst="BTC-USDT-SWAP", side="long", sid=7, state="attached"):
    return {"algo_cl_ord_id": cl_id, "strategy_id": sid, "inst_id": inst, "pos_side": side,
            "state": state, "created_at": 100, "updated_at": 100}


def test_cancel_algo_orders_filters_by_inst_and_side(monkeypatch):
    db = _AlgoDbWithList([
        _algo_row("A-LONG", side="long"), _algo_row("A-SHORT", side="short"),
        _algo_row("A-ETH", inst="ETH-USDT-SWAP", side="long"),
        _algo_row("A-OTHERSTRAT", sid=99, side="long"),
    ])
    client = _CancelClient()
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    main.cancel_algo_orders_for_position("BTC-USDT-SWAP", "long", strategy_id=7)
    assert [c["algoClOrdId"] for c in client.cancelled] == ["A-LONG"]
    assert db.rows["A-LONG"]["state"] == "cancelled"
    assert db.rows["A-SHORT"]["state"] == "attached"


def test_cancel_algo_orders_no_strategy_id_scopes_all(monkeypatch):
    db = _AlgoDbWithList([_algo_row("A1", sid=7), _algo_row("A2", sid=99)])
    client = _CancelClient()
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    main.cancel_algo_orders_for_position("BTC-USDT-SWAP", strategy_id=7)
    assert [c["algoClOrdId"] for c in client.cancelled] == ["A1"]


def test_cancel_algo_orders_rejection_keeps_state(monkeypatch):
    db = _AlgoDbWithList([_algo_row("A1")])
    client = _CancelClient(reject_cancel=True)
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    main.cancel_algo_orders_for_position("BTC-USDT-SWAP")
    assert db.rows["A1"]["state"] == "attached"  # 撤单失败不改状态，下次可重试


def test_cancel_algo_orders_disabled_is_noop(monkeypatch):
    db = _AlgoDbWithList([_algo_row("A1")])
    client = _CancelClient()
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", False)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    assert main.cancel_algo_orders_for_position("BTC-USDT-SWAP") == []
    assert client.cancelled == []


def test_reconcile_marks_orphans_and_keeps_live(monkeypatch):
    db = _AlgoDbWithList([_algo_row("LIVE"), _algo_row("GONE")])
    client = _CancelClient(live_algo_ids=["LIVE"])
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    result = main.reconcile_algo_orders_on_startup()
    assert result == {"checked": 2, "orphan": 1, "kept": 1}
    assert db.rows["GONE"]["state"] == "orphan"
    assert db.rows["LIVE"]["state"] == "attached"


def test_reconcile_disabled_is_noop(monkeypatch):
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", False)
    assert main.reconcile_algo_orders_on_startup() == {"checked": 0, "orphan": 0, "kept": 0}


def test_exit_signal_requires_position_for_dedup():
    # 双轨去重的天然基础：无持仓时不生成平仓信号，条件单已平掉仓后本地不会重复平。
    strategy = {"execution_mode": "simulated_auto", "take_profit_pct": "2", "stop_loss_pct": "1",
                "inst_id": "BTC-USDT-SWAP"}
    account = {"positions": []}
    assert main.automation_exit_signal(strategy, account) is None


# ---------- 边界修复：多合约策略归档按策略全撤 ----------

def test_cancel_by_strategy_covers_all_instruments(monkeypatch):
    db = _AlgoDbWithList([
        _algo_row("A-BTC", inst="BTC-USDT-SWAP", sid=7),
        _algo_row("A-ETH", inst="ETH-USDT-SWAP", sid=7),
        _algo_row("A-SOL", inst="SOL-USDT-SWAP", sid=7),
        _algo_row("A-OTHER", inst="BTC-USDT-SWAP", sid=99),
    ])
    client = _CancelClient()
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    # inst_id 传空 + strategy_id=7 → 撤该策略全部合约
    rows = main.cancel_algo_orders_for_position("", strategy_id=7)
    cancelled = {c["algoClOrdId"] for c in client.cancelled}
    assert cancelled == {"A-BTC", "A-ETH", "A-SOL"}
    assert "A-OTHER" not in cancelled  # 其他策略不受影响
    assert len(rows) == 3
    assert all(db.rows[i]["state"] == "cancelled" for i in ("A-BTC", "A-ETH", "A-SOL"))


def test_cancel_by_strategy_uses_each_row_inst_id(monkeypatch):
    db = _AlgoDbWithList([
        _algo_row("A-BTC", inst="BTC-USDT-SWAP", sid=7),
        _algo_row("A-ETH", inst="eth-usdt-swap", sid=7),  # 小写应被规范化
    ])
    client = _CancelClient()
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    main.cancel_algo_orders_for_position("", strategy_id=7)
    insts = {c["algoClOrdId"]: c["instId"] for c in client.cancelled}
    assert insts["A-BTC"] == "BTC-USDT-SWAP"
    assert insts["A-ETH"] == "ETH-USDT-SWAP"  # 用记录自身合约并规范化，而非外部空入参
    assert db.rows["A-ETH"]["inst_id"] == "ETH-USDT-SWAP"


def test_cancel_by_strategy_requires_strategy_id(monkeypatch):
    db = _AlgoDbWithList([_algo_row("A1", sid=7)])
    client = _CancelClient()
    monkeypatch.setattr(main, "EXCHANGE_ALGO_TPSL_ENABLED", True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "client_for_environment", lambda env: client)
    # 空合约 + 无策略 → 安全护栏拒绝，避免误撤全局算法单
    assert main.cancel_algo_orders_for_position("") == []
    assert client.cancelled == []


def test_archive_uses_strategy_scoped_cancel():
    # 锁定归档调用点：按策略维度全撤（传空 inst_id），而非仅主合约。
    import inspect
    src = inspect.getsource(main.archive_automation_strategy)
    assert 'cancel_algo_orders_for_position("", strategy_id=strategy_id)' in src
