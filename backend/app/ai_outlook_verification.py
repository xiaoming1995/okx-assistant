"""Deterministic, read-only grading for AI market outlook directions."""

from __future__ import annotations

import hashlib
import json
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


CRITERION_VERSION = 1
MIN_SIGNIFICANT_MOVE_PCT = Decimal("0.1")
MIN_RATE_SAMPLE_COUNT = 5
SAMPLE_KINDS = ("main_direction", "price_plan_15m")


def number(value: Any) -> Decimal | None:
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def hypothetical_close_return_pct(sample: dict[str, Any], prediction: dict[str, Any], observed_close: Any) -> str | None:
    """Price-reference to target-close change in the predicted direction, without assuming a fill."""
    if sample.get("kind") != "price_plan_15m" or sample.get("direction") not in {"long", "short"}:
        return None
    entry = number(prediction.get("entryPrice"))
    observed = number(observed_close)
    if entry is None or entry <= 0 or observed is None or observed <= 0:
        return None
    change = (observed - entry) / entry * 100
    if sample["direction"] == "short":
        change = -change
    rounded = change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{Decimal('0.00') if rounded == 0 else rounded:.2f}"


def completed_candle(candles: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = [row for row in candles if isinstance(row, dict) and str(row.get("confirm") or "") == "1"]
    return max(rows, key=lambda row: int(row.get("ts") or 0)) if rows else None


def prediction_sample(
    *, report_id: str, inst_id: str, kind: str, bar: str, candles: list[dict[str, Any]],
    interval_ms: int, created_at: int, direction: str, tick_size: Any, snapshot_id: str,
    prompt_version: str, report_source: str, report_summary: str, confidence: Any,
    price_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline = completed_candle(candles)
    baseline_ts = int(baseline.get("ts") or 0) if baseline else 0
    baseline_close = number(baseline.get("close")) if baseline else None
    tick = number(tick_size)
    valid_direction = direction in {"long", "short"}
    target_ts = baseline_ts + interval_ms if baseline_ts else 0
    due_at = target_ts + interval_ms if target_ts else 0
    threshold_pct = max(
        MIN_SIGNIFICANT_MOVE_PCT,
        tick * 2 / baseline_close * 100 if tick is not None and tick > 0 and baseline_close is not None and baseline_close > 0 else Decimal("0"),
    )
    plan_status = str((price_plan or {}).get("status") or "")
    scorable = bool(
        valid_direction and baseline_close is not None and baseline_close > 0
        and target_ts > 0 and created_at < due_at
        and (kind != "price_plan_15m" or plan_status in {"ready", "watch"})
    )
    unscored_reason = ""
    if not valid_direction:
        unscored_reason = "本次没有明确的看涨或看跌方向。"
    elif baseline_close is None or baseline_close <= 0 or target_ts <= 0:
        unscored_reason = "缺少可核验的完整基准 K 线。"
    elif created_at >= due_at:
        unscored_reason = "预测生成时已超过目标 K 线的收盘时间。"
    elif kind == "price_plan_15m" and plan_status not in {"ready", "watch"}:
        unscored_reason = "价格计划未处于有效观察状态。"
    plan_version = int((price_plan or {}).get("version") or 1) if kind == "price_plan_15m" else 0
    identity_parts = (inst_id, kind, bar, str(baseline_ts), direction, prompt_version, str(CRITERION_VERSION))
    if kind == "price_plan_15m":
        identity_parts = (*identity_parts, f"plan-v{plan_version}")
        if plan_version >= 2:
            identity_parts = (*identity_parts, str((price_plan or {}).get("entryQuoteTs") or 0),
                              str((price_plan or {}).get("entryPrice") or ""),
                              str((price_plan or {}).get("targetPrice") or ""))
    identity = "|".join(identity_parts)
    sample_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
    prediction = {
        "criterion": "next_complete_candle_close_direction",
        "criterionVersion": CRITERION_VERSION,
        "minimumMovePct": str(threshold_pct),
        "reportSummary": str(report_summary or "")[:900],
        "confidence": int(confidence or 0),
        "planStatus": plan_status,
        "planVersion": plan_version,
        "entryBasis": str((price_plan or {}).get("entryBasis") or ""),
        "entryQuoteTs": int((price_plan or {}).get("entryQuoteTs") or 0),
        "quoteSource": str((price_plan or {}).get("quoteSource") or ""),
        "priceConditionMet": (price_plan or {}).get("priceConditionMet") if isinstance((price_plan or {}).get("priceConditionMet"), bool) else None,
        "entryPrice": str((price_plan or {}).get("entryPrice") or ""),
        "stopPrice": str((price_plan or {}).get("stopPrice") or ""),
        "targetPrice": str((price_plan or {}).get("targetPrice") or ""),
        "planValidUntil": int((price_plan or {}).get("validUntil") or 0),
        "planCondition": str((price_plan or {}).get("condition") or "")[:500],
        "priceLogic": (price_plan or {}).get("priceLogic") if isinstance((price_plan or {}).get("priceLogic"), dict) else None,
        "unscoredReason": unscored_reason,
    }
    return {
        "sample_id": sample_id,
        "report_id": report_id,
        "inst_id": inst_id,
        "kind": kind,
        "bar": bar,
        "created_at": created_at,
        "due_at": due_at,
        "target_ts": target_ts,
        "direction": direction if valid_direction else "none",
        "status": "pending" if scorable else "not_scored",
        "prompt_version": prompt_version,
        "criterion_version": CRITERION_VERSION,
        "snapshot_id": snapshot_id,
        "report_source": report_source,
        "baseline_ts": baseline_ts,
        "baseline_close": str(baseline_close) if baseline_close is not None else "",
        "threshold_pct": str(threshold_pct),
        "prediction_json": json.dumps(prediction, ensure_ascii=False, separators=(",", ":")),
        "observed_ts": None,
        "observed_close": None,
        "observed_source": None,
        "evaluated_at": None,
        "move_pct": None,
        "evaluation_json": None,
    }


def samples_for_report(
    report: dict[str, Any], market: dict[str, Any], chart_candles: list[dict[str, Any]],
    plan_candles: list[dict[str, Any]], bar_intervals: dict[str, int], created_at: int,
) -> list[dict[str, Any]]:
    instrument = market.get("instrument") if isinstance(market.get("instrument"), dict) else {}
    plan = report.get("pricePlan") if isinstance(report.get("pricePlan"), dict) else {}
    chart = market.get("chartSnapshot") if isinstance(market.get("chartSnapshot"), dict) else {}
    inst_id = str(instrument.get("instId") or "")
    bar = str((market.get("technical") or {}).get("bar") or "15m")
    source = str(report.get("source") or "")
    prompt_version = str(report.get("promptVersion") or "")
    report_id = uuid.uuid4().hex
    stance = str(report.get("stance") or "")
    main_direction = "long" if stance == "bullish" else "short" if stance == "bearish" else "none"
    common = {
        "report_id": report_id,
        "inst_id": inst_id,
        "created_at": created_at,
        "tick_size": instrument.get("tickSize"),
        "prompt_version": prompt_version,
        "report_source": source,
        "report_summary": report.get("summary") or "",
        "confidence": report.get("confidence") or 0,
    }
    return [
        prediction_sample(
            **common, kind="main_direction", bar=bar, candles=chart_candles,
            interval_ms=bar_intervals[bar], direction=main_direction,
            snapshot_id=str(chart.get("snapshotId") or ""),
        ),
        prediction_sample(
            **common, kind="price_plan_15m", bar="15m", candles=plan_candles,
            interval_ms=bar_intervals["15m"], direction=str(plan.get("direction") or "none"),
            snapshot_id=f"15m:{plan.get('lastClosedTs') or 0}:{plan.get('source') or ''}", price_plan=plan,
        ),
    ]


def price_path_evidence(
    sample: dict[str, Any], prediction: dict[str, Any], minute_candles: list[dict[str, Any]] | None,
    minute_source: str = "",
) -> dict[str, Any]:
    """Observe reference levels only in complete 1m candles after the report.

    A candle containing the report timestamp is excluded because its high/low may
    have occurred before the prediction. Separate candles establish price order,
    but never establish an order fill.
    """
    result: dict[str, Any] = {
        "pricePathVersion": 1,
        "pricePathBar": "1m",
        "pricePathSource": minute_source,
        "entryReachedAfterReport": None,
        "targetReachedAfterReport": None,
        "targetAfterEntryObserved": None,
        "pricePathCoverage": "unavailable",
    }
    if sample.get("kind") != "price_plan_15m" or minute_candles is None:
        return result
    entry = number(prediction.get("entryPrice"))
    target = number(prediction.get("targetPrice"))
    stop = number(prediction.get("stopPrice"))
    direction = sample.get("direction")
    if direction not in {"long", "short"} or any(value is None or value <= 0 for value in (entry, target, stop)):
        return result
    if (direction == "long" and not stop < entry < target) or (direction == "short" and not target < entry < stop):
        return result
    created_at = int(sample.get("created_at") or 0)
    due_at = min(int(sample.get("due_at") or 0), int(prediction.get("planValidUntil") or sample.get("due_at") or 0))
    first_ts = (created_at // 60_000 + 1) * 60_000
    expected = list(range(first_ts, due_at, 60_000))
    if not expected:
        return result
    rows: dict[int, tuple[Decimal, Decimal]] = {}
    for row in minute_candles:
        if not isinstance(row, dict) or str(row.get("confirm") or "") != "1":
            continue
        try:
            ts = int(row.get("ts") or 0)
        except (TypeError, ValueError):
            continue
        low, high = number(row.get("low")), number(row.get("high"))
        if ts in expected and low is not None and high is not None and low > 0 and high >= low:
            rows[ts] = (low, high)
    complete = len(rows) == len(expected)
    result.update({
        "pricePathCoverage": "complete" if complete else "partial",
        "pricePathStartsAt": first_ts,
        "pricePathEndsAt": due_at,
        "pricePathReportMinuteExcluded": created_at < first_ts,
        "pricePathObservedBars": len(rows),
        "pricePathExpectedBars": len(expected),
    })
    entry_hits: list[int] = []
    target_hits: list[int] = []
    stop_hits: list[int] = []
    for ts in expected:
        if ts not in rows:
            continue
        low, high = rows[ts]
        entry_seen = low <= entry if direction == "long" else high >= entry
        target_seen = high >= target if direction == "long" else low <= target
        stop_seen = low <= stop if direction == "long" else high >= stop
        if entry_seen:
            entry_hits.append(ts)
        if target_seen:
            target_hits.append(ts)
        if stop_seen:
            stop_hits.append(ts)
    entry_ts = entry_hits[0] if entry_hits else None
    target_ts = target_hits[0] if target_hits else None
    if prediction.get("entryBasis") == "quote_snapshot":
        # The quote is already observable before report generation. A later
        # re-touch is not a prerequisite for testing the target price.
        result["entryObservedAt"] = int(prediction.get("entryQuoteTs") or 0) or None
        result["targetObservedAt"] = target_ts
        result["targetReachedAfterReport"] = True if target_ts is not None else False if complete else None
        if target_ts is None:
            result["targetAfterEntryObserved"] = False if complete else None
            return result
        if any(ts not in rows for ts in range(first_ts, target_ts + 1, 60_000)):
            return result
        earlier_stop = any(ts < target_ts for ts in stop_hits)
        same_minute_stop = target_ts in stop_hits
        result["targetAfterEntryObserved"] = False if earlier_stop else None if same_minute_stop else True
        return result
    result["entryReachedAfterReport"] = True if entry_ts is not None else False if complete else None
    result["targetReachedAfterReport"] = True if target_ts is not None else False if complete else None
    result["entryObservedAt"] = entry_ts
    result["targetObservedAt"] = target_ts
    if entry_ts is None or target_ts is None:
        result["targetAfterEntryObserved"] = False if complete else None
    else:
        for later_target in (ts for ts in target_hits if ts > entry_ts):
            if not all(ts in rows for ts in range(entry_ts, later_target + 1, 60_000)):
                continue
            if any(entry_ts <= ts <= later_target for ts in stop_hits):
                continue
            result["targetAfterEntryObserved"] = True
            break
        if result["targetAfterEntryObserved"] is None and complete:
            ambiguous = entry_ts in target_hits or entry_ts in stop_hits or any(
                ts in stop_hits for ts in target_hits if ts >= entry_ts
            )
            if not ambiguous:
                result["targetAfterEntryObserved"] = False
    # Entry/target or stop/target inside one minute have unknown order.
    return result


def grade_sample(
    sample: dict[str, Any], target_candle: dict[str, Any] | None, source: str,
    evaluated_at: int, interval_ms: int, minute_candles: list[dict[str, Any]] | None = None,
    minute_source: str = "",
) -> dict[str, Any] | None:
    if target_candle is None or str(target_candle.get("confirm") or "") != "1" or int(target_candle.get("ts") or 0) != int(sample["target_ts"]):
        if evaluated_at < int(sample["due_at"]) + 3 * interval_ms:
            return None
        return {
            "status": "insufficient_data", "observed_ts": None, "observed_close": None,
            "observed_source": source, "evaluated_at": evaluated_at, "move_pct": None,
            "evaluation_json": json.dumps({"criterionVersion": sample["criterion_version"], "reason": "目标完整 K 线在重试期限内未获取。"}, ensure_ascii=False),
        }
    baseline = number(sample.get("baseline_close"))
    observed = number(target_candle.get("close"))
    threshold = number(sample.get("threshold_pct"))
    if baseline is None or baseline <= 0 or observed is None or observed <= 0 or threshold is None:
        if evaluated_at < int(sample["due_at"]) + 3 * interval_ms:
            return None
        return {
            "status": "insufficient_data", "observed_ts": int(target_candle["ts"]),
            "observed_close": None, "observed_source": source, "evaluated_at": evaluated_at,
            "move_pct": None,
            "evaluation_json": json.dumps({"criterionVersion": sample["criterion_version"], "reason": "目标 K 线收盘价无效。"}, ensure_ascii=False),
        }
    move_pct = (observed - baseline) / baseline * 100
    if abs(move_pct) < threshold:
        status = "flat"
    elif (move_pct > 0 and sample["direction"] == "long") or (move_pct < 0 and sample["direction"] == "short"):
        status = "hit"
    else:
        status = "miss"
    prediction = json.loads(str(sample.get("prediction_json") or "{}"))
    hypothetical_return = hypothetical_close_return_pct(sample, prediction, observed)
    low = number(target_candle.get("low"))
    high = number(target_candle.get("high"))
    valid_range = low is not None and high is not None and low > 0 and high >= low
    def touched_price(field: str) -> bool | None:
        reference = number(prediction.get(field))
        return low <= reference <= high if valid_range and reference is not None and reference > 0 else None

    path = price_path_evidence(sample, prediction, minute_candles, minute_source)
    return {
        "status": status,
        "observed_ts": int(target_candle["ts"]),
        "observed_close": str(observed),
        "observed_source": source,
        "evaluated_at": evaluated_at,
        "move_pct": str(move_pct.quantize(Decimal("0.0001"))),
        "evaluation_json": json.dumps({
            "criterionVersion": sample["criterion_version"], "thresholdPct": str(threshold),
            "entryReferenceTouched": touched_price("entryPrice"),
            "stopReferenceTouched": touched_price("stopPrice"),
            "targetReferenceTouched": touched_price("targetPrice"),
            **path,
            "hypotheticalCloseReturnPct": hypothetical_return,
            "hypotheticalReturnBasis": "entry_reference_to_target_close_no_costs" if hypothetical_return is not None else None,
            "filledOrder": False, "profitMeasured": False,
        }, ensure_ascii=False, separators=(",", ":")),
    }


def sample_summary(count_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, dict[str, Any]] = {}
    for kind in SAMPLE_KINDS:
        counts = {status: 0 for status in ("pending", "hit", "miss", "flat", "not_scored", "insufficient_data")}
        for row in count_rows:
            if row.get("kind") == kind:
                status = str(row.get("status") or "")
                if status in counts:
                    counts[status] += int(row.get("total") or 0)
        scored = counts["hit"] + counts["miss"]
        by_kind[kind] = {
            **counts,
            "total": sum(counts.values()),
            "scored": scored,
            "hitRatePct": round(counts["hit"] / scored * 100, 1) if scored >= MIN_RATE_SAMPLE_COUNT else None,
            "minimumRateSamples": MIN_RATE_SAMPLE_COUNT,
        }
    return by_kind


def public_sample(sample: dict[str, Any]) -> dict[str, Any]:
    prediction = json.loads(str(sample.get("prediction_json") or "{}"))
    evaluation = json.loads(str(sample.get("evaluation_json") or "{}"))
    hypothetical_return = None
    if sample.get("status") in {"hit", "miss", "flat"}:
        hypothetical_return = evaluation.get("hypotheticalCloseReturnPct")
        if hypothetical_return is None:
            hypothetical_return = hypothetical_close_return_pct(sample, prediction, sample.get("observed_close"))
    return {
        "id": sample.get("sample_id"), "reportId": sample.get("report_id"),
        "kind": sample.get("kind"), "instId": sample.get("inst_id"), "bar": sample.get("bar"),
        "createdAt": sample.get("created_at"), "targetTs": sample.get("target_ts"),
        "dueAt": sample.get("due_at"),
        "direction": sample.get("direction"), "status": sample.get("status"),
        "baselineClose": sample.get("baseline_close"), "observedClose": sample.get("observed_close"),
        "observedTs": sample.get("observed_ts"), "observedSource": sample.get("observed_source"),
        "evaluatedAt": sample.get("evaluated_at"), "movePct": sample.get("move_pct"),
        "thresholdPct": sample.get("threshold_pct"), "criterionVersion": sample.get("criterion_version"),
        "promptVersion": sample.get("prompt_version"), "reportSource": sample.get("report_source"),
        "reportSummary": prediction.get("reportSummary") or "", "confidence": prediction.get("confidence"),
        "entryPrice": prediction.get("entryPrice") or "", "stopPrice": prediction.get("stopPrice") or "",
        "targetPrice": prediction.get("targetPrice") or "", "planStatus": prediction.get("planStatus") or "",
        "planVersion": prediction.get("planVersion") or 1,
        "entryBasis": prediction.get("entryBasis") or "",
        "entryQuoteTs": prediction.get("entryQuoteTs") or None,
        "quoteSource": prediction.get("quoteSource") or "",
        "priceConditionMet": prediction.get("priceConditionMet"),
        "planValidUntil": prediction.get("planValidUntil") or sample.get("due_at"),
        "planCondition": prediction.get("planCondition") or "",
        "priceLogic": prediction.get("priceLogic") if isinstance(prediction.get("priceLogic"), dict) else None,
        "unscoredReason": prediction.get("unscoredReason") or "",
        "entryReferenceTouched": evaluation.get("entryReferenceTouched"),
        "stopReferenceTouched": evaluation.get("stopReferenceTouched"),
        "targetReferenceTouched": evaluation.get("targetReferenceTouched"),
        "entryReachedAfterReport": evaluation.get("entryReachedAfterReport"),
        "targetReachedAfterReport": evaluation.get("targetReachedAfterReport"),
        "targetAfterEntryObserved": evaluation.get("targetAfterEntryObserved"),
        "entryObservedAt": evaluation.get("entryObservedAt"),
        "targetObservedAt": evaluation.get("targetObservedAt"),
        "pricePathCoverage": evaluation.get("pricePathCoverage"),
        "pricePathStartsAt": evaluation.get("pricePathStartsAt"),
        "pricePathEndsAt": evaluation.get("pricePathEndsAt"),
        "pricePathReportMinuteExcluded": evaluation.get("pricePathReportMinuteExcluded"),
        "pricePathSource": evaluation.get("pricePathSource"),
        "hypotheticalCloseReturnPct": hypothetical_return,
    }


def prompt_sample_context(summary: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    examples = []
    for row in samples[:3]:
        if row.get("status") not in {"hit", "miss", "flat"}:
            continue
        example = {
            "kind": row.get("kind"), "bar": row.get("bar"), "direction": row.get("direction"),
            "result": row.get("status"), "movePct": row.get("move_pct"),
        }
        if row.get("kind") == "price_plan_15m":
            evaluation = json.loads(str(row.get("evaluation_json") or "{}"))
            prediction = json.loads(str(row.get("prediction_json") or "{}"))
            if prediction.get("entryBasis") == "quote_snapshot":
                example["entryBasis"] = "quote_snapshot"
                example["priceReferences"] = {
                    "targetReachedAfterReport": evaluation.get("targetReachedAfterReport"),
                    "targetAfterQuoteObserved": evaluation.get("targetAfterEntryObserved"),
                }
            else:
                example["entryBasis"] = "legacy_breakout"
                example["priceReferences"] = {
                    key: evaluation.get(key)
                    for key in ("entryReferenceTouched", "stopReferenceTouched", "targetReferenceTouched")
                }
        examples.append(example)
    def verified_counts(kind: str) -> dict[str, Any]:
        counts = summary.get(kind) or {}
        return {key: counts.get(key) for key in ("hit", "miss", "flat", "scored", "hitRatePct", "minimumRateSamples")}

    return {
        "criterionVersion": CRITERION_VERSION,
        "scope": "same_instrument_and_prompt_version",
        "directionOnly": True,
        "mainDirection": verified_counts("main_direction"),
        "pricePlan15m": verified_counts("price_plan_15m"),
        "examples": examples,
        "meaning": "历史下一根完整 K 线的方向与参考价触及核验；无法判断触价先后，不是成交、交易盈利、模型训练或未来保证。",
    }
