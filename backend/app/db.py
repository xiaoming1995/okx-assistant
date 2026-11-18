from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import Any, Protocol


AI_OUTLOOK_SAMPLE_COLUMNS = (
    "sample_id", "report_id", "inst_id", "kind", "bar", "created_at", "due_at", "target_ts",
    "direction", "status", "prompt_version", "criterion_version", "snapshot_id", "report_source",
    "baseline_ts", "baseline_close", "threshold_pct", "prediction_json", "observed_ts",
    "observed_close", "observed_source", "evaluated_at", "move_pct", "evaluation_json",
)


def ai_outlook_sample_row(sample: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(sample.get(column) for column in AI_OUTLOOK_SAMPLE_COLUMNS)


def retain_published_market_event(event: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Do not let a later schedule-only refresh erase official released facts."""
    incoming_is_empty_schedule = (
        event.get("state") == "scheduled"
        and not any(event.get(field) for field in ("actual", "forecast", "previous_value", "revision"))
    )
    current_is_published = (
        str(current.get("state") or "") in {"released", "revised"}
        and any(current.get(field) for field in ("actual", "forecast", "previous_value", "revision"))
    )
    if not (incoming_is_empty_schedule and current_is_published):
        return event
    retained = dict(event)
    for field in (
        "state", "published_at", "actual", "forecast", "previous_value", "revision",
        "unit", "period_label", "source_url", "source_summary", "payload_hash",
    ):
        retained[field] = current.get(field)
    return retained


class DatabaseBackend(Protocol):
    def init(self) -> None: ...
    def upsert_instruments(self, instruments: list[dict[str, Any]], updated_at: int) -> None: ...
    def list_instruments(self, query: str = "", limit: int = 200) -> list[dict[str, Any]]: ...
    def set_watched(self, inst_id: str, watched: bool, ts: int) -> None: ...
    def watchlist(self) -> list[dict[str, Any]]: ...
    def upsert_candles(self, inst_id: str, bar: str, candles: list[dict[str, str]]) -> None: ...
    def latest_candles(self, inst_id: str, bar: str, limit: int = 300) -> list[dict[str, Any]]: ...
    def insert_ai_outlook_sample(self, sample: dict[str, Any]) -> bool: ...
    def due_ai_outlook_samples(self, current_ms: int, limit: int = 100) -> list[dict[str, Any]]: ...
    def settle_ai_outlook_sample(self, sample_id: str, settlement: dict[str, Any]) -> bool: ...
    def list_ai_outlook_samples(self, inst_id: str, prompt_version: str = "", limit: int = 50, verified_only: bool = False) -> list[dict[str, Any]]: ...
    def page_ai_outlook_samples(self, inst_id: str = "", status: str = "", kind: str = "", limit: int = 20, offset: int = 0, priced_only: bool = False) -> tuple[list[dict[str, Any]], int]: ...
    def ai_outlook_sample_counts(self, inst_id: str, prompt_version: str) -> list[dict[str, Any]]: ...
    def insert_account_snapshot(self, environment: str, ts: int, payload: dict[str, Any], details_json: str) -> None: ...
    def insert_position_snapshots(
        self, environment: str, ts: int, positions: list[dict[str, Any]], raw_json: str
    ) -> None: ...
    def latest_account_snapshot(self, environment: str) -> dict[str, Any] | None: ...
    def latest_position_snapshot_payload(self, environment: str) -> dict[str, Any] | None: ...
    def position_snapshot_rows_between(self, environment: str, from_ts: int, to_ts: int) -> list[dict[str, Any]]: ...
    def insert_sim_order_event(self, event: dict[str, Any]) -> None: ...
    def list_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        limit: int = 100,
        offset: int = 0,
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> list[dict[str, Any]]: ...
    def count_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> int: ...
    def sim_order_event_origin_counts(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
    ) -> dict[str, int]: ...
    def mark_sim_order_event_origin(self, cl_ord_ids: list[str], origin: str) -> int: ...
    def sim_order_event_origin_for(self, environment: str, cl_ord_id: str) -> str: ...
    def create_automation_strategy(self, strategy: dict[str, Any]) -> dict[str, Any]: ...
    def update_automation_strategy(self, strategy_id: int, strategy: dict[str, Any]) -> dict[str, Any] | None: ...
    def list_automation_strategies(self, include_archived: bool = False) -> list[dict[str, Any]]: ...
    def get_automation_strategy(self, strategy_id: int) -> dict[str, Any] | None: ...
    def set_automation_strategy_last_eval(self, strategy_id: int, last_eval_ts: int, updated_at: int) -> None: ...
    def insert_automation_signal(self, signal: dict[str, Any]) -> dict[str, Any]: ...
    def get_automation_signal(self, signal_id: int) -> dict[str, Any] | None: ...
    def list_automation_signals(self, strategy_id: int = 0, limit: int = 100) -> list[dict[str, Any]]: ...
    def list_automation_signals_since(self, strategy_id: int, since_ts: int) -> list[dict[str, Any]]: ...
    def latest_actionable_automation_signal(self, strategy_id: int) -> dict[str, Any] | None: ...
    def insert_automation_risk_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]: ...
    def get_automation_risk_snapshot(self, signal_id: int) -> dict[str, Any] | None: ...
    def insert_automation_execution_step(self, step: dict[str, Any]) -> dict[str, Any]: ...
    def list_automation_execution_steps(self, signal_id: int) -> list[dict[str, Any]]: ...
    def upsert_algo_order(self, order: dict[str, Any]) -> dict[str, Any]: ...
    def get_algo_order_by_cl_id(self, algo_cl_ord_id: str) -> dict[str, Any] | None: ...
    def list_algo_orders(self, strategy_id: int = 0, states: list[str] | None = None) -> list[dict[str, Any]]: ...
    def delete_algo_order(self, algo_cl_ord_id: str) -> None: ...
    def insert_automation_alert(self, alert: dict[str, Any]) -> dict[str, Any]: ...
    def list_automation_alerts(
        self,
        active_only: bool = False,
        severity: str = "",
        source: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...
    def count_automation_alerts(self, active_only: bool = False, severity: str = "", source: str = "") -> int: ...
    def acknowledge_automation_alert(self, alert_id: int, acknowledged_at: int) -> None: ...
    def insert_llm_usage_log(self, log: dict[str, Any]) -> dict[str, Any]: ...
    def list_llm_usage_logs(
        self, limit: int = 100, offset: int = 0, request_type: str = "", status: str = "", strategy_id: int = 0
    ) -> list[dict[str, Any]]: ...
    def count_llm_usage_logs(self, request_type: str = "", status: str = "", strategy_id: int = 0) -> int: ...
    def llm_usage_summary(self, since_ts: int = 0) -> dict[str, Any]: ...
    def get_app_setting(self, key: str) -> str | None: ...
    def set_app_setting(self, key: str, value: str, ts: int) -> None: ...
    def upsert_market_event(self, event: dict[str, Any]) -> dict[str, Any]: ...
    def prune_unmatched_scheduled_market_events(self, provider: str, event_keys: list[str], start_ts: int, end_ts: int) -> int: ...
    def list_market_events(self, start_ts: int, end_ts: int, categories: list[str], states: list[str]) -> list[dict[str, Any]]: ...
    def count_market_events(self, provider: str = "") -> int: ...
    def get_market_event(self, event_id: str) -> dict[str, Any] | None: ...
    def list_market_event_versions(self, event_id: str) -> list[dict[str, Any]]: ...


class Database:
    def __init__(self, database_url: str):
        if database_url.startswith(("postgresql://", "postgres://")):
            self._backend: DatabaseBackend = PostgresDatabase(database_url)
        else:
            path = database_url.removeprefix("sqlite:///")
            self._backend = SqliteDatabase(path)

    def init(self) -> None:
        self._backend.init()

    def upsert_instruments(self, instruments: list[dict[str, Any]], updated_at: int) -> None:
        self._backend.upsert_instruments(instruments, updated_at)

    def list_instruments(self, query: str = "", limit: int = 200) -> list[dict[str, Any]]:
        return self._backend.list_instruments(query=query, limit=limit)

    def set_watched(self, inst_id: str, watched: bool, ts: int) -> None:
        self._backend.set_watched(inst_id, watched, ts)

    def watchlist(self) -> list[dict[str, Any]]:
        return self._backend.watchlist()

    def upsert_candles(self, inst_id: str, bar: str, candles: list[dict[str, str]]) -> None:
        self._backend.upsert_candles(inst_id, bar, candles)

    def latest_candles(self, inst_id: str, bar: str, limit: int = 300) -> list[dict[str, Any]]:
        return self._backend.latest_candles(inst_id, bar, limit)

    def insert_ai_outlook_sample(self, sample: dict[str, Any]) -> bool:
        return self._backend.insert_ai_outlook_sample(sample)

    def due_ai_outlook_samples(self, current_ms: int, limit: int = 100) -> list[dict[str, Any]]:
        return self._backend.due_ai_outlook_samples(current_ms, limit)

    def settle_ai_outlook_sample(self, sample_id: str, settlement: dict[str, Any]) -> bool:
        return self._backend.settle_ai_outlook_sample(sample_id, settlement)

    def list_ai_outlook_samples(self, inst_id: str, prompt_version: str = "", limit: int = 50, verified_only: bool = False) -> list[dict[str, Any]]:
        return self._backend.list_ai_outlook_samples(inst_id, prompt_version, limit, verified_only)

    def page_ai_outlook_samples(self, inst_id: str = "", status: str = "", kind: str = "", limit: int = 20, offset: int = 0, priced_only: bool = False) -> tuple[list[dict[str, Any]], int]:
        return self._backend.page_ai_outlook_samples(inst_id, status, kind, limit, offset, priced_only)

    def ai_outlook_sample_counts(self, inst_id: str, prompt_version: str) -> list[dict[str, Any]]:
        return self._backend.ai_outlook_sample_counts(inst_id, prompt_version)

    def insert_account_snapshot(self, environment: str, ts: int, payload: dict[str, Any], details_json: str) -> None:
        self._backend.insert_account_snapshot(environment, ts, payload, details_json)

    def insert_position_snapshots(
        self, environment: str, ts: int, positions: list[dict[str, Any]], raw_json: str
    ) -> None:
        self._backend.insert_position_snapshots(environment, ts, positions, raw_json)

    def latest_account_snapshot(self, environment: str) -> dict[str, Any] | None:
        return self._backend.latest_account_snapshot(environment)

    def latest_position_snapshot_payload(self, environment: str) -> dict[str, Any] | None:
        return self._backend.latest_position_snapshot_payload(environment)

    def position_snapshot_rows_between(self, environment: str, from_ts: int, to_ts: int) -> list[dict[str, Any]]:
        return self._backend.position_snapshot_rows_between(environment, from_ts, to_ts)

    def insert_sim_order_event(self, event: dict[str, Any]) -> None:
        self._backend.insert_sim_order_event(event)

    def list_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        limit: int = 100,
        offset: int = 0,
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> list[dict[str, Any]]:
        return self._backend.list_sim_order_events(
            environment=environment,
            inst_id=inst_id,
            limit=limit,
            offset=offset,
            keyword=keyword,
            action=action,
            state=state,
            origin=origin,
        )

    def count_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> int:
        return self._backend.count_sim_order_events(
            environment=environment,
            inst_id=inst_id,
            keyword=keyword,
            action=action,
            state=state,
            origin=origin,
        )

    def sim_order_event_origin_counts(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
    ) -> dict[str, int]:
        return self._backend.sim_order_event_origin_counts(
            environment=environment,
            inst_id=inst_id,
            keyword=keyword,
            action=action,
            state=state,
        )

    def mark_sim_order_event_origin(self, cl_ord_ids: list[str], origin: str) -> int:
        return self._backend.mark_sim_order_event_origin(cl_ord_ids=cl_ord_ids, origin=origin)

    def sim_order_event_origin_for(self, environment: str, cl_ord_id: str) -> str:
        return self._backend.sim_order_event_origin_for(environment=environment, cl_ord_id=cl_ord_id)

    def create_automation_strategy(self, strategy: dict[str, Any]) -> dict[str, Any]:
        return self._backend.create_automation_strategy(strategy)

    def update_automation_strategy(self, strategy_id: int, strategy: dict[str, Any]) -> dict[str, Any] | None:
        return self._backend.update_automation_strategy(strategy_id, strategy)

    def list_automation_strategies(self, include_archived: bool = False) -> list[dict[str, Any]]:
        return self._backend.list_automation_strategies(include_archived=include_archived)

    def get_automation_strategy(self, strategy_id: int) -> dict[str, Any] | None:
        return self._backend.get_automation_strategy(strategy_id)

    def set_automation_strategy_last_eval(self, strategy_id: int, last_eval_ts: int, updated_at: int) -> None:
        self._backend.set_automation_strategy_last_eval(strategy_id, last_eval_ts, updated_at)

    def insert_automation_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        return self._backend.insert_automation_signal(signal)

    def get_automation_signal(self, signal_id: int) -> dict[str, Any] | None:
        return self._backend.get_automation_signal(signal_id)

    def list_automation_signals(self, strategy_id: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        return self._backend.list_automation_signals(strategy_id=strategy_id, limit=limit)

    def list_automation_signals_since(self, strategy_id: int, since_ts: int) -> list[dict[str, Any]]:
        return self._backend.list_automation_signals_since(strategy_id, since_ts)

    def latest_actionable_automation_signal(self, strategy_id: int) -> dict[str, Any] | None:
        return self._backend.latest_actionable_automation_signal(strategy_id)

    def insert_automation_risk_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        return self._backend.insert_automation_risk_snapshot(snapshot)

    def get_automation_risk_snapshot(self, signal_id: int) -> dict[str, Any] | None:
        return self._backend.get_automation_risk_snapshot(signal_id)

    def insert_automation_execution_step(self, step: dict[str, Any]) -> dict[str, Any]:
        return self._backend.insert_automation_execution_step(step)

    def list_automation_execution_steps(self, signal_id: int) -> list[dict[str, Any]]:
        return self._backend.list_automation_execution_steps(signal_id)

    def upsert_algo_order(self, order: dict[str, Any]) -> dict[str, Any]:
        return self._backend.upsert_algo_order(order)

    def get_algo_order_by_cl_id(self, algo_cl_ord_id: str) -> dict[str, Any] | None:
        return self._backend.get_algo_order_by_cl_id(algo_cl_ord_id)

    def list_algo_orders(self, strategy_id: int = 0, states: list[str] | None = None) -> list[dict[str, Any]]:
        return self._backend.list_algo_orders(strategy_id=strategy_id, states=states)

    def delete_algo_order(self, algo_cl_ord_id: str) -> None:
        return self._backend.delete_algo_order(algo_cl_ord_id)

    def insert_automation_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        return self._backend.insert_automation_alert(alert)

    def list_automation_alerts(
        self,
        active_only: bool = False,
        severity: str = "",
        source: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self._backend.list_automation_alerts(
            active_only=active_only,
            severity=severity,
            source=source,
            limit=limit,
        )

    def count_automation_alerts(self, active_only: bool = False, severity: str = "", source: str = "") -> int:
        return self._backend.count_automation_alerts(active_only=active_only, severity=severity, source=source)

    def acknowledge_automation_alert(self, alert_id: int, acknowledged_at: int) -> None:
        self._backend.acknowledge_automation_alert(alert_id, acknowledged_at)

    def insert_llm_usage_log(self, log: dict[str, Any]) -> dict[str, Any]:
        return self._backend.insert_llm_usage_log(log)

    def list_llm_usage_logs(
        self, limit: int = 100, offset: int = 0, request_type: str = "", status: str = "", strategy_id: int = 0
    ) -> list[dict[str, Any]]:
        return self._backend.list_llm_usage_logs(limit=limit, offset=offset, request_type=request_type, status=status, strategy_id=strategy_id)

    def count_llm_usage_logs(self, request_type: str = "", status: str = "", strategy_id: int = 0) -> int:
        return self._backend.count_llm_usage_logs(request_type=request_type, status=status, strategy_id=strategy_id)

    def llm_usage_summary(self, since_ts: int = 0) -> dict[str, Any]:
        return self._backend.llm_usage_summary(since_ts=since_ts)

    def get_app_setting(self, key: str) -> str | None:
        return self._backend.get_app_setting(key)

    def set_app_setting(self, key: str, value: str, ts: int) -> None:
        self._backend.set_app_setting(key, value, ts)

    def upsert_market_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return self._backend.upsert_market_event(event)

    def prune_unmatched_scheduled_market_events(self, provider: str, event_keys: list[str], start_ts: int, end_ts: int) -> int:
        return self._backend.prune_unmatched_scheduled_market_events(provider, event_keys, start_ts, end_ts)

    def list_market_events(self, start_ts: int, end_ts: int, categories: list[str], states: list[str]) -> list[dict[str, Any]]:
        return self._backend.list_market_events(start_ts, end_ts, categories, states)

    def count_market_events(self, provider: str = "") -> int:
        return self._backend.count_market_events(provider)

    def get_market_event(self, event_id: str) -> dict[str, Any] | None:
        return self._backend.get_market_event(event_id)

    def list_market_event_versions(self, event_id: str) -> list[dict[str, Any]]:
        return self._backend.list_market_event_versions(event_id)


class SqliteDatabase:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = RLock()

    def init(self) -> None:
        with self._lock:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS instruments (
                    inst_id TEXT PRIMARY KEY,
                    inst_type TEXT NOT NULL,
                    uly TEXT,
                    inst_family TEXT,
                    base_ccy TEXT,
                    quote_ccy TEXT,
                    settle_ccy TEXT,
                    ct_val TEXT,
                    tick_sz TEXT,
                    lot_sz TEXT,
                    state TEXT,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS watchlist (
                    inst_id TEXT PRIMARY KEY,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS candles (
                    inst_id TEXT NOT NULL,
                    bar TEXT NOT NULL,
                    ts INTEGER NOT NULL,
                    open TEXT NOT NULL,
                    high TEXT NOT NULL,
                    low TEXT NOT NULL,
                    close TEXT NOT NULL,
                    volume TEXT NOT NULL,
                    volume_ccy TEXT,
                    volume_quote TEXT,
                    confirm TEXT,
                    PRIMARY KEY (inst_id, bar, ts)
                );

                CREATE TABLE IF NOT EXISTS account_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    environment TEXT NOT NULL DEFAULT 'live',
                    ts INTEGER NOT NULL,
                    total_eq TEXT,
                    adj_eq TEXT,
                    imr TEXT,
                    mmr TEXT,
                    iso_eq TEXT,
                    details_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS position_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    environment TEXT NOT NULL DEFAULT 'live',
                    ts INTEGER NOT NULL,
                    inst_id TEXT NOT NULL,
                    pos_side TEXT,
                    pos TEXT,
                    avg_px TEXT,
                    mark_px TEXT,
                    upl TEXT,
                    upl_ratio TEXT,
                    margin TEXT,
                    raw_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sim_order_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    environment TEXT NOT NULL DEFAULT 'simulated',
                    ts INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    inst_id TEXT NOT NULL,
                    td_mode TEXT,
                    side TEXT,
                    pos_side TEXT,
                    ord_type TEXT,
                    px TEXT,
                    sz TEXT,
                    reduce_only INTEGER NOT NULL DEFAULT 0,
                    cl_ord_id TEXT,
                    ord_id TEXT,
                    state TEXT,
                    code TEXT,
                    message TEXT,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    pnl_usd TEXT,
                    pnl_pct TEXT,
                    pnl_basis TEXT,
                    origin TEXT NOT NULL DEFAULT 'manual'
                );

                CREATE TABLE IF NOT EXISTS automation_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    archived INTEGER NOT NULL DEFAULT 0,
                    archived_at INTEGER,
                    archived_reason TEXT NOT NULL DEFAULT '',
                    inst_id TEXT NOT NULL,
                    inst_ids TEXT NOT NULL DEFAULT '[]',
                    daily_position_pct TEXT NOT NULL DEFAULT '0',
                    bar TEXT NOT NULL,
                    template TEXT NOT NULL,
                    execution_mode TEXT NOT NULL,
                    td_mode TEXT NOT NULL,
                    ord_type TEXT NOT NULL,
                    sz TEXT NOT NULL,
                    fast_window INTEGER NOT NULL,
                    slow_window INTEGER NOT NULL,
                    max_order_contracts TEXT NOT NULL,
                    max_position_contracts TEXT NOT NULL,
                    cooldown_seconds INTEGER NOT NULL,
                    take_profit_pct TEXT NOT NULL DEFAULT '0',
                    stop_loss_pct TEXT NOT NULL DEFAULT '0',
                    last_eval_ts INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS automation_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    environment TEXT NOT NULL,
                    inst_id TEXT NOT NULL,
                    bar TEXT NOT NULL,
                    template TEXT NOT NULL,
                    action TEXT NOT NULL,
                    side TEXT,
                    pos_side TEXT,
                    price TEXT,
                    sz TEXT,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    message TEXT,
                    raw_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS llm_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    ts INTEGER NOT NULL,
                    provider TEXT,
                    model TEXT,
                    mode TEXT,
                    request_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    strategy_id INTEGER,
                    signal_id INTEGER,
                    inst_id TEXT,
                    bar TEXT,
                    profile_id TEXT,
                    profile_version INTEGER,
                    profile_hash TEXT,
                    prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    completion_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    cached_tokens INTEGER NOT NULL DEFAULT 0,
                    reasoning_tokens INTEGER NOT NULL DEFAULT 0,
                    cache_hit_tokens INTEGER NOT NULL DEFAULT 0,
                    cache_miss_tokens INTEGER NOT NULL DEFAULT 0,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    timeout_seconds INTEGER NOT NULL DEFAULT 0,
                    finish_reason TEXT,
                    error TEXT,
                    raw_usage_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS automation_risk_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    strategy_id INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    allowed INTEGER NOT NULL DEFAULT 0,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    checks_json TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS automation_execution_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    strategy_id INTEGER NOT NULL,
                    step_order INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS automation_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    strategy_id INTEGER,
                    signal_id INTEGER,
                    order_event_id INTEGER,
                    acknowledged_at INTEGER,
                    raw_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS automation_algo_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    algo_cl_ord_id TEXT NOT NULL UNIQUE,
                    strategy_id INTEGER NOT NULL,
                    inst_id TEXT NOT NULL,
                    pos_side TEXT NOT NULL,
                    td_mode TEXT NOT NULL DEFAULT 'cross',
                    sz TEXT NOT NULL DEFAULT '',
                    main_ord_id TEXT NOT NULL DEFAULT '',
                    avg_px TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT 'pending',
                    detail TEXT NOT NULL DEFAULT '',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_algo_orders_strategy
                    ON automation_algo_orders (strategy_id);
                CREATE INDEX IF NOT EXISTS idx_algo_orders_state
                    ON automation_algo_orders (state);

                CREATE INDEX IF NOT EXISTS idx_sim_order_events_ts
                    ON sim_order_events (ts DESC);
                CREATE INDEX IF NOT EXISTS idx_sim_order_events_inst
                    ON sim_order_events (inst_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_automation_strategies_enabled
                    ON automation_strategies (enabled, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_automation_signals_strategy_ts
                    ON automation_signals (strategy_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_automation_signals_ts
                    ON automation_signals (ts DESC);
                CREATE INDEX IF NOT EXISTS idx_automation_risk_snapshots_signal
                    ON automation_risk_snapshots (signal_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_automation_execution_steps_signal
                    ON automation_execution_steps (signal_id, step_order ASC);
                CREATE INDEX IF NOT EXISTS idx_automation_alerts_active
                    ON automation_alerts (acknowledged_at, severity, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_automation_alerts_source
                    ON automation_alerts (source, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_llm_usage_logs_ts
                    ON llm_usage_logs (ts DESC);
                CREATE INDEX IF NOT EXISTS idx_llm_usage_logs_strategy_ts
                    ON llm_usage_logs (strategy_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_llm_usage_logs_request
                    ON llm_usage_logs (request_id);

                CREATE TABLE IF NOT EXISTS market_events (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    provider_event_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance TEXT NOT NULL,
                    state TEXT NOT NULL,
                    scheduled_at BIGINT,
                    source_timezone TEXT NOT NULL,
                    published_at BIGINT,
                    fetched_at BIGINT NOT NULL,
                    actual TEXT,
                    forecast TEXT,
                    previous_value TEXT,
                    revision TEXT,
                    unit TEXT,
                    period_label TEXT,
                    source_url TEXT NOT NULL,
                    source_summary TEXT NOT NULL,
                    official INTEGER NOT NULL DEFAULT 1,
                    payload_hash TEXT NOT NULL,
                    UNIQUE(provider, provider_event_key)
                );
                CREATE TABLE IF NOT EXISTS market_event_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    observed_at BIGINT NOT NULL,
                    state TEXT NOT NULL,
                    actual TEXT,
                    forecast TEXT,
                    previous_value TEXT,
                    revision TEXT,
                    unit TEXT,
                    period_label TEXT,
                    source_summary TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    UNIQUE(event_id, payload_hash)
                );
                CREATE INDEX IF NOT EXISTS idx_market_events_schedule ON market_events (scheduled_at ASC);
                CREATE INDEX IF NOT EXISTS idx_market_events_state ON market_events (state, scheduled_at ASC);
                CREATE INDEX IF NOT EXISTS idx_market_event_versions_event ON market_event_versions (event_id, observed_at ASC);

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_outlook_samples (
                    sample_id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    inst_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    bar TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    due_at INTEGER NOT NULL,
                    target_ts INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    status TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    criterion_version INTEGER NOT NULL,
                    snapshot_id TEXT NOT NULL,
                    report_source TEXT NOT NULL,
                    baseline_ts INTEGER NOT NULL,
                    baseline_close TEXT NOT NULL,
                    threshold_pct TEXT NOT NULL,
                    prediction_json TEXT NOT NULL,
                    observed_ts INTEGER,
                    observed_close TEXT,
                    observed_source TEXT,
                    evaluated_at INTEGER,
                    move_pct TEXT,
                    evaluation_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_ai_outlook_samples_due ON ai_outlook_samples (status, due_at ASC);
                CREATE INDEX IF NOT EXISTS idx_ai_outlook_samples_inst ON ai_outlook_samples (inst_id, prompt_version, created_at DESC);
                """
            )
            self._ensure_column("account_snapshots", "environment", "TEXT NOT NULL DEFAULT 'live'")
            self._ensure_column("position_snapshots", "environment", "TEXT NOT NULL DEFAULT 'live'")
            self._ensure_column("sim_order_events", "environment", "TEXT NOT NULL DEFAULT 'simulated'")
            self._ensure_column("sim_order_events", "pnl_usd", "TEXT")
            self._ensure_column("sim_order_events", "pnl_pct", "TEXT")
            self._ensure_column("sim_order_events", "pnl_basis", "TEXT")
            self._ensure_column("sim_order_events", "origin", "TEXT NOT NULL DEFAULT 'manual'")
            self._ensure_column("automation_strategies", "archived", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column("automation_strategies", "archived_at", "INTEGER")
            self._ensure_column("automation_strategies", "archived_reason", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("automation_strategies", "take_profit_pct", "TEXT NOT NULL DEFAULT '0'")
            self._ensure_column("automation_strategies", "stop_loss_pct", "TEXT NOT NULL DEFAULT '0'")
            self._ensure_column("automation_strategies", "inst_ids", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column("automation_strategies", "daily_position_pct", "TEXT NOT NULL DEFAULT '0'")
            self._ensure_column("llm_usage_logs", "profile_id", "TEXT")
            self._ensure_column("llm_usage_logs", "profile_version", "INTEGER")
            self._ensure_column("llm_usage_logs", "profile_hash", "TEXT")
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_risk_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    strategy_id INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    allowed INTEGER NOT NULL DEFAULT 0,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    checks_json TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_execution_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    strategy_id INTEGER NOT NULL,
                    step_order INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    strategy_id INTEGER,
                    signal_id INTEGER,
                    order_event_id INTEGER,
                    acknowledged_at INTEGER,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self.conn.commit()

    def upsert_market_event(self, event: dict[str, Any]) -> dict[str, Any]:
        columns = ("id", "provider", "provider_event_key", "title", "category", "importance", "state", "scheduled_at", "source_timezone", "published_at", "fetched_at", "actual", "forecast", "previous_value", "revision", "unit", "period_label", "source_url", "source_summary", "official", "payload_hash")
        row = tuple(event.get(column) for column in columns)
        with self._lock:
            current = self.conn.execute("SELECT * FROM market_events WHERE provider = ? AND provider_event_key = ?", (event["provider"], event["provider_event_key"])).fetchone()
            if current:
                event["id"] = str(current["id"])
                current_row = dict(current)
                event = retain_published_market_event(event, current_row)
                if event.get("state") == "released" and str(current["state"]) in {"released", "revised"} and any(
                    (event.get(field) or "") != (current[field] or "") for field in ("actual", "previous_value", "revision", "period_label")
                ):
                    event["state"] = "revised"
                row = tuple(event.get(column) for column in columns)
            self.conn.execute(f"INSERT INTO market_events ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) ON CONFLICT(provider, provider_event_key) DO UPDATE SET title=excluded.title, category=excluded.category, importance=excluded.importance, state=excluded.state, scheduled_at=excluded.scheduled_at, source_timezone=excluded.source_timezone, published_at=excluded.published_at, fetched_at=excluded.fetched_at, actual=excluded.actual, forecast=excluded.forecast, previous_value=excluded.previous_value, revision=excluded.revision, unit=excluded.unit, period_label=excluded.period_label, source_url=excluded.source_url, source_summary=excluded.source_summary, official=excluded.official, payload_hash=excluded.payload_hash", row)
            self.conn.execute("INSERT OR IGNORE INTO market_event_versions (event_id, observed_at, state, actual, forecast, previous_value, revision, unit, period_label, source_summary, payload_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (event["id"], event["fetched_at"], event["state"], event.get("actual"), event.get("forecast"), event.get("previous_value"), event.get("revision"), event.get("unit"), event.get("period_label"), event.get("source_summary") or "", event["payload_hash"]))
            self.conn.commit()
            result = self.conn.execute("SELECT * FROM market_events WHERE id = ?", (event["id"],)).fetchone()
            return dict(result) if result else {}

    def prune_unmatched_scheduled_market_events(self, provider: str, event_keys: list[str], start_ts: int, end_ts: int) -> int:
        if not event_keys or end_ts <= start_ts:
            return 0
        placeholders = ", ".join("?" for _ in event_keys)
        params = [provider, start_ts, end_ts, *event_keys]
        with self._lock:
            rows = self.conn.execute(
                f"SELECT id FROM market_events WHERE provider = ? AND state = 'scheduled' AND scheduled_at >= ? AND scheduled_at <= ? AND provider_event_key NOT IN ({placeholders})",
                tuple(params),
            ).fetchall()
            event_ids = [str(row["id"]) for row in rows]
            if not event_ids:
                return 0
            id_placeholders = ", ".join("?" for _ in event_ids)
            self.conn.execute(f"DELETE FROM market_event_versions WHERE event_id IN ({id_placeholders})", tuple(event_ids))
            self.conn.execute(f"DELETE FROM market_events WHERE id IN ({id_placeholders})", tuple(event_ids))
            self.conn.commit()
            return len(event_ids)

    def list_market_events(self, start_ts: int, end_ts: int, categories: list[str], states: list[str]) -> list[dict[str, Any]]:
        clauses, params = ["scheduled_at >= ?", "scheduled_at < ?"], [start_ts, end_ts]
        if categories:
            clauses.append(f"category IN ({', '.join('?' for _ in categories)})"); params.extend(categories)
        if states:
            clauses.append(f"state IN ({', '.join('?' for _ in states)})"); params.extend(states)
        with self._lock:
            return [dict(row) for row in self.conn.execute(f"SELECT * FROM market_events WHERE {' AND '.join(clauses)} ORDER BY scheduled_at ASC, title ASC", tuple(params)).fetchall()]

    def count_market_events(self, provider: str = "") -> int:
        with self._lock:
            if provider:
                row = self.conn.execute("SELECT COUNT(*) AS count FROM market_events WHERE provider = ?", (provider,)).fetchone()
            else:
                row = self.conn.execute("SELECT COUNT(*) AS count FROM market_events").fetchone()
            return int(row["count"] if row else 0)

    def get_market_event(self, event_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute("SELECT * FROM market_events WHERE id = ?", (event_id,)).fetchone()
            return dict(row) if row else None

    def list_market_event_versions(self, event_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(row) for row in self.conn.execute("SELECT * FROM market_event_versions WHERE event_id = ? ORDER BY observed_at ASC, id ASC", (event_id,)).fetchall()]

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        if column not in {str(row["name"]) for row in rows}:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def upsert_instruments(self, instruments: list[dict[str, Any]], updated_at: int) -> None:
        rows = instrument_rows(instruments, updated_at)
        with self._lock:
            self.conn.executemany(
                """
                INSERT INTO instruments (
                    inst_id, inst_type, uly, inst_family, base_ccy, quote_ccy,
                    settle_ccy, ct_val, tick_sz, lot_sz, state, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(inst_id) DO UPDATE SET
                    inst_type=excluded.inst_type,
                    uly=excluded.uly,
                    inst_family=excluded.inst_family,
                    base_ccy=excluded.base_ccy,
                    quote_ccy=excluded.quote_ccy,
                    settle_ccy=excluded.settle_ccy,
                    ct_val=excluded.ct_val,
                    tick_sz=excluded.tick_sz,
                    lot_sz=excluded.lot_sz,
                    state=excluded.state,
                    updated_at=excluded.updated_at
                """,
                rows,
            )
            self.conn.commit()

    def list_instruments(self, query: str = "", limit: int = 200) -> list[dict[str, Any]]:
        pattern = f"%{query.upper()}%"
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT i.*, w.inst_id IS NOT NULL AS watched
                FROM instruments i
                LEFT JOIN watchlist w ON w.inst_id = i.inst_id
                WHERE (? = '' OR i.inst_id LIKE ? OR COALESCE(i.inst_family, '') LIKE ?)
                ORDER BY watched DESC, i.inst_id ASC
                LIMIT ?
                """,
                (query, pattern, pattern, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def set_watched(self, inst_id: str, watched: bool, ts: int) -> None:
        with self._lock:
            if watched:
                self.conn.execute(
                    "INSERT OR IGNORE INTO watchlist (inst_id, created_at) VALUES (?, ?)",
                    (inst_id, ts),
                )
            else:
                self.conn.execute("DELETE FROM watchlist WHERE inst_id = ?", (inst_id,))
            self.conn.commit()

    def watchlist(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT i.*, w.created_at, 1 AS watched
                FROM watchlist w
                LEFT JOIN instruments i ON i.inst_id = w.inst_id
                ORDER BY w.created_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def upsert_candles(self, inst_id: str, bar: str, candles: list[dict[str, str]]) -> None:
        rows = candle_rows(inst_id, bar, candles)
        with self._lock:
            self.conn.executemany(
                """
                INSERT INTO candles (
                    inst_id, bar, ts, open, high, low, close, volume,
                    volume_ccy, volume_quote, confirm
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(inst_id, bar, ts) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    volume_ccy=excluded.volume_ccy,
                    volume_quote=excluded.volume_quote,
                    confirm=excluded.confirm
                """,
                rows,
            )
            self.conn.commit()

    def latest_candles(self, inst_id: str, bar: str, limit: int = 300) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT ts, open, high, low, close, volume, volume_ccy, volume_quote, confirm
                FROM candles
                WHERE inst_id = ? AND bar = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (inst_id, bar, limit),
            ).fetchall()
            return [dict(row) for row in reversed(rows)]

    def insert_ai_outlook_sample(self, sample: dict[str, Any]) -> bool:
        columns = ", ".join(AI_OUTLOOK_SAMPLE_COLUMNS)
        markers = ", ".join("?" for _ in AI_OUTLOOK_SAMPLE_COLUMNS)
        with self._lock:
            cursor = self.conn.execute(
                f"INSERT INTO ai_outlook_samples ({columns}) VALUES ({markers}) ON CONFLICT(sample_id) DO NOTHING",
                ai_outlook_sample_row(sample),
            )
            self.conn.commit()
            return cursor.rowcount == 1

    def due_ai_outlook_samples(self, current_ms: int, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM ai_outlook_samples WHERE status = 'pending' AND due_at <= ? ORDER BY due_at ASC LIMIT ?",
                (current_ms, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def settle_ai_outlook_sample(self, sample_id: str, settlement: dict[str, Any]) -> bool:
        with self._lock:
            cursor = self.conn.execute(
                """UPDATE ai_outlook_samples SET status = ?, observed_ts = ?, observed_close = ?, observed_source = ?,
                   evaluated_at = ?, move_pct = ?, evaluation_json = ? WHERE sample_id = ? AND status = 'pending'""",
                (settlement["status"], settlement.get("observed_ts"), settlement.get("observed_close"),
                 settlement.get("observed_source"), settlement["evaluated_at"], settlement.get("move_pct"),
                 settlement.get("evaluation_json"), sample_id),
            )
            self.conn.commit()
            return cursor.rowcount == 1

    def list_ai_outlook_samples(self, inst_id: str, prompt_version: str = "", limit: int = 50, verified_only: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT * FROM ai_outlook_samples WHERE inst_id = ? AND (? = '' OR prompt_version = ?)
                   AND (? = 0 OR status IN ('hit', 'miss', 'flat')) ORDER BY created_at DESC LIMIT ?""",
                (inst_id, prompt_version, prompt_version, int(verified_only), limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def page_ai_outlook_samples(self, inst_id: str = "", status: str = "", kind: str = "", limit: int = 20, offset: int = 0, priced_only: bool = False) -> tuple[list[dict[str, Any]], int]:
        where = "WHERE (? = '' OR inst_id = ?) AND (? = '' OR status = ?) AND (? = '' OR kind = ?) AND (? = 0 OR (kind = 'price_plan_15m' AND direction IN ('long', 'short') AND COALESCE(json_extract(prediction_json, '$.entryPrice'), '') <> ''))"
        params = (inst_id, inst_id, status, status, kind, kind, int(priced_only))
        with self._lock:
            total = int(self.conn.execute(f"SELECT COUNT(*) FROM ai_outlook_samples {where}", params).fetchone()[0])
            rows = self.conn.execute(
                f"SELECT * FROM ai_outlook_samples {where} ORDER BY created_at DESC, sample_id ASC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
            return [dict(row) for row in rows], total

    def ai_outlook_sample_counts(self, inst_id: str, prompt_version: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT kind, status, COUNT(*) AS total FROM ai_outlook_samples WHERE inst_id = ? AND prompt_version = ? GROUP BY kind, status",
                (inst_id, prompt_version),
            ).fetchall()
            return [dict(row) for row in rows]

    def insert_account_snapshot(self, environment: str, ts: int, payload: dict[str, Any], details_json: str) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO account_snapshots (
                    environment, ts, total_eq, adj_eq, imr, mmr, iso_eq, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                account_snapshot_row(environment, ts, payload, details_json),
            )
            self.conn.commit()

    def insert_position_snapshots(
        self, environment: str, ts: int, positions: list[dict[str, Any]], raw_json: str
    ) -> None:
        rows = position_snapshot_rows(environment, ts, positions, raw_json)
        with self._lock:
            self.conn.executemany(
                """
                INSERT INTO position_snapshots (
                    environment, ts, inst_id, pos_side, pos, avg_px, mark_px, upl,
                    upl_ratio, margin, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            self.conn.commit()

    def latest_account_snapshot(self, environment: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT ts, details_json
                FROM account_snapshots
                WHERE environment = ?
                ORDER BY ts DESC, id DESC
                LIMIT 1
                """
                ,
                (environment,),
            ).fetchone()
            return dict(row) if row else None

    def latest_position_snapshot_payload(self, environment: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT ts, raw_json
                FROM position_snapshots
                WHERE environment = ?
                ORDER BY ts DESC, id DESC
                LIMIT 1
                """
                ,
                (environment,),
            ).fetchone()
            return dict(row) if row else None

    def position_snapshot_rows_between(self, environment: str, from_ts: int, to_ts: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT ts, inst_id, pos_side, pos, avg_px, mark_px, upl, upl_ratio, margin
                FROM position_snapshots
                WHERE environment = ? AND ts >= ? AND ts <= ?
                ORDER BY ts DESC, id DESC
                """,
                (environment, from_ts, to_ts),
            ).fetchall()
            return [dict(row) for row in rows]

    def insert_sim_order_event(self, event: dict[str, Any]) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO sim_order_events (
                    environment, ts, action, inst_id, td_mode, side, pos_side, ord_type,
                    px, sz, reduce_only, cl_ord_id, ord_id, state, code,
                    message, request_json, response_json, pnl_usd, pnl_pct, pnl_basis, origin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                sim_order_event_row(event),
            )
            self.conn.commit()

    def list_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        limit: int = 100,
        offset: int = 0,
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> list[dict[str, Any]]:
        keyword_like = f"%{keyword.upper()}%"
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT *
                FROM sim_order_events
                WHERE environment = ? AND (? = '' OR inst_id = ?)
                  AND (? = '' OR action = ?)
                  AND (? = '' OR state = ?)
                  AND (? = '' OR origin = ?)
                  AND (
                    ? = ''
                    OR UPPER(inst_id) LIKE ?
                    OR UPPER(COALESCE(cl_ord_id, '')) LIKE ?
                    OR UPPER(COALESCE(ord_id, '')) LIKE ?
                    OR UPPER(COALESCE(code, '')) LIKE ?
                    OR UPPER(COALESCE(message, '')) LIKE ?
                  )
                ORDER BY ts DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (
                    environment,
                    inst_id.upper(),
                    inst_id.upper(),
                    action,
                    action,
                    state,
                    state,
                    origin,
                    origin,
                    keyword,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    limit,
                    offset,
                ),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> int:
        keyword_like = f"%{keyword.upper()}%"
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM sim_order_events
                WHERE environment = ? AND (? = '' OR inst_id = ?)
                  AND (? = '' OR action = ?)
                  AND (? = '' OR state = ?)
                  AND (? = '' OR origin = ?)
                  AND (
                    ? = ''
                    OR UPPER(inst_id) LIKE ?
                    OR UPPER(COALESCE(cl_ord_id, '')) LIKE ?
                    OR UPPER(COALESCE(ord_id, '')) LIKE ?
                    OR UPPER(COALESCE(code, '')) LIKE ?
                    OR UPPER(COALESCE(message, '')) LIKE ?
                  )
                """,
                (
                    environment,
                    inst_id.upper(),
                    inst_id.upper(),
                    action,
                    action,
                    state,
                    state,
                    origin,
                    origin,
                    keyword,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                ),
            ).fetchone()
            return int(row["total"]) if row else 0

    def sim_order_event_origin_counts(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
    ) -> dict[str, int]:
        keyword_like = f"%{keyword.upper()}%"
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT COALESCE(NULLIF(origin, ''), 'manual') AS origin, COUNT(*) AS total
                FROM sim_order_events
                WHERE environment = ? AND (? = '' OR inst_id = ?)
                  AND (? = '' OR action = ?)
                  AND (? = '' OR state = ?)
                  AND (
                    ? = ''
                    OR UPPER(inst_id) LIKE ?
                    OR UPPER(COALESCE(cl_ord_id, '')) LIKE ?
                    OR UPPER(COALESCE(ord_id, '')) LIKE ?
                    OR UPPER(COALESCE(code, '')) LIKE ?
                    OR UPPER(COALESCE(message, '')) LIKE ?
                  )
                GROUP BY COALESCE(NULLIF(origin, ''), 'manual')
                """,
                (
                    environment,
                    inst_id.upper(),
                    inst_id.upper(),
                    action,
                    action,
                    state,
                    state,
                    keyword,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                    keyword_like,
                ),
            ).fetchall()
            return {str(row["origin"]): int(row["total"]) for row in rows}

    def mark_sim_order_event_origin(self, cl_ord_ids: list[str], origin: str) -> int:
        ids = [str(item).strip() for item in cl_ord_ids or [] if str(item or "").strip()]
        if not ids or not origin:
            return 0
        updated = 0
        with self._lock:
            for start in range(0, len(ids), 200):
                chunk = ids[start : start + 200]
                placeholders = ",".join("?" for _ in chunk)
                cursor = self.conn.execute(
                    f"""
                    UPDATE sim_order_events
                    SET origin = ?
                    WHERE cl_ord_id IN ({placeholders}) AND COALESCE(origin, '') != ?
                    """,
                    (origin, *chunk, origin),
                )
                updated += int(cursor.rowcount or 0)
            self.conn.commit()
        return updated

    def sim_order_event_origin_for(self, environment: str, cl_ord_id: str) -> str:
        target = str(cl_ord_id or "").strip()
        if not target:
            return ""
        with self._lock:
            row = self.conn.execute(
                """
                SELECT origin
                FROM sim_order_events
                WHERE environment = ? AND cl_ord_id = ? AND COALESCE(origin, '') != ''
                ORDER BY ts DESC, id DESC
                LIMIT 1
                """,
                (environment, target),
            ).fetchone()
            return str(row["origin"]) if row else ""

    def create_automation_strategy(self, strategy: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO automation_strategies (
                    name, enabled, archived, archived_at, archived_reason, inst_id, inst_ids, daily_position_pct, bar, template, execution_mode, td_mode,
                    ord_type, sz, fast_window, slow_window, max_order_contracts,
                    max_position_contracts, cooldown_seconds, take_profit_pct, stop_loss_pct,
                    last_eval_ts, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                automation_strategy_row(strategy),
            )
            self.conn.commit()
            return self.get_automation_strategy(int(cursor.lastrowid)) or {}

    def update_automation_strategy(self, strategy_id: int, strategy: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            self.conn.execute(
                """
                UPDATE automation_strategies
                SET name = ?, enabled = ?, archived = ?, archived_at = ?, archived_reason = ?, inst_id = ?, inst_ids = ?, daily_position_pct = ?, bar = ?, template = ?, execution_mode = ?,
                    td_mode = ?, ord_type = ?, sz = ?, fast_window = ?, slow_window = ?,
                    max_order_contracts = ?, max_position_contracts = ?, cooldown_seconds = ?,
                    take_profit_pct = ?, stop_loss_pct = ?, last_eval_ts = ?, updated_at = ?
                WHERE id = ?
                """,
                automation_strategy_update_row(strategy, strategy_id),
            )
            self.conn.commit()
            return self.get_automation_strategy(strategy_id)

    def list_automation_strategies(self, include_archived: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            if include_archived:
                rows = self.conn.execute(
                    """
                    SELECT *
                    FROM automation_strategies
                    ORDER BY enabled DESC, archived ASC, updated_at DESC, id DESC
                    """
                ).fetchall()
            else:
                rows = self.conn.execute(
                    """
                    SELECT *
                    FROM automation_strategies
                    WHERE COALESCE(archived, 0) = 0
                    ORDER BY enabled DESC, updated_at DESC, id DESC
                    """
                ).fetchall()
            return [dict(row) for row in rows]

    def get_automation_strategy(self, strategy_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM automation_strategies WHERE id = ?",
                (strategy_id,),
            ).fetchone()
            return dict(row) if row else None

    def set_automation_strategy_last_eval(self, strategy_id: int, last_eval_ts: int, updated_at: int) -> None:
        with self._lock:
            self.conn.execute(
                "UPDATE automation_strategies SET last_eval_ts = ?, updated_at = ? WHERE id = ?",
                (last_eval_ts, updated_at, strategy_id),
            )
            self.conn.commit()

    def insert_automation_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO automation_signals (
                    strategy_id, ts, environment, inst_id, bar, template, action,
                    side, pos_side, price, sz, decision, reason, message, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                automation_signal_row(signal),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM automation_signals WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            return dict(row) if row else {}

    def get_automation_signal(self, signal_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT s.*, a.name AS strategy_name
                FROM automation_signals s
                LEFT JOIN automation_strategies a ON a.id = s.strategy_id
                WHERE s.id = ?
                """,
                (signal_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_automation_signals(self, strategy_id: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT s.*, a.name AS strategy_name
                FROM automation_signals s
                LEFT JOIN automation_strategies a ON a.id = s.strategy_id
                WHERE (? = 0 OR s.strategy_id = ?)
                ORDER BY s.ts DESC, s.id DESC
                LIMIT ?
                """,
                (strategy_id, strategy_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_automation_signals_since(self, strategy_id: int, since_ts: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT s.*
                FROM automation_signals s
                WHERE s.strategy_id = ? AND s.ts >= ?
                ORDER BY s.ts DESC, s.id DESC
                """,
                (strategy_id, since_ts),
            ).fetchall()
            return [dict(row) for row in rows]

    def latest_actionable_automation_signal(self, strategy_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT *
                FROM automation_signals
                WHERE strategy_id = ? AND action IN ('long', 'short')
                ORDER BY ts DESC, id DESC
                LIMIT 1
                """,
                (strategy_id,),
            ).fetchone()
            return dict(row) if row else None

    def insert_automation_risk_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO automation_risk_snapshots (
                    signal_id, strategy_id, ts, allowed, severity, message, checks_json, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot["signal_id"],
                    snapshot["strategy_id"],
                    snapshot["ts"],
                    bool(snapshot.get("allowed")),
                    snapshot["severity"],
                    snapshot["message"],
                    snapshot["checks_json"],
                    snapshot["raw_json"],
                ),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM automation_risk_snapshots WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            return dict(row) if row else {}

    def get_automation_risk_snapshot(self, signal_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT *
                FROM automation_risk_snapshots
                WHERE signal_id = ?
                ORDER BY ts DESC, id DESC
                LIMIT 1
                """,
                (signal_id,),
            ).fetchone()
            return dict(row) if row else None

    def insert_automation_execution_step(self, step: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO automation_execution_steps (
                    signal_id, strategy_id, step_order, ts, action, status, message, request_json, response_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step["signal_id"],
                    step["strategy_id"],
                    step["step_order"],
                    step["ts"],
                    step["action"],
                    step["status"],
                    step["message"],
                    step["request_json"],
                    step["response_json"],
                ),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM automation_execution_steps WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            return dict(row) if row else {}

    def list_automation_execution_steps(self, signal_id: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT *
                FROM automation_execution_steps
                WHERE signal_id = ?
                ORDER BY step_order ASC, id ASC
                """,
                (signal_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def upsert_algo_order(self, order: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO automation_algo_orders (
                    algo_cl_ord_id, strategy_id, inst_id, pos_side, td_mode, sz,
                    main_ord_id, avg_px, state, detail, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(algo_cl_ord_id) DO UPDATE SET
                    state=excluded.state,
                    main_ord_id=excluded.main_ord_id,
                    avg_px=excluded.avg_px,
                    detail=excluded.detail,
                    updated_at=excluded.updated_at
                """,
                _algo_order_row(order),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM automation_algo_orders WHERE algo_cl_ord_id = ?",
                (str(order.get("algo_cl_ord_id") or ""),),
            ).fetchone()
            return dict(row) if row else {}

    def get_algo_order_by_cl_id(self, algo_cl_ord_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM automation_algo_orders WHERE algo_cl_ord_id = ?",
                (algo_cl_ord_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_algo_orders(self, strategy_id: int = 0, states: list[str] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            clauses = ["(? = 0 OR strategy_id = ?)"]
            params: list[Any] = [strategy_id, strategy_id]
            if states:
                placeholders = ",".join("?" for _ in states)
                clauses.append(f"state IN ({placeholders})")
                params.extend(states)
            rows = self.conn.execute(
                f"SELECT * FROM automation_algo_orders WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC",
                tuple(params),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_algo_order(self, algo_cl_ord_id: str) -> None:
        with self._lock:
            self.conn.execute(
                "DELETE FROM automation_algo_orders WHERE algo_cl_ord_id = ?",
                (algo_cl_ord_id,),
            )
            self.conn.commit()

    def insert_automation_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO automation_alerts (
                    ts, severity, source, message, strategy_id, signal_id, order_event_id, acknowledged_at, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["ts"],
                    alert["severity"],
                    alert["source"],
                    alert["message"],
                    alert.get("strategy_id"),
                    alert.get("signal_id"),
                    alert.get("order_event_id"),
                    alert.get("acknowledged_at"),
                    alert["raw_json"],
                ),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM automation_alerts WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            return dict(row) if row else {}

    def list_automation_alerts(
        self,
        active_only: bool = False,
        severity: str = "",
        source: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT *
                FROM automation_alerts
                WHERE (? = 0 OR acknowledged_at IS NULL)
                  AND (? = '' OR severity = ?)
                  AND (? = '' OR source = ?)
                ORDER BY ts DESC, id DESC
                LIMIT ?
                """,
                (int(active_only), severity, severity, source, source, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_automation_alerts(self, active_only: bool = False, severity: str = "", source: str = "") -> int:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM automation_alerts
                WHERE (? = 0 OR acknowledged_at IS NULL)
                  AND (? = '' OR severity = ?)
                  AND (? = '' OR source = ?)
                """,
                (int(active_only), severity, severity, source, source),
            ).fetchone()
            return int(row["total"]) if row else 0

    def acknowledge_automation_alert(self, alert_id: int, acknowledged_at: int) -> None:
        with self._lock:
            self.conn.execute(
                "UPDATE automation_alerts SET acknowledged_at = ? WHERE id = ?",
                (acknowledged_at, alert_id),
            )
            self.conn.commit()

    def insert_llm_usage_log(self, log: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO llm_usage_logs (
                    request_id, ts, provider, model, mode, request_type, status,
                    strategy_id, signal_id, inst_id, bar, profile_id, profile_version, profile_hash, prompt_tokens, completion_tokens,
                    total_tokens, cached_tokens, reasoning_tokens, cache_hit_tokens,
                    cache_miss_tokens, duration_ms, timeout_seconds, finish_reason,
                    error, raw_usage_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                llm_usage_log_row(log),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM llm_usage_logs WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            return dict(row) if row else {}

    def list_llm_usage_logs(
        self, limit: int = 100, offset: int = 0, request_type: str = "", status: str = "", strategy_id: int = 0
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT *
                FROM llm_usage_logs
                WHERE (? = '' OR request_type = ?)
                  AND (? = '' OR status = ?)
                  AND (? = 0 OR strategy_id = ?)
                ORDER BY ts DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (request_type, request_type, status, status, strategy_id, strategy_id, limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_llm_usage_logs(self, request_type: str = "", status: str = "", strategy_id: int = 0) -> int:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM llm_usage_logs
                WHERE (? = '' OR request_type = ?)
                  AND (? = '' OR status = ?)
                  AND (? = 0 OR strategy_id = ?)
                """,
                (request_type, request_type, status, status, strategy_id, strategy_id),
            ).fetchone()
            return int(row["total"]) if row else 0

    def llm_usage_summary(self, since_ts: int = 0) -> dict[str, Any]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT
                    COUNT(*) AS calls,
                    COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                    COALESCE(SUM(total_tokens), 0) AS total_tokens,
                    COALESCE(SUM(cached_tokens), 0) AS cached_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) AS reasoning_tokens,
                    COALESCE(SUM(cache_hit_tokens), 0) AS cache_hit_tokens,
                    COALESCE(SUM(cache_miss_tokens), 0) AS cache_miss_tokens,
                    COALESCE(SUM(CASE WHEN status <> 'success' THEN 1 ELSE 0 END), 0) AS failed_calls,
                    COALESCE(ROUND(AVG(duration_ms)), 0) AS avg_duration_ms
                FROM llm_usage_logs
                WHERE (? = 0 OR ts >= ?)
                """,
                (since_ts, since_ts),
            ).fetchone()
            return dict(row) if row else {}

    def get_app_setting(self, key: str) -> str | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (key,),
            ).fetchone()
            return str(row["value"]) if row else None

    def set_app_setting(self, key: str, value: str, ts: int) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    updated_at=excluded.updated_at
                """,
                (key, value, ts),
            )
            self.conn.commit()


class PostgresDatabase:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Any | None = None
        self._lock = RLock()

    def init(self) -> None:
        with self._lock:
            conn = self._connection_with_retries()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS instruments (
                        inst_id TEXT PRIMARY KEY,
                        inst_type TEXT NOT NULL,
                        uly TEXT,
                        inst_family TEXT,
                        base_ccy TEXT,
                        quote_ccy TEXT,
                        settle_ccy TEXT,
                        ct_val TEXT,
                        tick_sz TEXT,
                        lot_sz TEXT,
                        state TEXT,
                        updated_at BIGINT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS watchlist (
                        inst_id TEXT PRIMARY KEY,
                        created_at BIGINT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS candles (
                        inst_id TEXT NOT NULL,
                        bar TEXT NOT NULL,
                        ts BIGINT NOT NULL,
                        open TEXT NOT NULL,
                        high TEXT NOT NULL,
                        low TEXT NOT NULL,
                        close TEXT NOT NULL,
                        volume TEXT NOT NULL,
                        volume_ccy TEXT,
                        volume_quote TEXT,
                        confirm TEXT,
                        PRIMARY KEY (inst_id, bar, ts)
                    );

                    CREATE TABLE IF NOT EXISTS account_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        environment TEXT NOT NULL DEFAULT 'live',
                        ts BIGINT NOT NULL,
                        total_eq TEXT,
                        adj_eq TEXT,
                        imr TEXT,
                        mmr TEXT,
                        iso_eq TEXT,
                        details_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS position_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        environment TEXT NOT NULL DEFAULT 'live',
                        ts BIGINT NOT NULL,
                        inst_id TEXT NOT NULL,
                        pos_side TEXT,
                        pos TEXT,
                        avg_px TEXT,
                        mark_px TEXT,
                        upl TEXT,
                        upl_ratio TEXT,
                        margin TEXT,
                        raw_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS sim_order_events (
                        id BIGSERIAL PRIMARY KEY,
                        environment TEXT NOT NULL DEFAULT 'simulated',
                        ts BIGINT NOT NULL,
                        action TEXT NOT NULL,
                        inst_id TEXT NOT NULL,
                        td_mode TEXT,
                        side TEXT,
                        pos_side TEXT,
                        ord_type TEXT,
                        px TEXT,
                        sz TEXT,
                        reduce_only BOOLEAN NOT NULL DEFAULT FALSE,
                        cl_ord_id TEXT,
                        ord_id TEXT,
                        state TEXT,
                        code TEXT,
                        message TEXT,
                        request_json TEXT NOT NULL,
                        response_json TEXT NOT NULL,
                        pnl_usd TEXT,
                        pnl_pct TEXT,
                        pnl_basis TEXT,
                        origin TEXT NOT NULL DEFAULT 'manual'
                    );

                    CREATE TABLE IF NOT EXISTS automation_strategies (
                        id BIGSERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        enabled BOOLEAN NOT NULL DEFAULT FALSE,
                        archived BOOLEAN NOT NULL DEFAULT FALSE,
                        archived_at BIGINT,
                        archived_reason TEXT NOT NULL DEFAULT '',
                        inst_id TEXT NOT NULL,
                        inst_ids TEXT NOT NULL DEFAULT '[]',
                        daily_position_pct TEXT NOT NULL DEFAULT '0',
                        bar TEXT NOT NULL,
                        template TEXT NOT NULL,
                        execution_mode TEXT NOT NULL,
                        td_mode TEXT NOT NULL,
                        ord_type TEXT NOT NULL,
                        sz TEXT NOT NULL,
                        fast_window INTEGER NOT NULL,
                        slow_window INTEGER NOT NULL,
                        max_order_contracts TEXT NOT NULL,
                        max_position_contracts TEXT NOT NULL,
                        cooldown_seconds INTEGER NOT NULL,
                        take_profit_pct TEXT NOT NULL DEFAULT '0',
                        stop_loss_pct TEXT NOT NULL DEFAULT '0',
                        last_eval_ts BIGINT,
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS automation_signals (
                        id BIGSERIAL PRIMARY KEY,
                        strategy_id BIGINT NOT NULL,
                        ts BIGINT NOT NULL,
                        environment TEXT NOT NULL,
                        inst_id TEXT NOT NULL,
                        bar TEXT NOT NULL,
                        template TEXT NOT NULL,
                        action TEXT NOT NULL,
                        side TEXT,
                        pos_side TEXT,
                        price TEXT,
                        sz TEXT,
                        decision TEXT NOT NULL,
                        reason TEXT,
                        message TEXT,
                        raw_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS llm_usage_logs (
                        id BIGSERIAL PRIMARY KEY,
                        request_id TEXT NOT NULL,
                        ts BIGINT NOT NULL,
                        provider TEXT,
                        model TEXT,
                        mode TEXT,
                        request_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        strategy_id BIGINT,
                        signal_id BIGINT,
                        inst_id TEXT,
                        bar TEXT,
                        profile_id TEXT,
                        profile_version INTEGER,
                        profile_hash TEXT,
                        prompt_tokens BIGINT NOT NULL DEFAULT 0,
                        completion_tokens BIGINT NOT NULL DEFAULT 0,
                        total_tokens BIGINT NOT NULL DEFAULT 0,
                        cached_tokens BIGINT NOT NULL DEFAULT 0,
                        reasoning_tokens BIGINT NOT NULL DEFAULT 0,
                        cache_hit_tokens BIGINT NOT NULL DEFAULT 0,
                        cache_miss_tokens BIGINT NOT NULL DEFAULT 0,
                        duration_ms BIGINT NOT NULL DEFAULT 0,
                        timeout_seconds BIGINT NOT NULL DEFAULT 0,
                        finish_reason TEXT,
                        error TEXT,
                        raw_usage_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS automation_risk_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        signal_id BIGINT NOT NULL,
                        strategy_id BIGINT NOT NULL,
                        ts BIGINT NOT NULL,
                        allowed BOOLEAN NOT NULL DEFAULT FALSE,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        checks_json TEXT NOT NULL,
                        raw_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS automation_execution_steps (
                        id BIGSERIAL PRIMARY KEY,
                        signal_id BIGINT NOT NULL,
                        strategy_id BIGINT NOT NULL,
                        step_order INTEGER NOT NULL,
                        ts BIGINT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT NOT NULL,
                        request_json TEXT NOT NULL,
                        response_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS automation_alerts (
                        id BIGSERIAL PRIMARY KEY,
                        ts BIGINT NOT NULL,
                        severity TEXT NOT NULL,
                        source TEXT NOT NULL,
                        message TEXT NOT NULL,
                        strategy_id BIGINT,
                        signal_id BIGINT,
                        order_event_id BIGINT,
                        acknowledged_at BIGINT,
                        raw_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS automation_algo_orders (
                        id BIGSERIAL PRIMARY KEY,
                        algo_cl_ord_id TEXT NOT NULL UNIQUE,
                        strategy_id BIGINT NOT NULL,
                        inst_id TEXT NOT NULL,
                        pos_side TEXT NOT NULL,
                        td_mode TEXT NOT NULL DEFAULT 'cross',
                        sz TEXT NOT NULL DEFAULT '',
                        main_ord_id TEXT NOT NULL DEFAULT '',
                        avg_px TEXT NOT NULL DEFAULT '',
                        state TEXT NOT NULL DEFAULT 'pending',
                        detail TEXT NOT NULL DEFAULT '',
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_algo_orders_strategy
                        ON automation_algo_orders (strategy_id);
                    CREATE INDEX IF NOT EXISTS idx_algo_orders_state
                        ON automation_algo_orders (state);

                    CREATE INDEX IF NOT EXISTS idx_candles_lookup
                        ON candles (inst_id, bar, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_account_snapshots_ts
                        ON account_snapshots (ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_position_snapshots_ts
                        ON position_snapshots (ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_sim_order_events_ts
                        ON sim_order_events (ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_sim_order_events_inst
                        ON sim_order_events (inst_id, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_automation_strategies_enabled
                        ON automation_strategies (enabled, updated_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_automation_signals_strategy_ts
                        ON automation_signals (strategy_id, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_automation_signals_ts
                        ON automation_signals (ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_automation_risk_snapshots_signal
                        ON automation_risk_snapshots (signal_id, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_automation_execution_steps_signal
                        ON automation_execution_steps (signal_id, step_order ASC);
                    CREATE INDEX IF NOT EXISTS idx_automation_alerts_active
                        ON automation_alerts (acknowledged_at, severity, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_automation_alerts_source
                        ON automation_alerts (source, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_llm_usage_logs_ts
                        ON llm_usage_logs (ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_llm_usage_logs_strategy_ts
                        ON llm_usage_logs (strategy_id, ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_llm_usage_logs_request
                        ON llm_usage_logs (request_id);

                    CREATE TABLE IF NOT EXISTS market_events (
                        id TEXT PRIMARY KEY,
                        provider TEXT NOT NULL,
                        provider_event_key TEXT NOT NULL,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        importance TEXT NOT NULL,
                        state TEXT NOT NULL,
                        scheduled_at BIGINT,
                        source_timezone TEXT NOT NULL,
                        published_at BIGINT,
                        fetched_at BIGINT NOT NULL,
                        actual TEXT,
                        forecast TEXT,
                        previous_value TEXT,
                        revision TEXT,
                        unit TEXT,
                        period_label TEXT,
                        source_url TEXT NOT NULL,
                        source_summary TEXT NOT NULL,
                        official BOOLEAN NOT NULL DEFAULT TRUE,
                        payload_hash TEXT NOT NULL,
                        UNIQUE(provider, provider_event_key)
                    );
                    CREATE TABLE IF NOT EXISTS market_event_versions (
                        id BIGSERIAL PRIMARY KEY,
                        event_id TEXT NOT NULL,
                        observed_at BIGINT NOT NULL,
                        state TEXT NOT NULL,
                        actual TEXT,
                        forecast TEXT,
                        previous_value TEXT,
                        revision TEXT,
                        unit TEXT,
                        period_label TEXT,
                        source_summary TEXT NOT NULL,
                        payload_hash TEXT NOT NULL,
                        UNIQUE(event_id, payload_hash)
                    );
                    CREATE INDEX IF NOT EXISTS idx_market_events_schedule ON market_events (scheduled_at ASC);
                    CREATE INDEX IF NOT EXISTS idx_market_events_state ON market_events (state, scheduled_at ASC);
                    CREATE INDEX IF NOT EXISTS idx_market_event_versions_event ON market_event_versions (event_id, observed_at ASC);

                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at BIGINT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS ai_outlook_samples (
                        sample_id TEXT PRIMARY KEY,
                        report_id TEXT NOT NULL,
                        inst_id TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        bar TEXT NOT NULL,
                        created_at BIGINT NOT NULL,
                        due_at BIGINT NOT NULL,
                        target_ts BIGINT NOT NULL,
                        direction TEXT NOT NULL,
                        status TEXT NOT NULL,
                        prompt_version TEXT NOT NULL,
                        criterion_version INTEGER NOT NULL,
                        snapshot_id TEXT NOT NULL,
                        report_source TEXT NOT NULL,
                        baseline_ts BIGINT NOT NULL,
                        baseline_close TEXT NOT NULL,
                        threshold_pct TEXT NOT NULL,
                        prediction_json TEXT NOT NULL,
                        observed_ts BIGINT,
                        observed_close TEXT,
                        observed_source TEXT,
                        evaluated_at BIGINT,
                        move_pct TEXT,
                        evaluation_json TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_ai_outlook_samples_due ON ai_outlook_samples (status, due_at ASC);
                    CREATE INDEX IF NOT EXISTS idx_ai_outlook_samples_inst ON ai_outlook_samples (inst_id, prompt_version, created_at DESC);
                    """
                )
                cur.execute("ALTER TABLE account_snapshots ADD COLUMN IF NOT EXISTS environment TEXT NOT NULL DEFAULT 'live'")
                cur.execute("ALTER TABLE position_snapshots ADD COLUMN IF NOT EXISTS environment TEXT NOT NULL DEFAULT 'live'")
                cur.execute("ALTER TABLE sim_order_events ADD COLUMN IF NOT EXISTS environment TEXT NOT NULL DEFAULT 'simulated'")
                cur.execute("ALTER TABLE sim_order_events ADD COLUMN IF NOT EXISTS pnl_usd TEXT")
                cur.execute("ALTER TABLE sim_order_events ADD COLUMN IF NOT EXISTS pnl_pct TEXT")
                cur.execute("ALTER TABLE sim_order_events ADD COLUMN IF NOT EXISTS pnl_basis TEXT")
                cur.execute("ALTER TABLE sim_order_events ADD COLUMN IF NOT EXISTS origin TEXT NOT NULL DEFAULT 'manual'")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT FALSE")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS archived_at BIGINT")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS archived_reason TEXT NOT NULL DEFAULT ''")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS take_profit_pct TEXT NOT NULL DEFAULT '0'")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS stop_loss_pct TEXT NOT NULL DEFAULT '0'")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS inst_ids TEXT NOT NULL DEFAULT '[]'")
                cur.execute("ALTER TABLE automation_strategies ADD COLUMN IF NOT EXISTS daily_position_pct TEXT NOT NULL DEFAULT '0'")
                cur.execute("ALTER TABLE llm_usage_logs ADD COLUMN IF NOT EXISTS profile_id TEXT")
                cur.execute("ALTER TABLE llm_usage_logs ADD COLUMN IF NOT EXISTS profile_version INTEGER")
                cur.execute("ALTER TABLE llm_usage_logs ADD COLUMN IF NOT EXISTS profile_hash TEXT")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS automation_risk_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        signal_id BIGINT NOT NULL,
                        strategy_id BIGINT NOT NULL,
                        ts BIGINT NOT NULL,
                        allowed BOOLEAN NOT NULL DEFAULT FALSE,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        checks_json TEXT NOT NULL,
                        raw_json TEXT NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS automation_execution_steps (
                        id BIGSERIAL PRIMARY KEY,
                        signal_id BIGINT NOT NULL,
                        strategy_id BIGINT NOT NULL,
                        step_order INTEGER NOT NULL,
                        ts BIGINT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT NOT NULL,
                        request_json TEXT NOT NULL,
                        response_json TEXT NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS automation_alerts (
                        id BIGSERIAL PRIMARY KEY,
                        ts BIGINT NOT NULL,
                        severity TEXT NOT NULL,
                        source TEXT NOT NULL,
                        message TEXT NOT NULL,
                        strategy_id BIGINT,
                        signal_id BIGINT,
                        order_event_id BIGINT,
                        acknowledged_at BIGINT,
                        raw_json TEXT NOT NULL
                    )
                    """
                )
            conn.commit()

    def _connection_with_retries(self) -> Any:
        last_error: Exception | None = None
        for attempt in range(30):
            try:
                return self._connect()
            except Exception as exc:
                last_error = exc
                if attempt == 29:
                    break
                time.sleep(1)
        raise RuntimeError(f"PostgreSQL connection failed after retries: {last_error}") from last_error

    def _connect(self) -> Any:
        if self.conn is None or self.conn.closed:
            import psycopg
            from psycopg.rows import dict_row

            self.conn = psycopg.connect(self.database_url, row_factory=dict_row)
        return self.conn

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()

    def _executemany(self, sql: str, rows: list[tuple[Any, ...]]) -> None:
        if not rows:
            return
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.executemany(sql, rows)
            conn.commit()

    def upsert_instruments(self, instruments: list[dict[str, Any]], updated_at: int) -> None:
        self._executemany(
            """
            INSERT INTO instruments (
                inst_id, inst_type, uly, inst_family, base_ccy, quote_ccy,
                settle_ccy, ct_val, tick_sz, lot_sz, state, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(inst_id) DO UPDATE SET
                inst_type=excluded.inst_type,
                uly=excluded.uly,
                inst_family=excluded.inst_family,
                base_ccy=excluded.base_ccy,
                quote_ccy=excluded.quote_ccy,
                settle_ccy=excluded.settle_ccy,
                ct_val=excluded.ct_val,
                tick_sz=excluded.tick_sz,
                lot_sz=excluded.lot_sz,
                state=excluded.state,
                updated_at=excluded.updated_at
            """,
            instrument_rows(instruments, updated_at),
        )

    def list_instruments(self, query: str = "", limit: int = 200) -> list[dict[str, Any]]:
        pattern = f"%{query.upper()}%"
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT i.*, (w.inst_id IS NOT NULL) AS watched
                    FROM instruments i
                    LEFT JOIN watchlist w ON w.inst_id = i.inst_id
                    WHERE (%s = '' OR i.inst_id LIKE %s OR COALESCE(i.inst_family, '') LIKE %s)
                    ORDER BY watched DESC, i.inst_id ASC
                    LIMIT %s
                    """,
                    (query, pattern, pattern, limit),
                )
                return list(cur.fetchall())

    def set_watched(self, inst_id: str, watched: bool, ts: int) -> None:
        if watched:
            self._execute(
                "INSERT INTO watchlist (inst_id, created_at) VALUES (%s, %s) ON CONFLICT(inst_id) DO NOTHING",
                (inst_id, ts),
            )
        else:
            self._execute("DELETE FROM watchlist WHERE inst_id = %s", (inst_id,))

    def watchlist(self) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT i.*, w.created_at, TRUE AS watched
                    FROM watchlist w
                    LEFT JOIN instruments i ON i.inst_id = w.inst_id
                    ORDER BY w.created_at DESC
                    """
                )
                return list(cur.fetchall())

    def upsert_candles(self, inst_id: str, bar: str, candles: list[dict[str, str]]) -> None:
        self._executemany(
            """
            INSERT INTO candles (
                inst_id, bar, ts, open, high, low, close, volume,
                volume_ccy, volume_quote, confirm
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(inst_id, bar, ts) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                volume=excluded.volume,
                volume_ccy=excluded.volume_ccy,
                volume_quote=excluded.volume_quote,
                confirm=excluded.confirm
            """,
            candle_rows(inst_id, bar, candles),
        )

    def latest_candles(self, inst_id: str, bar: str, limit: int = 300) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ts, open, high, low, close, volume, volume_ccy, volume_quote, confirm
                    FROM candles
                    WHERE inst_id = %s AND bar = %s
                    ORDER BY ts DESC
                    LIMIT %s
                    """,
                    (inst_id, bar, limit),
                )
                return list(reversed(cur.fetchall()))

    def insert_ai_outlook_sample(self, sample: dict[str, Any]) -> bool:
        columns = ", ".join(AI_OUTLOOK_SAMPLE_COLUMNS)
        markers = ", ".join("%s" for _ in AI_OUTLOOK_SAMPLE_COLUMNS)
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO ai_outlook_samples ({columns}) VALUES ({markers}) ON CONFLICT(sample_id) DO NOTHING",
                    ai_outlook_sample_row(sample),
                )
                inserted = cur.rowcount == 1
            conn.commit()
            return inserted

    def due_ai_outlook_samples(self, current_ms: int, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM ai_outlook_samples WHERE status = 'pending' AND due_at <= %s ORDER BY due_at ASC LIMIT %s",
                    (current_ms, limit),
                )
                return list(cur.fetchall())

    def settle_ai_outlook_sample(self, sample_id: str, settlement: dict[str, Any]) -> bool:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE ai_outlook_samples SET status = %s, observed_ts = %s, observed_close = %s, observed_source = %s,
                       evaluated_at = %s, move_pct = %s, evaluation_json = %s WHERE sample_id = %s AND status = 'pending'""",
                    (settlement["status"], settlement.get("observed_ts"), settlement.get("observed_close"),
                     settlement.get("observed_source"), settlement["evaluated_at"], settlement.get("move_pct"),
                     settlement.get("evaluation_json"), sample_id),
                )
                settled = cur.rowcount == 1
            conn.commit()
            return settled

    def list_ai_outlook_samples(self, inst_id: str, prompt_version: str = "", limit: int = 50, verified_only: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT * FROM ai_outlook_samples WHERE inst_id = %s AND (%s = '' OR prompt_version = %s)
                       AND (%s = FALSE OR status IN ('hit', 'miss', 'flat')) ORDER BY created_at DESC LIMIT %s""",
                    (inst_id, prompt_version, prompt_version, verified_only, limit),
                )
                return list(cur.fetchall())

    def page_ai_outlook_samples(self, inst_id: str = "", status: str = "", kind: str = "", limit: int = 20, offset: int = 0, priced_only: bool = False) -> tuple[list[dict[str, Any]], int]:
        where = "WHERE (%s = '' OR inst_id = %s) AND (%s = '' OR status = %s) AND (%s = '' OR kind = %s) AND (%s = FALSE OR (kind = 'price_plan_15m' AND direction IN ('long', 'short') AND COALESCE(prediction_json::jsonb ->> 'entryPrice', '') <> ''))"
        params = (inst_id, inst_id, status, status, kind, kind, priced_only)
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) AS total FROM ai_outlook_samples {where}", params)
                total = int(cur.fetchone()["total"])
                cur.execute(
                    f"SELECT * FROM ai_outlook_samples {where} ORDER BY created_at DESC, sample_id ASC LIMIT %s OFFSET %s",
                    (*params, limit, offset),
                )
                return list(cur.fetchall()), total

    def ai_outlook_sample_counts(self, inst_id: str, prompt_version: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT kind, status, COUNT(*) AS total FROM ai_outlook_samples WHERE inst_id = %s AND prompt_version = %s GROUP BY kind, status",
                    (inst_id, prompt_version),
                )
                return list(cur.fetchall())

    def insert_account_snapshot(self, environment: str, ts: int, payload: dict[str, Any], details_json: str) -> None:
        self._execute(
            """
            INSERT INTO account_snapshots (
                environment, ts, total_eq, adj_eq, imr, mmr, iso_eq, details_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            account_snapshot_row(environment, ts, payload, details_json),
        )

    def insert_position_snapshots(
        self, environment: str, ts: int, positions: list[dict[str, Any]], raw_json: str
    ) -> None:
        self._executemany(
            """
            INSERT INTO position_snapshots (
                environment, ts, inst_id, pos_side, pos, avg_px, mark_px, upl,
                upl_ratio, margin, raw_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            position_snapshot_rows(environment, ts, positions, raw_json),
        )

    def latest_account_snapshot(self, environment: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ts, details_json
                    FROM account_snapshots
                    WHERE environment = %s
                    ORDER BY ts DESC, id DESC
                    LIMIT 1
                    """
                    ,
                    (environment,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def latest_position_snapshot_payload(self, environment: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ts, raw_json
                    FROM position_snapshots
                    WHERE environment = %s
                    ORDER BY ts DESC, id DESC
                    LIMIT 1
                    """
                    ,
                    (environment,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def position_snapshot_rows_between(self, environment: str, from_ts: int, to_ts: int) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ts, inst_id, pos_side, pos, avg_px, mark_px, upl, upl_ratio, margin
                    FROM position_snapshots
                    WHERE environment = %s AND ts >= %s AND ts <= %s
                    ORDER BY ts DESC, id DESC
                    """,
                    (environment, from_ts, to_ts),
                )
                return list(cur.fetchall())

    def insert_sim_order_event(self, event: dict[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO sim_order_events (
                environment, ts, action, inst_id, td_mode, side, pos_side, ord_type,
                px, sz, reduce_only, cl_ord_id, ord_id, state, code,
                message, request_json, response_json, pnl_usd, pnl_pct, pnl_basis, origin
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            sim_order_event_row(event),
        )

    def list_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        limit: int = 100,
        offset: int = 0,
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> list[dict[str, Any]]:
        keyword_like = f"%{keyword.upper()}%"
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM sim_order_events
                    WHERE environment = %s AND (%s = '' OR inst_id = %s)
                      AND (%s = '' OR action = %s)
                      AND (%s = '' OR state = %s)
                      AND (%s = '' OR origin = %s)
                      AND (
                        %s = ''
                        OR UPPER(inst_id) LIKE %s
                        OR UPPER(COALESCE(cl_ord_id, '')) LIKE %s
                        OR UPPER(COALESCE(ord_id, '')) LIKE %s
                        OR UPPER(COALESCE(code, '')) LIKE %s
                        OR UPPER(COALESCE(message, '')) LIKE %s
                      )
                    ORDER BY ts DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (
                        environment,
                        inst_id.upper(),
                        inst_id.upper(),
                        action,
                        action,
                        state,
                        state,
                        origin,
                        origin,
                        keyword,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        limit,
                        offset,
                    ),
                )
                return list(cur.fetchall())

    def count_sim_order_events(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
        origin: str = "",
    ) -> int:
        keyword_like = f"%{keyword.upper()}%"
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM sim_order_events
                    WHERE environment = %s AND (%s = '' OR inst_id = %s)
                      AND (%s = '' OR action = %s)
                      AND (%s = '' OR state = %s)
                      AND (%s = '' OR origin = %s)
                      AND (
                        %s = ''
                        OR UPPER(inst_id) LIKE %s
                        OR UPPER(COALESCE(cl_ord_id, '')) LIKE %s
                        OR UPPER(COALESCE(ord_id, '')) LIKE %s
                        OR UPPER(COALESCE(code, '')) LIKE %s
                        OR UPPER(COALESCE(message, '')) LIKE %s
                      )
                    """,
                    (
                        environment,
                        inst_id.upper(),
                        inst_id.upper(),
                        action,
                        action,
                        state,
                        state,
                        origin,
                        origin,
                        keyword,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                    ),
                )
                row = cur.fetchone()
                return int(row["total"]) if row else 0

    def sim_order_event_origin_counts(
        self,
        environment: str,
        inst_id: str = "",
        keyword: str = "",
        action: str = "",
        state: str = "",
    ) -> dict[str, int]:
        keyword_like = f"%{keyword.upper()}%"
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(NULLIF(origin, ''), 'manual') AS origin, COUNT(*) AS total
                    FROM sim_order_events
                    WHERE environment = %s AND (%s = '' OR inst_id = %s)
                      AND (%s = '' OR action = %s)
                      AND (%s = '' OR state = %s)
                      AND (
                        %s = ''
                        OR UPPER(inst_id) LIKE %s
                        OR UPPER(COALESCE(cl_ord_id, '')) LIKE %s
                        OR UPPER(COALESCE(ord_id, '')) LIKE %s
                        OR UPPER(COALESCE(code, '')) LIKE %s
                        OR UPPER(COALESCE(message, '')) LIKE %s
                      )
                    GROUP BY COALESCE(NULLIF(origin, ''), 'manual')
                    """,
                    (
                        environment,
                        inst_id.upper(),
                        inst_id.upper(),
                        action,
                        action,
                        state,
                        state,
                        keyword,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                        keyword_like,
                    ),
                )
                return {str(row["origin"]): int(row["total"]) for row in cur.fetchall()}

    def mark_sim_order_event_origin(self, cl_ord_ids: list[str], origin: str) -> int:
        ids = [str(item).strip() for item in cl_ord_ids or [] if str(item or "").strip()]
        if not ids or not origin:
            return 0
        updated = 0
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                for start in range(0, len(ids), 200):
                    chunk = ids[start : start + 200]
                    cur.execute(
                        """
                        UPDATE sim_order_events
                        SET origin = %s
                        WHERE cl_ord_id = ANY(%s) AND COALESCE(origin, '') != %s
                        """,
                        (origin, chunk, origin),
                    )
                    updated += int(cur.rowcount or 0)
                conn.commit()
        return updated

    def sim_order_event_origin_for(self, environment: str, cl_ord_id: str) -> str:
        target = str(cl_ord_id or "").strip()
        if not target:
            return ""
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT origin
                    FROM sim_order_events
                    WHERE environment = %s AND cl_ord_id = %s AND COALESCE(origin, '') != ''
                    ORDER BY ts DESC, id DESC
                    LIMIT 1
                    """,
                    (environment, target),
                )
                row = cur.fetchone()
                return str(row["origin"]) if row else ""

    def create_automation_strategy(self, strategy: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_strategies (
                        name, enabled, archived, archived_at, archived_reason, inst_id, inst_ids, daily_position_pct, bar, template, execution_mode, td_mode,
                        ord_type, sz, fast_window, slow_window, max_order_contracts,
                        max_position_contracts, cooldown_seconds, take_profit_pct, stop_loss_pct,
                        last_eval_ts, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    automation_strategy_row(strategy),
                )
                row = cur.fetchone()
            conn.commit()
            return self.get_automation_strategy(int(row["id"])) if row else {}

    def update_automation_strategy(self, strategy_id: int, strategy: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE automation_strategies
                    SET name = %s, enabled = %s, archived = %s, archived_at = %s, archived_reason = %s, inst_id = %s, inst_ids = %s, daily_position_pct = %s, bar = %s, template = %s, execution_mode = %s,
                        td_mode = %s, ord_type = %s, sz = %s, fast_window = %s, slow_window = %s,
                        max_order_contracts = %s, max_position_contracts = %s, cooldown_seconds = %s,
                        take_profit_pct = %s, stop_loss_pct = %s, last_eval_ts = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    automation_strategy_update_row(strategy, strategy_id),
                )
            conn.commit()
            return self.get_automation_strategy(strategy_id)

    def list_automation_strategies(self, include_archived: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                if include_archived:
                    cur.execute(
                        """
                        SELECT *
                        FROM automation_strategies
                        ORDER BY enabled DESC, archived ASC, updated_at DESC, id DESC
                        """
                    )
                else:
                    cur.execute(
                        """
                        SELECT *
                        FROM automation_strategies
                        WHERE COALESCE(archived, FALSE) = FALSE
                        ORDER BY enabled DESC, updated_at DESC, id DESC
                        """
                    )
                return list(cur.fetchall())

    def get_automation_strategy(self, strategy_id: int) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_strategies WHERE id = %s", (strategy_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def set_automation_strategy_last_eval(self, strategy_id: int, last_eval_ts: int, updated_at: int) -> None:
        self._execute(
            "UPDATE automation_strategies SET last_eval_ts = %s, updated_at = %s WHERE id = %s",
            (last_eval_ts, updated_at, strategy_id),
        )

    def insert_automation_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_signals (
                        strategy_id, ts, environment, inst_id, bar, template, action,
                        side, pos_side, price, sz, decision, reason, message, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    automation_signal_row(signal),
                )
                row = cur.fetchone()
            conn.commit()
            if not row:
                return {}
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_signals WHERE id = %s", (int(row["id"]),))
                inserted = cur.fetchone()
                return dict(inserted) if inserted else {}

    def get_automation_signal(self, signal_id: int) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.*, a.name AS strategy_name
                    FROM automation_signals s
                    LEFT JOIN automation_strategies a ON a.id = s.strategy_id
                    WHERE s.id = %s
                    """,
                    (signal_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_automation_signals(self, strategy_id: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.*, a.name AS strategy_name
                    FROM automation_signals s
                    LEFT JOIN automation_strategies a ON a.id = s.strategy_id
                    WHERE (%s = 0 OR s.strategy_id = %s)
                    ORDER BY s.ts DESC, s.id DESC
                    LIMIT %s
                    """,
                    (strategy_id, strategy_id, limit),
                )
                return list(cur.fetchall())

    def list_automation_signals_since(self, strategy_id: int, since_ts: int) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.*
                    FROM automation_signals s
                    WHERE s.strategy_id = %s AND s.ts >= %s
                    ORDER BY s.ts DESC, s.id DESC
                    """,
                    (strategy_id, since_ts),
                )
                return list(cur.fetchall())

    def latest_actionable_automation_signal(self, strategy_id: int) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM automation_signals
                    WHERE strategy_id = %s AND action IN ('long', 'short')
                    ORDER BY ts DESC, id DESC
                    LIMIT 1
                    """,
                    (strategy_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def insert_automation_risk_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_risk_snapshots (
                        signal_id, strategy_id, ts, allowed, severity, message, checks_json, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        snapshot["signal_id"],
                        snapshot["strategy_id"],
                        snapshot["ts"],
                        bool(snapshot.get("allowed")),
                        snapshot["severity"],
                        snapshot["message"],
                        snapshot["checks_json"],
                        snapshot["raw_json"],
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            if not row:
                return {}
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_risk_snapshots WHERE id = %s", (int(row["id"]),))
                inserted = cur.fetchone()
                return dict(inserted) if inserted else {}

    def get_automation_risk_snapshot(self, signal_id: int) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM automation_risk_snapshots
                    WHERE signal_id = %s
                    ORDER BY ts DESC, id DESC
                    LIMIT 1
                    """,
                    (signal_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def insert_automation_execution_step(self, step: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_execution_steps (
                        signal_id, strategy_id, step_order, ts, action, status, message, request_json, response_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        step["signal_id"],
                        step["strategy_id"],
                        step["step_order"],
                        step["ts"],
                        step["action"],
                        step["status"],
                        step["message"],
                        step["request_json"],
                        step["response_json"],
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            if not row:
                return {}
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_execution_steps WHERE id = %s", (int(row["id"]),))
                inserted = cur.fetchone()
                return dict(inserted) if inserted else {}

    def list_automation_execution_steps(self, signal_id: int) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM automation_execution_steps
                    WHERE signal_id = %s
                    ORDER BY step_order ASC, id ASC
                    """,
                    (signal_id,),
                )
                return list(cur.fetchall())

    def upsert_algo_order(self, order: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_algo_orders (
                        algo_cl_ord_id, strategy_id, inst_id, pos_side, td_mode, sz,
                        main_ord_id, avg_px, state, detail, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(algo_cl_ord_id) DO UPDATE SET
                        state=excluded.state,
                        main_ord_id=excluded.main_ord_id,
                        avg_px=excluded.avg_px,
                        detail=excluded.detail,
                        updated_at=excluded.updated_at
                    """,
                    _algo_order_row(order),
                )
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM automation_algo_orders WHERE algo_cl_ord_id = %s",
                    (str(order.get("algo_cl_ord_id") or ""),),
                )
                row = cur.fetchone()
                return dict(row) if row else {}

    def get_algo_order_by_cl_id(self, algo_cl_ord_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_algo_orders WHERE algo_cl_ord_id = %s", (algo_cl_ord_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def list_algo_orders(self, strategy_id: int = 0, states: list[str] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            clauses = ["(%s = 0 OR strategy_id = %s)"]
            params: list[Any] = [strategy_id, strategy_id]
            if states:
                placeholders = ",".join("%s" for _ in states)
                clauses.append(f"state IN ({placeholders})")
                params.extend(states)
            sql = (
                f"SELECT * FROM automation_algo_orders WHERE {' AND '.join(clauses)} "
                "ORDER BY created_at DESC, id DESC"
            )
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                return [dict(row) for row in cur.fetchall()]

    def delete_algo_order(self, algo_cl_ord_id: str) -> None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM automation_algo_orders WHERE algo_cl_ord_id = %s", (algo_cl_ord_id,))
            conn.commit()

    def insert_automation_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO automation_alerts (
                        ts, severity, source, message, strategy_id, signal_id, order_event_id, acknowledged_at, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        alert["ts"],
                        alert["severity"],
                        alert["source"],
                        alert["message"],
                        alert.get("strategy_id"),
                        alert.get("signal_id"),
                        alert.get("order_event_id"),
                        alert.get("acknowledged_at"),
                        alert["raw_json"],
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            if not row:
                return {}
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM automation_alerts WHERE id = %s", (int(row["id"]),))
                inserted = cur.fetchone()
                return dict(inserted) if inserted else {}

    def list_automation_alerts(
        self,
        active_only: bool = False,
        severity: str = "",
        source: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM automation_alerts
                    WHERE (%s = FALSE OR acknowledged_at IS NULL)
                      AND (%s = '' OR severity = %s)
                      AND (%s = '' OR source = %s)
                    ORDER BY ts DESC, id DESC
                    LIMIT %s
                    """,
                    (active_only, severity, severity, source, source, limit),
                )
                return list(cur.fetchall())

    def count_automation_alerts(self, active_only: bool = False, severity: str = "", source: str = "") -> int:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM automation_alerts
                    WHERE (%s = FALSE OR acknowledged_at IS NULL)
                      AND (%s = '' OR severity = %s)
                      AND (%s = '' OR source = %s)
                    """,
                    (active_only, severity, severity, source, source),
                )
                row = cur.fetchone()
                return int(row["total"]) if row else 0

    def acknowledge_automation_alert(self, alert_id: int, acknowledged_at: int) -> None:
        self._execute(
            "UPDATE automation_alerts SET acknowledged_at = %s WHERE id = %s",
            (acknowledged_at, alert_id),
        )

    def insert_llm_usage_log(self, log: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_usage_logs (
                        request_id, ts, provider, model, mode, request_type, status,
                        strategy_id, signal_id, inst_id, bar, profile_id, profile_version, profile_hash, prompt_tokens, completion_tokens,
                        total_tokens, cached_tokens, reasoning_tokens, cache_hit_tokens,
                        cache_miss_tokens, duration_ms, timeout_seconds, finish_reason,
                        error, raw_usage_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    llm_usage_log_row(log),
                )
                row = cur.fetchone()
            conn.commit()
            if not row:
                return {}
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM llm_usage_logs WHERE id = %s", (int(row["id"]),))
                inserted = cur.fetchone()
                return dict(inserted) if inserted else {}

    def list_llm_usage_logs(
        self, limit: int = 100, offset: int = 0, request_type: str = "", status: str = "", strategy_id: int = 0
    ) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM llm_usage_logs
                    WHERE (%s = '' OR request_type = %s)
                      AND (%s = '' OR status = %s)
                      AND (%s = 0 OR strategy_id = %s)
                    ORDER BY ts DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (request_type, request_type, status, status, strategy_id, strategy_id, limit, offset),
                )
                return list(cur.fetchall())

    def count_llm_usage_logs(self, request_type: str = "", status: str = "", strategy_id: int = 0) -> int:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM llm_usage_logs
                    WHERE (%s = '' OR request_type = %s)
                      AND (%s = '' OR status = %s)
                      AND (%s = 0 OR strategy_id = %s)
                    """,
                    (request_type, request_type, status, status, strategy_id, strategy_id),
                )
                row = cur.fetchone()
                return int(row["total"]) if row else 0

    def llm_usage_summary(self, since_ts: int = 0) -> dict[str, Any]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS calls,
                        COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                        COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                        COALESCE(SUM(total_tokens), 0) AS total_tokens,
                        COALESCE(SUM(cached_tokens), 0) AS cached_tokens,
                        COALESCE(SUM(reasoning_tokens), 0) AS reasoning_tokens,
                        COALESCE(SUM(cache_hit_tokens), 0) AS cache_hit_tokens,
                        COALESCE(SUM(cache_miss_tokens), 0) AS cache_miss_tokens,
                        COALESCE(SUM(CASE WHEN status <> 'success' THEN 1 ELSE 0 END), 0) AS failed_calls,
                        COALESCE(ROUND(AVG(duration_ms)), 0) AS avg_duration_ms
                    FROM llm_usage_logs
                    WHERE (%s = 0 OR ts >= %s)
                    """,
                    (since_ts, since_ts),
                )
                row = cur.fetchone()
                return dict(row) if row else {}

    def get_app_setting(self, key: str) -> str | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM app_settings WHERE key = %s", (key,))
                row = cur.fetchone()
                return str(row["value"]) if row else None

    def set_app_setting(self, key: str, value: str, ts: int) -> None:
        self._execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (key, value, ts),
        )

    def upsert_market_event(self, event: dict[str, Any]) -> dict[str, Any]:
        columns = ("id", "provider", "provider_event_key", "title", "category", "importance", "state", "scheduled_at", "source_timezone", "published_at", "fetched_at", "actual", "forecast", "previous_value", "revision", "unit", "period_label", "source_url", "source_summary", "official", "payload_hash")
        # SQLite accepts 0/1 for the same column, but psycopg sends an integer
        # parameter as SMALLINT.  Normalize at this database boundary so the
        # PostgreSQL BOOLEAN column always receives a real Python bool.
        event = {**event, "official": bool(event.get("official"))}
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM market_events WHERE provider = %s AND provider_event_key = %s", (event["provider"], event["provider_event_key"]))
                    current = cur.fetchone()
                    if current:
                        event["id"] = str(current["id"])
                        previous = dict(current)
                        event = retain_published_market_event(event, previous)
                        if event.get("state") == "released" and str(previous.get("state") or "") in {"released", "revised"} and any(
                            (event.get(field) or "") != (previous.get(field) or "") for field in ("actual", "previous_value", "revision", "period_label")
                        ):
                            event["state"] = "revised"
                    placeholders = ", ".join("%s" for _ in columns)
                    updates = ", ".join(f"{name}=excluded.{name}" for name in columns if name not in {"id", "provider", "provider_event_key"})
                    cur.execute(f"INSERT INTO market_events ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT(provider, provider_event_key) DO UPDATE SET {updates}", tuple(event.get(column) for column in columns))
                    cur.execute("INSERT INTO market_event_versions (event_id, observed_at, state, actual, forecast, previous_value, revision, unit, period_label, source_summary, payload_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT(event_id, payload_hash) DO NOTHING", (event["id"], event["fetched_at"], event["state"], event.get("actual"), event.get("forecast"), event.get("previous_value"), event.get("revision"), event.get("unit"), event.get("period_label"), event.get("source_summary") or "", event["payload_hash"]))
                    cur.execute("SELECT * FROM market_events WHERE id = %s", (event["id"],)); result = cur.fetchone()
                conn.commit(); return dict(result) if result else {}
            except Exception:
                conn.rollback()
                raise

    def prune_unmatched_scheduled_market_events(self, provider: str, event_keys: list[str], start_ts: int, end_ts: int) -> int:
        if not event_keys or end_ts <= start_ts:
            return 0
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM market_events WHERE provider = %s AND state = 'scheduled' AND scheduled_at >= %s AND scheduled_at <= %s AND provider_event_key <> ALL(%s)",
                        (provider, start_ts, end_ts, event_keys),
                    )
                    event_ids = [str(row["id"]) for row in cur.fetchall()]
                    if not event_ids:
                        return 0
                    cur.execute("DELETE FROM market_event_versions WHERE event_id = ANY(%s)", (event_ids,))
                    cur.execute("DELETE FROM market_events WHERE id = ANY(%s)", (event_ids,))
                conn.commit()
                return len(event_ids)
            except Exception:
                conn.rollback()
                raise

    def list_market_events(self, start_ts: int, end_ts: int, categories: list[str], states: list[str]) -> list[dict[str, Any]]:
        clauses, params = ["scheduled_at >= %s", "scheduled_at < %s"], [start_ts, end_ts]
        if categories: clauses.append("category = ANY(%s)"); params.append(categories)
        if states: clauses.append("state = ANY(%s)"); params.append(states)
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM market_events WHERE {' AND '.join(clauses)} ORDER BY scheduled_at ASC, title ASC", tuple(params)); return list(cur.fetchall())

    def count_market_events(self, provider: str = "") -> int:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                if provider:
                    cur.execute("SELECT COUNT(*) AS count FROM market_events WHERE provider = %s", (provider,))
                else:
                    cur.execute("SELECT COUNT(*) AS count FROM market_events")
                row = cur.fetchone()
                return int(row["count"] if row else 0)

    def get_market_event(self, event_id: str) -> dict[str, Any] | None:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM market_events WHERE id = %s", (event_id,)); return cur.fetchone()

    def list_market_event_versions(self, event_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM market_event_versions WHERE event_id = %s ORDER BY observed_at ASC, id ASC", (event_id,)); return list(cur.fetchall())


def instrument_rows(instruments: list[dict[str, Any]], updated_at: int) -> list[tuple[Any, ...]]:
    return [
        (
            item.get("instId"),
            item.get("instType", "SWAP"),
            item.get("uly"),
            item.get("instFamily"),
            item.get("baseCcy"),
            item.get("quoteCcy"),
            item.get("settleCcy"),
            item.get("ctVal"),
            item.get("tickSz"),
            item.get("lotSz"),
            item.get("state"),
            updated_at,
        )
        for item in instruments
        if item.get("instId")
    ]


def candle_rows(inst_id: str, bar: str, candles: list[dict[str, str]]) -> list[tuple[Any, ...]]:
    return [
        (
            inst_id,
            bar,
            int(item["ts"]),
            item["open"],
            item["high"],
            item["low"],
            item["close"],
            item["volume"],
            item.get("volumeCcy"),
            item.get("volumeQuote"),
            item.get("confirm"),
        )
        for item in candles
    ]


def account_snapshot_row(environment: str, ts: int, payload: dict[str, Any], details_json: str) -> tuple[Any, ...]:
    return (
        environment,
        ts,
        payload.get("totalEq"),
        payload.get("adjEq"),
        payload.get("imr"),
        payload.get("mmr"),
        payload.get("isoEq"),
        details_json,
    )


def position_snapshot_rows(
    environment: str, ts: int, positions: list[dict[str, Any]], raw_json: str
) -> list[tuple[Any, ...]]:
    return [
        (
            environment,
            ts,
            item.get("instId", ""),
            item.get("posSide"),
            item.get("pos"),
            item.get("avgPx"),
            item.get("markPx"),
            item.get("upl"),
            item.get("uplRatio"),
            item.get("margin"),
            raw_json,
        )
        for item in positions
    ]


def sim_order_event_row(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        event["environment"],
        event["ts"],
        event["action"],
        event["inst_id"],
        event.get("td_mode"),
        event.get("side"),
        event.get("pos_side"),
        event.get("ord_type"),
        event.get("px"),
        event.get("sz"),
        bool(event.get("reduce_only")),
        event.get("cl_ord_id"),
        event.get("ord_id"),
        event.get("state"),
        event.get("code"),
        event.get("message"),
        event["request_json"],
        event["response_json"],
        event.get("pnl_usd"),
        event.get("pnl_pct"),
        event.get("pnl_basis"),
        event.get("origin") or "manual",
    )


def automation_strategy_row(strategy: dict[str, Any]) -> tuple[Any, ...]:
    return (
        strategy["name"],
        bool(strategy.get("enabled")),
        bool(strategy.get("archived")),
        strategy.get("archived_at"),
        strategy.get("archived_reason") or "",
        strategy["inst_id"],
        str(strategy.get("inst_ids") or "[]"),
        str(strategy.get("daily_position_pct") or "0"),
        strategy["bar"],
        strategy["template"],
        strategy["execution_mode"],
        strategy["td_mode"],
        strategy["ord_type"],
        strategy["sz"],
        int(strategy["fast_window"]),
        int(strategy["slow_window"]),
        strategy["max_order_contracts"],
        strategy["max_position_contracts"],
        int(strategy["cooldown_seconds"]),
        strategy.get("take_profit_pct", "0"),
        strategy.get("stop_loss_pct", "0"),
        strategy.get("last_eval_ts"),
        int(strategy["created_at"]),
        int(strategy["updated_at"]),
    )


def automation_strategy_update_row(strategy: dict[str, Any], strategy_id: int) -> tuple[Any, ...]:
    return (
        strategy["name"],
        bool(strategy.get("enabled")),
        bool(strategy.get("archived")),
        strategy.get("archived_at"),
        strategy.get("archived_reason") or "",
        strategy["inst_id"],
        str(strategy.get("inst_ids") or "[]"),
        str(strategy.get("daily_position_pct") or "0"),
        strategy["bar"],
        strategy["template"],
        strategy["execution_mode"],
        strategy["td_mode"],
        strategy["ord_type"],
        strategy["sz"],
        int(strategy["fast_window"]),
        int(strategy["slow_window"]),
        strategy["max_order_contracts"],
        strategy["max_position_contracts"],
        int(strategy["cooldown_seconds"]),
        strategy.get("take_profit_pct", "0"),
        strategy.get("stop_loss_pct", "0"),
        strategy.get("last_eval_ts"),
        int(strategy["updated_at"]),
        strategy_id,
    )


def automation_signal_row(signal: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(signal["strategy_id"]),
        int(signal["ts"]),
        signal["environment"],
        signal["inst_id"],
        signal["bar"],
        signal["template"],
        signal["action"],
        signal.get("side"),
        signal.get("pos_side"),
        signal.get("price"),
        signal.get("sz"),
        signal["decision"],
        signal.get("reason"),
        signal.get("message"),
        signal["raw_json"],
    )


def _algo_order_row(order: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(order["algo_cl_ord_id"]),
        int(order["strategy_id"]),
        str(order["inst_id"]),
        str(order.get("pos_side") or ""),
        str(order.get("td_mode") or "cross"),
        str(order.get("sz") or ""),
        str(order.get("main_ord_id") or ""),
        str(order.get("avg_px") or ""),
        str(order.get("state") or "pending"),
        str(order.get("detail") or ""),
        int(order["created_at"]),
        int(order["updated_at"]),
    )


def automation_risk_snapshot_row(snapshot: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(snapshot["signal_id"]),
        int(snapshot["strategy_id"]),
        int(snapshot["ts"]),
        bool(snapshot.get("allowed")),
        snapshot["severity"],
        snapshot["message"],
        snapshot["checks_json"],
        snapshot["raw_json"],
    )


def automation_execution_step_row(step: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(step["signal_id"]),
        int(step["strategy_id"]),
        int(step["step_order"]),
        int(step["ts"]),
        step["action"],
        step["status"],
        step["message"],
        step["request_json"],
        step["response_json"],
    )


def automation_alert_row(alert: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(alert["ts"]),
        alert["severity"],
        alert["source"],
        alert["message"],
        alert.get("strategy_id"),
        alert.get("signal_id"),
        alert.get("order_event_id"),
        alert.get("acknowledged_at"),
        alert["raw_json"],
    )


def int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def llm_usage_log_row(log: dict[str, Any]) -> tuple[Any, ...]:
    return (
        log["request_id"],
        int(log["ts"]),
        log.get("provider"),
        log.get("model"),
        log.get("mode"),
        log["request_type"],
        log["status"],
        log.get("strategy_id"),
        log.get("signal_id"),
        log.get("inst_id"),
        log.get("bar"),
        log.get("profile_id"),
        log.get("profile_version"),
        log.get("profile_hash"),
        int_or_zero(log.get("prompt_tokens")),
        int_or_zero(log.get("completion_tokens")),
        int_or_zero(log.get("total_tokens")),
        int_or_zero(log.get("cached_tokens")),
        int_or_zero(log.get("reasoning_tokens")),
        int_or_zero(log.get("cache_hit_tokens")),
        int_or_zero(log.get("cache_miss_tokens")),
        int_or_zero(log.get("duration_ms")),
        int_or_zero(log.get("timeout_seconds")),
        log.get("finish_reason"),
        log.get("error"),
        log.get("raw_usage_json") or "{}",
    )
