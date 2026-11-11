import json
from decimal import Decimal

from backend.app.ai_outlook_verification import (
    grade_sample,
    public_sample,
    prediction_sample,
    prompt_sample_context,
    sample_summary,
)
from backend.app.db import Database


BAR = 900_000


def make_sample(direction="long", kind="main_direction", created_at=BAR + 1000):
    return prediction_sample(
        report_id="report-1", inst_id="BTC-USDT-SWAP", kind=kind, bar="15m",
        candles=[{"ts": "0", "close": "99", "confirm": "1"}, {"ts": str(BAR), "close": "100", "confirm": "1"}],
        interval_ms=BAR, created_at=created_at, direction=direction, tick_size="0.1",
        snapshot_id="snapshot-1", prompt_version="test-v1", report_source="llm",
        report_summary="看涨", confidence=70,
        price_plan={"status": "ready", "entryPrice": "100.2", "stopPrice": "99.9", "targetPrice": "101.2", "validUntil": 3 * BAR, "condition": "收盘突破后观察"} if kind == "price_plan_15m" else None,
    )


def test_frozen_sample_identity_and_unscored_state():
    sample = make_sample()
    assert sample["status"] == "pending"
    assert sample["baseline_ts"] == BAR
    assert sample["baseline_close"] == "100"
    assert sample["target_ts"] == 2 * BAR
    assert sample["due_at"] == 3 * BAR
    assert Decimal(sample["threshold_pct"]) == Decimal("0.2")
    assert make_sample()["sample_id"] == sample["sample_id"]
    assert make_sample(direction="short")["sample_id"] != sample["sample_id"]
    assert make_sample(direction="none")["status"] == "not_scored"
    assert make_sample(created_at=3 * BAR)["status"] == "not_scored"
    no_plan = prediction_sample(
        report_id="r", inst_id="BTC-USDT-SWAP", kind="price_plan_15m", bar="15m",
        candles=[{"ts": str(BAR), "close": "100", "confirm": "1"}],
        interval_ms=BAR, created_at=BAR + 1, direction="long", tick_size="0.1",
        snapshot_id="s", prompt_version="test-v1", report_source="llm",
        report_summary="", confidence=0, price_plan={"status": "missed"},
    )
    assert no_plan["status"] == "not_scored"
    waiting = prediction_sample(
        report_id="r", inst_id="BTC-USDT-SWAP", kind="price_plan_15m", bar="15m",
        candles=[{"ts": str(BAR), "close": "100", "confirm": "1"}],
        interval_ms=BAR, created_at=BAR + 1, direction="short", tick_size="0.1",
        snapshot_id="s", prompt_version="test-v1", report_source="llm",
        report_summary="", confidence=0, price_plan={"status": "watch", "priceConditionMet": False, "entryPrice": "98.9"},
    )
    assert public_sample(waiting)["priceConditionMet"] is False
    assert public_sample(make_sample(kind="price_plan_15m"))["priceConditionMet"] is None


def test_exact_complete_candle_and_threshold_grading():
    sample = make_sample()
    def grade(close, ts=2 * BAR, confirm="1", now=3 * BAR):
        return grade_sample(sample, {"ts": str(ts), "close": close, "confirm": confirm}, "okx", now, BAR)

    assert grade("101")["status"] == "hit"
    assert grade("99")["status"] == "miss"
    assert grade("100.1")["status"] == "flat"
    assert grade("101", ts=3 * BAR) is None
    assert grade("101", confirm="0") is None
    assert grade("101", ts=3 * BAR, now=6 * BAR)["status"] == "insufficient_data"
    assert grade("invalid") is None
    assert grade("invalid", now=6 * BAR)["status"] == "insufficient_data"
    assert grade_sample(make_sample(direction="short"), {"ts": str(2 * BAR), "close": "99", "confirm": "1"}, "okx", 3 * BAR, BAR)["status"] == "hit"


def test_price_plan_reference_touch_is_observation_not_fill():
    sample = make_sample(kind="price_plan_15m")
    outcome = grade_sample(sample, {
        "ts": str(2 * BAR), "low": "99.9", "high": "101.1", "close": "101", "confirm": "1"
    }, "okx", 3 * BAR, BAR)
    evidence = json.loads(outcome["evaluation_json"])
    assert outcome["status"] == "hit"
    assert evidence["entryReferenceTouched"] is True
    assert evidence["stopReferenceTouched"] is True
    assert evidence["targetReferenceTouched"] is False
    assert evidence["filledOrder"] is False
    assert evidence["profitMeasured"] is False
    no_touch = grade_sample(sample, {
        "ts": str(2 * BAR), "low": "100.3", "high": "101.1", "close": "101", "confirm": "1"
    }, "okx", 3 * BAR, BAR)
    assert json.loads(no_touch["evaluation_json"])["entryReferenceTouched"] is False


def test_price_plan_checks_target_after_report_and_after_entry_in_separate_minutes():
    sample = make_sample(kind="price_plan_15m")
    minutes = [
        {"ts": str(ts), "low": "100.4", "high": "100.8", "confirm": "1"}
        for ts in range(BAR + 60_000, 3 * BAR, 60_000)
    ]
    minutes[0]["low"] = "100.1"  # Entry opportunity after the report.
    minutes[1]["high"] = "101.3"  # Target in a later complete minute.
    target = {"ts": str(2 * BAR), "low": "100", "high": "101.3", "close": "101", "confirm": "1"}
    outcome = grade_sample(sample, target, "okx", 3 * BAR, BAR, minutes, "okx")
    evidence = json.loads(outcome["evaluation_json"])
    assert evidence["pricePathCoverage"] == "complete"
    assert evidence["entryReachedAfterReport"] is True
    assert evidence["targetReachedAfterReport"] is True
    assert evidence["targetAfterEntryObserved"] is True
    assert public_sample({**sample, **outcome})["targetAfterEntryObserved"] is True

    same_minute = [dict(row) for row in minutes]
    same_minute[0]["high"] = "101.3"
    same_minute[1]["high"] = "100.8"
    evidence = json.loads(grade_sample(sample, target, "okx", 3 * BAR, BAR, same_minute)["evaluation_json"])
    assert evidence["targetReachedAfterReport"] is True
    assert evidence["targetAfterEntryObserved"] is None

    incomplete = [dict(row) for row in minutes[1:]]
    evidence = json.loads(grade_sample(sample, target, "okx", 3 * BAR, BAR, incomplete)["evaluation_json"])
    assert evidence["pricePathCoverage"] == "partial"
    assert evidence["entryReachedAfterReport"] is None
    assert evidence["targetAfterEntryObserved"] is None

    target_before_entry = [dict(row) for row in minutes]
    target_before_entry[0].update({"low": "100.4", "high": "101.3"})
    target_before_entry[1].update({"low": "100.1", "high": "100.8"})
    evidence = json.loads(grade_sample(sample, target, "okx", 3 * BAR, BAR, target_before_entry)["evaluation_json"])
    assert evidence["targetReachedAfterReport"] is True
    assert evidence["targetAfterEntryObserved"] is False

    short_sample = make_sample(direction="short", kind="price_plan_15m")
    short_prediction = json.loads(short_sample["prediction_json"])
    short_prediction.update({"targetPrice": "98.9", "stopPrice": "100.5"})
    short_sample["prediction_json"] = json.dumps(short_prediction)
    short_minutes = [
        {"ts": str(ts), "low": "99.4", "high": "99.8", "confirm": "1"}
        for ts in range(BAR + 60_000, 3 * BAR, 60_000)
    ]
    short_minutes[0]["high"] = "100.3"
    short_minutes[1]["low"] = "98.8"
    short_target = {"ts": str(2 * BAR), "low": "98.8", "high": "100.3", "close": "99", "confirm": "1"}
    evidence = json.loads(grade_sample(short_sample, short_target, "okx", 3 * BAR, BAR, short_minutes)["evaluation_json"])
    assert evidence["entryReachedAfterReport"] is True
    assert evidence["targetReachedAfterReport"] is True
    assert evidence["targetAfterEntryObserved"] is True


def test_quote_entry_is_frozen_and_target_does_not_require_quote_retouch():
    base = make_sample(kind="price_plan_15m")
    quote = prediction_sample(
        report_id="quote-report", inst_id="BTC-USDT-SWAP", kind="price_plan_15m", bar="15m",
        candles=[{"ts": str(BAR), "close": "100", "confirm": "1"}],
        interval_ms=BAR, created_at=BAR + 1_000, direction="long", tick_size="0.1",
        snapshot_id="snapshot-1", prompt_version="test-v1", report_source="llm",
        report_summary="看涨", confidence=70,
        price_plan={"version": 3, "entryBasis": "quote_snapshot", "entryQuoteTs": BAR + 500,
                    "status": "ready", "entryPrice": "100.2", "stopPrice": "99.9",
                    "targetPrice": "101.2", "validUntil": 3 * BAR,
                    "priceLogic": {"entry": "做多用当时卖一价 100.2", "stop": "低点减一跳 99.9", "target": "两倍风险 101.2"}},
    )
    assert quote["sample_id"] != base["sample_id"]
    different_quote = json.loads(quote["prediction_json"])
    assert different_quote["entryQuoteTs"] == BAR + 500
    assert public_sample(quote)["entryQuoteTs"] == BAR + 500
    assert public_sample(quote)["entryBasis"] == "quote_snapshot"
    assert public_sample(quote)["priceLogic"]["entry"] == "做多用当时卖一价 100.2"
    minutes = [{"ts": str(ts), "low": "100.5", "high": "100.8", "confirm": "1"}
               for ts in range(BAR + 60_000, 3 * BAR, 60_000)]
    minutes[1]["high"] = "101.3"
    target = {"ts": str(2 * BAR), "low": "100.5", "high": "101.3", "close": "101", "confirm": "1"}
    evidence = json.loads(grade_sample(quote, target, "okx", 3 * BAR, BAR, minutes, "okx")["evaluation_json"])
    assert evidence["entryReachedAfterReport"] is None
    assert evidence["entryObservedAt"] == BAR + 500
    assert evidence["targetReachedAfterReport"] is True
    assert evidence["targetAfterEntryObserved"] is True
    context = prompt_sample_context(sample_summary([]), [{**quote, **grade_sample(quote, target, "okx", 3 * BAR, BAR, minutes, "okx")}])
    assert context["examples"][0]["entryBasis"] == "quote_snapshot"
    assert context["examples"][0]["priceReferences"]["targetReachedAfterReport"] is True
    assert "entryReferenceTouched" not in context["examples"][0]["priceReferences"]

    stop_first = [dict(row) for row in minutes]
    stop_first[0]["low"] = "99.8"
    evidence = json.loads(grade_sample(quote, target, "okx", 3 * BAR, BAR, stop_first)["evaluation_json"])
    assert evidence["targetReachedAfterReport"] is True
    assert evidence["targetAfterEntryObserved"] is False

    same_minute = [dict(row) for row in minutes]
    same_minute[1]["low"] = "99.8"
    evidence = json.loads(grade_sample(quote, target, "okx", 3 * BAR, BAR, same_minute)["evaluation_json"])
    assert evidence["targetAfterEntryObserved"] is None


def test_price_plan_hypothetical_close_return_is_directional_and_not_realized():
    long_sample = make_sample(kind="price_plan_15m")
    long_outcome = grade_sample(long_sample, {
        "ts": str(2 * BAR), "low": "100.3", "high": "101.1", "close": "101", "confirm": "1",
    }, "okx", 3 * BAR, BAR)
    long_evidence = json.loads(long_outcome["evaluation_json"])
    assert long_evidence["hypotheticalCloseReturnPct"] == "0.80"
    assert long_evidence["entryReferenceTouched"] is False
    assert long_evidence["filledOrder"] is False
    assert long_evidence["profitMeasured"] is False
    assert public_sample({**long_sample, **long_outcome})["hypotheticalCloseReturnPct"] == "0.80"

    short_sample = make_sample(direction="short", kind="price_plan_15m")
    short_gain = grade_sample(short_sample, {"ts": str(2 * BAR), "close": "99", "confirm": "1"}, "okx", 3 * BAR, BAR)
    short_loss = grade_sample(short_sample, {"ts": str(2 * BAR), "close": "101", "confirm": "1"}, "okx", 3 * BAR, BAR)
    assert json.loads(short_gain["evaluation_json"])["hypotheticalCloseReturnPct"] == "1.20"
    assert json.loads(short_loss["evaluation_json"])["hypotheticalCloseReturnPct"] == "-0.80"
    assert public_sample({**short_sample, **short_loss, "evaluation_json": None})["hypotheticalCloseReturnPct"] == "-0.80"
    assert public_sample(short_sample)["hypotheticalCloseReturnPct"] is None
    assert public_sample(make_sample())["hypotheticalCloseReturnPct"] is None


def test_sqlite_dedup_atomic_settlement_and_scoped_feedback(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'samples.db'}")
    db.init()
    sample = make_sample()
    assert db.insert_ai_outlook_sample(sample)
    assert not db.insert_ai_outlook_sample(sample)
    assert db.due_ai_outlook_samples(sample["due_at"] - 1) == []
    due = db.due_ai_outlook_samples(sample["due_at"])
    assert len(due) == 1
    result = grade_sample(due[0], {"ts": str(2 * BAR), "close": "101", "confirm": "1"}, "okx", sample["due_at"], BAR)
    assert db.settle_ai_outlook_sample(sample["sample_id"], result)
    assert not db.settle_ai_outlook_sample(sample["sample_id"], result)
    assert db.due_ai_outlook_samples(sample["due_at"] + BAR) == []
    assert db.list_ai_outlook_samples("ETH-USDT-SWAP", "test-v1") == []
    assert db.list_ai_outlook_samples("BTC-USDT-SWAP", "another-version") == []
    rows = db.list_ai_outlook_samples("BTC-USDT-SWAP", "test-v1", verified_only=True)
    assert len(rows) == 1 and rows[0]["status"] == "hit"
    summary = sample_summary(db.ai_outlook_sample_counts("BTC-USDT-SWAP", "test-v1"))
    assert summary["main_direction"]["scored"] == 1
    assert summary["main_direction"]["hitRatePct"] is None
    context = prompt_sample_context(summary, rows)
    assert context["mainDirection"]["hit"] == 1
    assert context["examples"][0]["result"] == "hit"
    assert "pending" not in json.dumps(context)


def test_reconciliation_uses_exact_future_complete_candle(tmp_path, monkeypatch):
    from backend.app import main

    db = Database(f"sqlite:///{tmp_path / 'reconcile.db'}")
    db.init()
    sample = make_sample()
    db.insert_ai_outlook_sample(sample)
    monkeypatch.setattr(main, "database", db)
    candles = [
        {"ts": str(3 * BAR), "close": "103", "confirm": "1"},
        {"ts": str(2 * BAR), "close": "101", "confirm": "0"},
    ]
    monkeypatch.setattr(main, "candle_snapshot_for_inst", lambda inst_id, bar, limit: (candles, {"source": "okx"}))
    assert main.reconcile_due_market_ai_samples(sample["due_at"]) == 0
    assert db.due_ai_outlook_samples(sample["due_at"])[0]["status"] == "pending"
    candles[1]["confirm"] = "1"
    assert main.reconcile_due_market_ai_samples(sample["due_at"]) == 1
    assert db.list_ai_outlook_samples("BTC-USDT-SWAP", "test-v1")[0]["status"] == "hit"


def test_reconciliation_reads_minute_path_for_predicted_take_profit(tmp_path, monkeypatch):
    from backend.app import main

    db = Database(f"sqlite:///{tmp_path / 'target-path.db'}")
    db.init()
    sample = make_sample(kind="price_plan_15m")
    db.insert_ai_outlook_sample(sample)
    minute_rows = [
        {"ts": str(ts), "low": "100.4", "high": "100.8", "confirm": "1"}
        for ts in range(BAR + 60_000, 3 * BAR, 60_000)
    ]
    minute_rows[0]["low"] = "100.1"
    minute_rows[1]["high"] = "101.3"
    reads = []
    def snapshot(inst_id, bar, limit):
        reads.append(bar)
        if bar == "1m":
            return minute_rows, {"source": "okx"}
        return [{"ts": str(2 * BAR), "low": "100.1", "high": "101.3", "close": "101", "confirm": "1"}], {"source": "okx"}
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "candle_snapshot_for_inst", snapshot)
    assert main.reconcile_due_market_ai_samples(sample["due_at"]) == 1
    assert reads == ["15m", "1m"]
    settled = public_sample(db.list_ai_outlook_samples("BTC-USDT-SWAP", "test-v1")[0])
    assert settled["targetReachedAfterReport"] is True
    assert settled["targetAfterEntryObserved"] is True


def test_record_page_lists_and_filters_all_instruments(tmp_path, monkeypatch):
    from backend.app import main

    db = Database(f"sqlite:///{tmp_path / 'records.db'}")
    db.init()
    btc = make_sample()
    eth = {**make_sample(kind="price_plan_15m"), "sample_id": "eth-plan", "inst_id": "ETH-USDT-SWAP", "created_at": btc["created_at"] + 1}
    db.insert_ai_outlook_sample(btc)
    db.insert_ai_outlook_sample(eth)
    monkeypatch.setattr(main, "database", db)

    first = main.market_ai_outlook_evaluation_records(limit=1)
    assert first["total"] == 2
    assert first["samples"][0]["instId"] == "ETH-USDT-SWAP"
    assert first["samples"][0]["entryPrice"] == "100.2"
    assert first["samples"][0]["targetTs"] == 2 * BAR
    assert first["samples"][0]["dueAt"] == 3 * BAR
    assert first["samples"][0]["planValidUntil"] == 3 * BAR
    assert first["samples"][0]["planCondition"] == "收盘突破后观察"
    assert first["samples"][0]["stopPrice"] == "99.9"
    assert first["samples"][0]["targetPrice"] == "101.2"
    second = main.market_ai_outlook_evaluation_records(limit=1, offset=1)
    assert second["samples"][0]["instId"] == "BTC-USDT-SWAP"
    filtered = main.market_ai_outlook_evaluation_records(instId="ETH-USDT-SWAP", kind="price_plan_15m", status="pending")
    assert filtered["total"] == 1
    assert main.market_ai_outlook_evaluation_records(status="miss")["total"] == 0
    no_direction = {**make_sample(direction="none", kind="price_plan_15m"), "sample_id": "no-direction-plan", "created_at": eth["created_at"] + 1}
    db.insert_ai_outlook_sample(no_direction)
    no_price = {**make_sample(kind="price_plan_15m"), "sample_id": "no-price-plan", "created_at": eth["created_at"] + 2,
                "prediction_json": json.dumps({"entryPrice": "", "planStatus": "missed"})}
    db.insert_ai_outlook_sample(no_price)
    priced = main.market_ai_outlook_evaluation_records(kind="price_plan_15m", pricedOnly=True)
    assert priced["total"] == 1
    assert priced["samples"][0]["entryPrice"] == "100.2"
    assert main.market_ai_outlook_evaluation_records(kind="price_plan_15m")["total"] == 3


def test_price_plan_retries_stale_independent_15m_read(monkeypatch):
    from backend.app import main

    current = main.now_ms()
    interval = main.CANDLE_BAR_MILLISECONDS["15m"]
    calls = []

    def snapshot(inst_id, bar, limit):
        calls.append((inst_id, bar, limit))
        ts = current - 8 * interval if len(calls) == 1 else current - interval
        return [{"ts": str(ts), "close": "100", "confirm": "1"}], {"source": "database-cache" if len(calls) == 1 else "okx"}

    monkeypatch.setattr(main, "candle_snapshot_for_inst", snapshot)
    candles, meta = main.market_ai_plan_candles("BTC-USDT-SWAP", "1m", {"candles": [{"ts": "1"}]})
    assert len(calls) == 2
    assert calls[0][1] == calls[1][1] == "15m"
    assert meta["source"] == "okx"
    assert int(candles[0]["ts"]) > current - 3 * interval
