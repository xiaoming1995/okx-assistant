"""订单盈亏派生规则（纯函数，不引用 main 的全局单例）。

口径说明：
- 本地订单表记的是「委托请求 + 下单回执」，没有成交价、手续费与开平配对，
  因此不能据此算出交易所口径的已结算盈亏。
- 这里只在**平仓前**读取 OKX 持仓快照中的 ``upl``（未实现盈亏，USDT），
  作为「平仓前浮动盈亏」的近似值，并明确标注 basis，避免把估算值冒充结算值。
- 历史订单没有快照时，尝试用自动化信号里留存的持仓快照 / 浮动百分比回填。
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

CLOSE_ACTIONS = frozenset({"close-position"})
EXIT_SIGNAL_ACTIONS = frozenset({"take_profit", "stop_loss"})
OPEN_SIGNAL_ACTIONS = frozenset({"long", "short"})

# 平仓归属回溯窗口：超过这个时长就不再认为仓位还属于那笔开仓信号。
ATTRIBUTION_WINDOW_MS = 24 * 60 * 60 * 1000

PNL_BASIS_OKX = "okx-upl"
PNL_BASIS_CACHED = "cached-upl"
PNL_BASIS_ESTIMATED = "estimated-price"
PNL_BASIS_SIGNAL = "signal-snapshot"
PNL_BASIS_SNAPSHOT = "position-snapshot"
PNL_BASIS_BILLS = "okx-bills-settled"

SNAPSHOT_WINDOW_MS = 120_000


def to_decimal(value: Any) -> Decimal | None:
    """宽松解析数字；空值、脏数据一律返回 None，不抛异常。"""
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() else None


def decimal_text(value: Decimal | None, places: str) -> str:
    if value is None:
        return ""
    return format(value.quantize(Decimal(places)), "f")


def position_direction(position: dict[str, Any]) -> str:
    pos_side = str(position.get("posSide") or "net").lower()
    size = to_decimal(position.get("pos")) or Decimal("0")
    if pos_side in {"long", "short"}:
        return pos_side
    return "long" if size > 0 else "short"


def price_change_pct(position: dict[str, Any]) -> Decimal | None:
    """线性合约的价格变动百分比（不含杠杆），方向与持仓一致。"""
    avg_px = to_decimal(position.get("avgPx"))
    mark_px = to_decimal(position.get("markPx")) or to_decimal(position.get("last"))
    if not avg_px or avg_px <= 0 or not mark_px or mark_px <= 0:
        return None
    if position_direction(position) == "long":
        return (mark_px - avg_px) / avg_px * Decimal("100")
    return (avg_px - mark_px) / avg_px * Decimal("100")


def position_pnl(position: Any, basis: str = PNL_BASIS_OKX) -> dict[str, str]:
    """把单条持仓快照翻译成订单行可展示的盈亏字段；无法计算时返回空字典。"""
    if not isinstance(position, dict):
        return {}
    upl = to_decimal(position.get("upl"))
    pct = price_change_pct(position)
    notional = to_decimal(position.get("notionalUsd"))
    amount = upl
    if amount is None and pct is not None and notional:
        amount = notional * pct / Decimal("100")
    if amount is None and pct is None:
        return {}
    return {
        "pnl_usd": decimal_text(amount, "0.01"),
        "pnl_pct": decimal_text(pct, "0.0001"),
        "pnl_basis": basis if upl is not None else PNL_BASIS_ESTIMATED,
    }


def select_position(
    account_payload: Any,
    inst_id: str,
    pos_side: str = "",
    position_hint: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """优先用调用方给的持仓（自动化路径是同一轮实时快照），否则从账户快照里找。"""
    if isinstance(position_hint, dict) and position_hint:
        return position_hint
    positions = account_payload.get("positions") if isinstance(account_payload, dict) else None
    if not isinstance(positions, list):
        return None
    target_inst = str(inst_id or "").strip().upper()
    target_side = str(pos_side or "net").strip().lower()
    for row in positions:
        if not isinstance(row, dict):
            continue
        if str(row.get("instId") or "").strip().upper() != target_inst:
            continue
        size = to_decimal(row.get("pos"))
        if size is None or size == 0:
            continue
        row_side = str(row.get("posSide") or "net").strip().lower()
        if target_side not in {"", "net"} and row_side not in {"net", target_side}:
            continue
        return row
    return None


def derive_close_pnl(
    account_payload: Any,
    inst_id: str,
    pos_side: str = "",
    position_hint: dict[str, Any] | None = None,
    cached: bool = False,
) -> dict[str, str]:
    position = select_position(account_payload, inst_id, pos_side, position_hint)
    if position is None:
        return {}
    basis = PNL_BASIS_CACHED if cached and not position_hint else PNL_BASIS_OKX
    return position_pnl(position, basis=basis)


def parse_json_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return None
    return None


def _collect_order_ids(node: Any, found: set[str], depth: int = 0) -> None:
    if depth > 14:
        return
    if isinstance(node, dict):
        for key in ("cl_ord_id", "clOrdId", "ord_id", "ordId"):
            value = node.get(key)
            if isinstance(value, (str, int)) and str(value).strip():
                found.add(str(value).strip())
        for value in node.values():
            _collect_order_ids(value, found, depth + 1)
    elif isinstance(node, list):
        for item in node:
            _collect_order_ids(item, found, depth + 1)


def signal_pnl_links(signals: Any) -> dict[str, dict[str, Any]]:
    """按 clOrdId / ordId 建立「订单 → 策略 / 信号 / 盈亏」的只读索引。"""
    links: dict[str, dict[str, Any]] = {}
    for signal in signals or []:
        if not isinstance(signal, dict):
            continue
        raw = parse_json_value(signal.get("raw_json"))
        if not isinstance(raw, dict):
            continue
        action = str(signal.get("action") or raw.get("action") or "")
        info: dict[str, Any] = {
            "strategy_id": signal.get("strategy_id"),
            "strategy_name": signal.get("strategy_name") or "",
            "signal_id": signal.get("id"),
            "action": action,
        }
        if action in EXIT_SIGNAL_ACTIONS:
            pnl = position_pnl(raw.get("position"), basis=PNL_BASIS_SIGNAL)
            if not pnl.get("pnl_pct"):
                pct = to_decimal(raw.get("profit_pct"))
                if pct is not None:
                    pnl = {
                        "pnl_usd": pnl.get("pnl_usd", ""),
                        "pnl_pct": decimal_text(pct, "0.0001"),
                        "pnl_basis": PNL_BASIS_SIGNAL,
                    }
            if pnl:
                pnl["pnl_basis"] = PNL_BASIS_SIGNAL
                info.update(pnl)
        ids: set[str] = set()
        _collect_order_ids(raw.get("execution_payload"), ids)
        _collect_order_ids(raw.get("execution_steps"), ids)
        for key in ids:
            links.setdefault(key, info)
    return links


def snapshot_position(row: dict[str, Any]) -> dict[str, Any]:
    """把持仓快照表的列名映射回 OKX 持仓字段。"""
    return {
        "instId": row.get("inst_id"),
        "pos": row.get("pos"),
        "posSide": row.get("pos_side"),
        "avgPx": row.get("avg_px"),
        "markPx": row.get("mark_px"),
        "upl": row.get("upl"),
        "uplRatio": row.get("upl_ratio"),
    }


def nearest_snapshot_pnl(event: dict[str, Any], snapshots: Any) -> dict[str, str]:
    """历史平仓单没有自己的快照时，取平仓前最近一次同合约持仓快照。"""
    event_ts = to_decimal(event.get("ts"))
    inst_id = str(event.get("inst_id") or "").strip().upper()
    if event_ts is None or not inst_id or not isinstance(snapshots, list):
        return {}
    for row in snapshots:
        if not isinstance(row, dict):
            continue
        row_ts = to_decimal(row.get("ts"))
        if row_ts is None or row_ts > event_ts or event_ts - row_ts > SNAPSHOT_WINDOW_MS:
            continue
        if str(row.get("inst_id") or "").strip().upper() != inst_id:
            continue
        size = to_decimal(row.get("pos"))
        if size is None or size == 0:
            continue
        return position_pnl(snapshot_position(row), basis=PNL_BASIS_SNAPSHOT)
    return {}


def attach_order_pnl(
    events: Any,
    links: dict[str, dict[str, Any]] | None,
    snapshots: Any = None,
) -> dict[str, Any]:
    """把来源策略与盈亏回填到订单行，并汇总本页可计价的平仓盈亏。"""
    summary: dict[str, Any] = {"pageRealizedTotal": "0.00", "pricedCloses": 0, "closeCount": 0}
    total = Decimal("0")
    for event in events or []:
        if not isinstance(event, dict):
            continue
        key = str(event.get("cl_ord_id") or event.get("ord_id") or "").strip()
        link = (links or {}).get(key)
        if link:
            event["strategy_id"] = link.get("strategy_id")
            event["strategy_name"] = link.get("strategy_name") or ""
            event["signal_id"] = link.get("signal_id")
        is_close = (
            str(event.get("action") or "") in CLOSE_ACTIONS
            and str(event.get("state") or "") != "failed"
        )
        if not is_close:
            continue
        summary["closeCount"] += 1
        if not event.get("pnl_usd") and link and link.get("pnl_usd"):
            event["pnl_usd"] = link["pnl_usd"]
            event["pnl_pct"] = link.get("pnl_pct") or ""
            event["pnl_basis"] = PNL_BASIS_SIGNAL
        if not event.get("pnl_usd"):
            snapshot_pnl = nearest_snapshot_pnl(event, snapshots)
            if snapshot_pnl.get("pnl_usd"):
                event["pnl_usd"] = snapshot_pnl["pnl_usd"]
                event["pnl_pct"] = snapshot_pnl.get("pnl_pct") or ""
                event["pnl_basis"] = snapshot_pnl.get("pnl_basis") or PNL_BASIS_SNAPSHOT
        amount = to_decimal(event.get("pnl_usd"))
        if amount is None:
            event["pnl_note"] = "该笔平仓没有平仓前持仓快照，无法计算盈亏。"
        else:
            total += amount
            summary["pricedCloses"] += 1
    summary["pageRealizedTotal"] = decimal_text(total, "0.01")
    return summary


def automation_open_signals(signals: Any) -> list[dict[str, Any]]:
    """把「真正提交过」的自动化开仓信号整理成时序表，用于回溯平仓归属。

    只认 ``decision=submitted`` 且动作为 long/short 的信号：被风控拦下、
    跳过或只是观望的信号不会产生持仓，不参与归属。
    """
    opens: list[dict[str, Any]] = []
    for signal in signals or []:
        if not isinstance(signal, dict):
            continue
        action = str(signal.get("action") or "")
        if action not in OPEN_SIGNAL_ACTIONS:
            continue
        decision = str(signal.get("decision") or "").strip().lower()
        if decision and decision != "submitted":
            continue
        ts = to_decimal(signal.get("ts"))
        inst_id = str(signal.get("inst_id") or "").strip().upper()
        if ts is None or not inst_id:
            continue
        opens.append(
            {
                "ts": int(ts),
                "inst_id": inst_id,
                "action": action,
                "strategy_id": signal.get("strategy_id"),
                "strategy_name": signal.get("strategy_name") or "",
            }
        )
    opens.sort(key=lambda item: item["ts"])
    return opens


def close_strategy_attribution(events: Any, signals: Any) -> int:
    """给平仓单补上「平的是哪个策略的仓位」。

    订单来源只回答「谁按下了这个操作」，回答不了「平掉的是谁的仓」。例如
    自动化开仓后被手动平掉时，来源是手动，但仓位仍属于某条策略，订单里看
    不出这层关系。这里按「同合约、平仓时间之前最近一笔已提交的自动化开仓
    信号（默认 24 小时内）」回填 ``close_strategy_id`` / ``close_strategy_name``。

    命中与否不影响来源判断，只是给平仓单补充上下文。
    """
    opens = automation_open_signals(signals)
    if not opens:
        return 0
    matched = 0
    for event in events or []:
        if not isinstance(event, dict):
            continue
        if str(event.get("action") or "") not in CLOSE_ACTIONS:
            continue
        ts = to_decimal(event.get("ts"))
        inst_id = str(event.get("inst_id") or "").strip().upper()
        if ts is None or not inst_id:
            continue
        event_ts = int(ts)
        close_side = str(event.get("side") or "").strip().lower()
        best: dict[str, Any] | None = None
        for item in opens:
            if item["inst_id"] != inst_id:
                continue
            if item["ts"] > event_ts or event_ts - item["ts"] > ATTRIBUTION_WINDOW_MS:
                continue
            # 市价全平可能不带 side（净持仓全平），带 side 时才按方向校验。
            if close_side == "sell" and item["action"] != "long":
                continue
            if close_side == "buy" and item["action"] != "short":
                continue
            best = item
        if best is not None:
            event["close_strategy_id"] = best["strategy_id"]
            event["close_strategy_name"] = best["strategy_name"]
            matched += 1
    return matched


def index_bills_by_order(bills: Any) -> dict[str, dict[str, Any]]:
    """把 OKX 交易账单流水按 clOrdId 聚合为该订单的结算盈亏。

    OKX 的 ``/api/v5/account/bills``（type=2）每条是一笔成交，带 ``pnl``（该笔
    已实现毛盈亏）与 ``fee``（手续费，负数扣减）。同一订单可能拆成多笔成交，
    按 clOrdId 求和即得该订单的：
    - gross：毛盈亏（不含手续费）
    - fee：手续费合计（负数为扣减）
    - net：结算净盈亏 = gross + fee
    - pnl_pct：用成交名义金额加权反推的成本基准算出的收益率

    这也是交易所口径，能覆盖「平仓前浮动盈亏」估算含手续费与滑点的盲区。
    """
    index: dict[str, dict[str, Any]] = {}
    for bill in bills or []:
        if not isinstance(bill, dict):
            continue
        cl_ord_id = str(bill.get("clOrdId") or "").strip()
        if not cl_ord_id:
            continue
        pnl = to_decimal(bill.get("pnl"))
        fee = to_decimal(bill.get("fee"))
        if pnl is None and fee is None:
            continue
        px = to_decimal(bill.get("px"))
        sz = to_decimal(bill.get("sz"))
        # 逐笔手续费 / 名义金额 -> 费率，用于反推整笔名义本金（ctVal 已含在 fillSz 语义里，
        # 这里用 pnl 与名义的比值口径；真正的收益率仍以毛盈亏/成本为准，见 settle_order_pnl）。
        entry = index.setdefault(
            cl_ord_id,
            {"gross": Decimal("0"), "fee": Decimal("0"), "notional": Decimal("0"), "count": 0},
        )
        entry["gross"] += pnl or Decimal("0")
        entry["fee"] += fee or Decimal("0")
        if px is not None and sz is not None and px > 0 and sz > 0:
            entry["notional"] += px * sz
        entry["count"] += 1

    result: dict[str, dict[str, Any]] = {}
    for cl_ord_id, entry in index.items():
        gross = entry["gross"]
        fee = entry["fee"]
        net = gross + fee
        result[cl_ord_id] = {
            "pnl_usd": decimal_text(net, "0.01"),
            "pnl_gross": decimal_text(gross, "0.01"),
            "pnl_fee": decimal_text(fee, "0.01"),
            "pnl_basis": PNL_BASIS_BILLS,
            "bill_count": int(entry["count"]),
            "notional": entry["notional"],
        }
    return result


def settle_order_pnl(event: dict[str, Any], bills_index: dict[str, dict[str, Any]]) -> bool:
    """用账单结算值覆盖单条平仓订单的估算盈亏。

    命中返回 True（并把 pnl_usd/pnl_pct/pnl_basis/pnl_gross/pnl_fee 写回 event），
    未命中保持原值返回 False。pct 口径为「净盈亏 / 成交名义金额」的有符号百分比；
    名义金额缺失时 pct 留空，但金额仍以结算值为准。
    """
    key = str(event.get("cl_ord_id") or event.get("ord_id") or "").strip()
    settled = bills_index.get(key)
    if not settled or not settled.get("pnl_usd"):
        return False
    net = to_decimal(settled["pnl_usd"])
    if net is None:
        return False
    event["pnl_usd"] = decimal_text(net, "0.01")
    event["pnl_gross"] = settled.get("pnl_gross") or ""
    event["pnl_fee"] = settled.get("pnl_fee") or ""
    event["pnl_basis"] = PNL_BASIS_BILLS
    event["bill_count"] = settled.get("bill_count") or 0
    notional = settled.get("notional")
    if isinstance(notional, Decimal) and notional > 0:
        event["pnl_pct"] = decimal_text(net / notional * Decimal("100"), "0.0001")
    else:
        event["pnl_pct"] = ""
    event.pop("pnl_note", None)
    return True


def apply_settled_pnl(events: Any, bills_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """把账单结算盈亏应用到所有平仓订单并重算本页汇总。

    仅覆盖 ``action=close-position`` 且非 failed 的订单；其余订单不动。
    命中结算的订单标注 ``pnl_settled=True`` 供前端区分「结算」与「估算」。
    """
    summary: dict[str, Any] = {
        "pageRealizedTotal": "0.00",
        "pricedCloses": 0,
        "closeCount": 0,
        "settledCloses": 0,
    }
    total = Decimal("0")
    for event in events or []:
        if not isinstance(event, dict):
            continue
        is_close = (
            str(event.get("action") or "") in CLOSE_ACTIONS
            and str(event.get("state") or "") != "failed"
        )
        if not is_close:
            continue
        summary["closeCount"] += 1
        if settle_order_pnl(event, bills_index):
            event["pnl_settled"] = True
            summary["settledCloses"] += 1
        amount = to_decimal(event.get("pnl_usd"))
        if amount is not None:
            total += amount
            summary["pricedCloses"] += 1
    summary["pageRealizedTotal"] = decimal_text(total, "0.01")
    return summary
