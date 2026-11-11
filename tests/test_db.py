from backend.app.db import Database


def test_database_persists_watchlist_and_candles(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()
    db.upsert_instruments(
        [
            {
                "instId": "BTC-USDT-SWAP",
                "instType": "SWAP",
                "state": "live",
            }
        ],
        123,
    )
    db.set_watched("BTC-USDT-SWAP", True, 124)
    db.upsert_candles(
        "BTC-USDT-SWAP",
        "1m",
        [
            {
                "ts": "1000",
                "open": "1",
                "high": "2",
                "low": "0.5",
                "close": "1.5",
                "volume": "10",
            }
        ],
    )

    assert db.watchlist()[0]["inst_id"] == "BTC-USDT-SWAP"
    assert db.latest_candles("BTC-USDT-SWAP", "1m")[0]["close"] == "1.5"


def test_database_reads_latest_account_and_position_snapshots(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()
    db.insert_account_snapshot(
        "live",
        100,
        {"totalEq": "10"},
        '{"data":[{"totalEq":"10"}]}',
    )
    db.insert_account_snapshot(
        "live",
        200,
        {"totalEq": "20"},
        '{"data":[{"totalEq":"20"}]}',
    )
    db.insert_account_snapshot(
        "simulated",
        300,
        {"totalEq": "30"},
        '{"data":[{"totalEq":"30"}]}',
    )
    db.insert_position_snapshots(
        "live",
        200,
        [{"instId": "BTC-USDT-SWAP", "pos": "1"}],
        '{"data":[{"instId":"BTC-USDT-SWAP","pos":"1"}]}',
    )
    db.insert_position_snapshots(
        "simulated",
        300,
        [{"instId": "ETH-USDT-SWAP", "pos": "2"}],
        '{"data":[{"instId":"ETH-USDT-SWAP","pos":"2"}]}',
    )

    account = db.latest_account_snapshot("live")
    positions = db.latest_position_snapshot_payload("live")

    assert account is not None
    assert account["ts"] == 200
    assert '"totalEq":"20"' in account["details_json"]
    assert positions is not None
    assert positions["ts"] == 200
    assert "BTC-USDT-SWAP" in positions["raw_json"]
    assert "ETH-USDT-SWAP" not in positions["raw_json"]


def test_database_persists_sim_order_events(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()
    db.insert_sim_order_event(
        {
            "environment": "simulated",
            "ts": 300,
            "action": "place",
            "inst_id": "BTC-USDT-SWAP",
            "td_mode": "cross",
            "side": "buy",
            "pos_side": "net",
            "ord_type": "limit",
            "px": "100",
            "sz": "1",
            "reduce_only": False,
            "cl_ord_id": "abc",
            "ord_id": "123",
            "state": "accepted",
            "code": "0",
            "message": "",
            "request_json": '{"instId":"BTC-USDT-SWAP"}',
            "response_json": '{"code":"0"}',
        }
    )

    events = db.list_sim_order_events("simulated", "BTC-USDT-SWAP")

    assert len(events) == 1
    assert events[0]["action"] == "place"
    assert events[0]["ord_id"] == "123"
    assert events[0]["state"] == "accepted"


def test_database_filters_and_pages_sim_order_events(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()
    rows = [
        ("BTC-USDT-SWAP", 100, "place", "accepted", "BTC-1", "OK"),
        ("ETH-USDT-SWAP", 200, "place", "failed", "ETH-1", "USDT 保证金不足"),
        ("BTC-USDT-SWAP", 300, "close-position", "failed", "BTC-2", "账户持仓模式不匹配"),
        ("BTC-USDT-SWAP", 400, "place", "accepted", "BTC-3", "Order placed"),
    ]
    for inst_id, ts, action, state, ord_id, message in rows:
        db.insert_sim_order_event(
            {
                "environment": "simulated",
                "ts": ts,
                "action": action,
                "inst_id": inst_id,
                "td_mode": "cross",
                "side": "buy",
                "pos_side": "net",
                "ord_type": "limit",
                "px": "100",
                "sz": "1",
                "reduce_only": False,
                "cl_ord_id": "",
                "ord_id": ord_id,
                "state": state,
                "code": "0",
                "message": message,
                "request_json": f'{{"instId":"{inst_id}"}}',
                "response_json": '{"code":"0"}',
            }
        )

    first_page = db.list_sim_order_events("simulated", "BTC-USDT-SWAP", limit=2, offset=0)
    second_page = db.list_sim_order_events("simulated", "BTC-USDT-SWAP", limit=2, offset=2)
    failed = db.list_sim_order_events("simulated", keyword="持仓", state="failed")

    assert [event["ord_id"] for event in first_page] == ["BTC-3", "BTC-2"]
    assert [event["ord_id"] for event in second_page] == ["BTC-1"]
    assert db.count_sim_order_events("simulated", "BTC-USDT-SWAP") == 3
    assert db.count_sim_order_events("simulated", keyword="保证金") == 1
    assert db.count_sim_order_events("simulated", action="close-position", state="failed") == 1
    assert [event["ord_id"] for event in failed] == ["BTC-2"]


def test_database_persists_app_settings(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()

    db.set_app_setting("trading_environment", "simulated", 400)

    assert db.get_app_setting("trading_environment") == "simulated"


def test_database_persists_market_event_versions(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()
    event = {
        "id": "fed-1", "provider": "Federal Reserve", "provider_event_key": "fomc-2026-09-16",
        "title": "FOMC 会议与利率决议", "category": "monetary", "importance": "high", "state": "scheduled",
        "scheduled_at": 1_000, "source_timezone": "America/New_York", "published_at": None, "fetched_at": 10,
        "actual": None, "forecast": None, "previous_value": "4.00%", "revision": None, "unit": "%", "period_label": "2026-09",
        "source_url": "https://example.test/fomc", "source_summary": "{}", "official": 1, "payload_hash": "scheduled"
    }
    db.upsert_market_event(event)
    event.update({"state": "released", "actual": "4.00%", "fetched_at": 20, "payload_hash": "released"})
    db.upsert_market_event(event)
    event.update({"actual": "4.25%", "fetched_at": 30, "payload_hash": "revised"})
    db.upsert_market_event(event)

    rows = db.list_market_events(0, 2_000, ["monetary"], ["revised"])
    assert rows[0]["actual"] == "4.25%"
    assert len(db.list_market_event_versions("fed-1")) == 3


def test_schedule_only_refresh_cannot_erase_released_market_values(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()
    released = {
        "id": "bls-cpi-1", "provider": "BLS", "provider_event_key": "cpi-2026-09-11",
        "title": "Consumer Price Index", "category": "inflation", "importance": "high", "state": "released",
        "scheduled_at": 1_000, "source_timezone": "America/New_York", "published_at": 20, "fetched_at": 20,
        "actual": "334.980", "forecast": None, "previous_value": "333.918", "revision": None,
        "unit": "CPI-U", "period_label": "2026 August", "source_url": "https://api.bls.gov/example",
        "source_summary": '{"timeKnown": true}', "official": 1, "payload_hash": "released",
    }
    db.upsert_market_event(released)
    schedule_only = {**released, "state": "scheduled", "published_at": None, "fetched_at": 30,
                     "actual": None, "previous_value": None, "unit": None, "period_label": None,
                     "source_url": "https://www.bls.gov/schedule/", "source_summary": '{}', "payload_hash": "schedule"}
    db.upsert_market_event(schedule_only)

    row = db.get_market_event("bls-cpi-1")
    assert row and row["state"] == "released"
    assert row["actual"] == "334.980"
    assert row["previous_value"] == "333.918"
    assert row["source_url"] == "https://api.bls.gov/example"


def test_database_persists_automation_strategy_and_signals(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()

    strategy = db.create_automation_strategy(
        {
            "name": "BTC MA",
            "enabled": False,
            "inst_id": "BTC-USDT-SWAP",
            "bar": "1m",
            "template": "ma_cross",
            "execution_mode": "signal_only",
            "td_mode": "cross",
            "ord_type": "market",
            "sz": "1",
            "fast_window": 5,
            "slow_window": 20,
            "max_order_contracts": "1",
            "max_position_contracts": "5",
            "cooldown_seconds": 300,
            "take_profit_pct": "3",
            "stop_loss_pct": "1",
            "last_eval_ts": None,
            "created_at": 100,
            "updated_at": 100,
        }
    )

    assert strategy["id"]
    assert strategy["inst_id"] == "BTC-USDT-SWAP"
    assert strategy["take_profit_pct"] == "3"
    assert strategy["stop_loss_pct"] == "1"

    strategy["enabled"] = True
    strategy["updated_at"] = 200
    updated = db.update_automation_strategy(strategy["id"], strategy)
    assert updated is not None
    assert bool(updated["enabled"]) is True

    db.set_automation_strategy_last_eval(strategy["id"], 3000, 300)
    assert db.get_automation_strategy(strategy["id"])["last_eval_ts"] == 3000

    signal = db.insert_automation_signal(
        {
            "strategy_id": strategy["id"],
            "ts": 400,
            "environment": "simulated",
            "inst_id": "BTC-USDT-SWAP",
            "bar": "1m",
            "template": "ma_cross",
            "action": "long",
            "side": "buy",
            "pos_side": "long",
            "price": "64000",
            "sz": "1",
            "decision": "signal_only",
            "reason": "fast crossed above slow",
            "message": "recorded",
            "raw_json": '{"action":"long"}',
        }
    )

    assert signal["id"]
    signals = db.list_automation_signals(strategy_id=strategy["id"])
    assert signals[0]["strategy_name"] == "BTC MA"
    assert signals[0]["action"] == "long"
    signal_detail = db.get_automation_signal(signal["id"])
    assert signal_detail is not None
    assert signal_detail["strategy_name"] == "BTC MA"
    assert signal_detail["action"] == "long"
    assert db.get_automation_signal(99999) is None
    assert db.latest_actionable_automation_signal(strategy["id"])["price"] == "64000"


def test_database_preserves_archived_strategy_and_audit_rows(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()

    active = db.create_automation_strategy(
        {
            "name": "Active",
            "enabled": False,
            "archived": False,
            "archived_at": None,
            "archived_reason": "",
            "inst_id": "BTC-USDT-SWAP",
            "bar": "5m",
            "template": "ma_cross",
            "execution_mode": "signal_only",
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
    archived = db.create_automation_strategy(
        {
            "name": "Archived",
            "enabled": False,
            "archived": True,
            "archived_at": 200,
            "archived_reason": "old",
            "inst_id": "ETH-USDT-SWAP",
            "bar": "15m",
            "template": "llm_direct",
            "execution_mode": "simulated_auto",
            "td_mode": "cross",
            "ord_type": "market",
            "sz": "2",
            "fast_window": 5,
            "slow_window": 20,
            "max_order_contracts": "2",
            "max_position_contracts": "5",
            "cooldown_seconds": 300,
            "take_profit_pct": "2",
            "stop_loss_pct": "1",
            "last_eval_ts": None,
            "created_at": 100,
            "updated_at": 100,
        }
    )

    assert bool(active["archived"]) is False
    assert bool(archived["archived"]) is True
    assert len(db.list_automation_strategies()) == 1
    assert len(db.list_automation_strategies(include_archived=True)) == 2

    signal = db.insert_automation_signal(
        {
            "strategy_id": active["id"],
            "ts": 500,
            "environment": "simulated",
            "inst_id": "BTC-USDT-SWAP",
            "bar": "5m",
            "template": "ma_cross",
            "action": "long",
            "side": "buy",
            "pos_side": "long",
            "price": "64000",
            "sz": "1",
            "decision": "submitted",
            "reason": "crossed",
            "message": "submitted",
            "raw_json": '{"risk_snapshot":{"allowed":true,"severity":"ok","message":"pass","checks":[]}}',
        }
    )

    snapshot = db.insert_automation_risk_snapshot(
        {
            "signal_id": signal["id"],
            "strategy_id": active["id"],
            "ts": 500,
            "allowed": False,
            "severity": "warning",
            "message": "blocked",
            "checks_json": "[{\"key\":\"global_pause\"}]",
            "raw_json": '{"preview":true}',
        }
    )
    step = db.insert_automation_execution_step(
        {
            "signal_id": signal["id"],
            "strategy_id": active["id"],
            "step_order": 0,
            "ts": 500,
            "action": "place",
            "status": "ok",
            "message": "submitted",
            "request_json": '{"instId":"BTC-USDT-SWAP"}',
            "response_json": '{"ok":true}',
        }
    )
    alert = db.insert_automation_alert(
        {
            "ts": 500,
            "severity": "warning",
            "source": "risk_block",
            "message": "blocked",
            "strategy_id": active["id"],
            "signal_id": signal["id"],
            "order_event_id": None,
            "acknowledged_at": None,
            "raw_json": '{"reason":"blocked"}',
        }
    )

    assert snapshot["allowed"] in (0, False)
    assert db.get_automation_risk_snapshot(signal["id"])["message"] == "blocked"
    assert db.list_automation_execution_steps(signal["id"])[0]["action"] == "place"
    assert db.list_automation_alerts(active_only=True)[0]["id"] == alert["id"]
    assert db.count_automation_alerts(active_only=True) == 1
    db.acknowledge_automation_alert(alert["id"], 600)
    assert db.count_automation_alerts(active_only=True) == 0


def test_database_persists_llm_usage_logs(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'okx.sqlite3'}")
    db.init()

    inserted = db.insert_llm_usage_log(
        {
            "request_id": "req-1",
            "ts": 500,
            "provider": "openai_compatible",
            "model": "deepseek-v4-flash",
            "mode": "direct_signal",
            "request_type": "direct_signal",
            "status": "success",
            "strategy_id": 7,
            "signal_id": None,
            "inst_id": "BTC-USDT-SWAP",
            "bar": "5m",
            "profile_id": "okx-market-reading",
            "profile_version": 1,
            "profile_hash": "profile-hash",
            "prompt_tokens": 120,
            "completion_tokens": 34,
            "total_tokens": 154,
            "cached_tokens": 12,
            "reasoning_tokens": 0,
            "cache_hit_tokens": 12,
            "cache_miss_tokens": 108,
            "duration_ms": 830,
            "timeout_seconds": 20,
            "finish_reason": "stop",
            "error": "",
            "raw_usage_json": '{"total_tokens":154}',
        }
    )
    db.insert_llm_usage_log(
        {
            "request_id": "req-2",
            "ts": 600,
            "provider": "openai_compatible",
            "model": "deepseek-v4-flash",
            "mode": "direct_signal",
            "request_type": "connection_test",
            "status": "failed",
            "strategy_id": None,
            "signal_id": None,
            "inst_id": None,
            "bar": None,
            "prompt_tokens": 10,
            "completion_tokens": 0,
            "total_tokens": 10,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "cache_hit_tokens": 0,
            "cache_miss_tokens": 10,
            "duration_ms": 200,
            "timeout_seconds": 20,
            "finish_reason": "",
            "error": "bad response",
            "raw_usage_json": "{}",
        }
    )

    assert inserted["id"]
    assert inserted["profile_id"] == "okx-market-reading"
    assert inserted["profile_version"] == 1
    assert inserted["profile_hash"] == "profile-hash"
    assert db.count_llm_usage_logs(request_type="direct_signal") == 1
    assert db.list_llm_usage_logs(request_type="direct_signal")[0]["request_id"] == "req-1"
    assert db.list_llm_usage_logs(status="failed")[0]["error"] == "bad response"
    assert db.llm_usage_summary()["total_tokens"] == 164
    assert db.llm_usage_summary()["failed_calls"] == 1
    assert db.llm_usage_summary(since_ts=550)["calls"] == 1
