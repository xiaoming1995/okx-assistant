import json

import pytest
from fastapi import HTTPException

from backend.app import main


def automation_strategy(**overrides):
    strategy = {
        "id": 0,
        "name": "BTC LLM",
        "enabled": True,
        "inst_id": "BTC-USDT-SWAP",
        "bar": "5m",
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
        "take_profit_pct": "0",
        "stop_loss_pct": "0",
        "last_eval_ts": None,
        "created_at": 100,
        "updated_at": 100,
    }
    strategy.update(overrides)
    return strategy


def test_automation_preview_normalizes_and_validates_stop_percentages():
    payload = main.AutomationPreviewRequest(takeProfitPct="2.50", stopLossPct="1.25")

    preview_strategy = main.normalized_strategy_from_preview_payload(payload)

    assert preview_strategy["take_profit_pct"] == "2.5"
    assert preview_strategy["stop_loss_pct"] == "1.25"

    with pytest.raises(HTTPException, match="止损幅度不能小于 0"):
        main.normalized_strategy_from_preview_payload(main.AutomationPreviewRequest(stopLossPct="-1"))


def test_llm_confidence_below_threshold_blocks_auto_trade(monkeypatch):
    class FakeSettings:
        def has_credentials_for_environment(self, environment):
            return True

    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": True})
    monkeypatch.setattr(main, "refresh_account_cache_sync", lambda environment: {"positions": [], "summary": {}, "source": "okx"})

    preview = main.automation_risk_preview(
        automation_strategy(),
        {
            "action": "long",
            "side": "buy",
            "pos_side": "long",
            "price": "64000",
            "llm_confidence": 69,
        },
    )

    assert preview["allowed"] is False
    assert preview["severity"] == "blocked"
    assert "置信度" in preview["message"]


def test_execute_automation_order_reverses_opposite_position(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main,
        "refresh_account_cache_sync",
        lambda environment: {
            "positions": [{"instId": "BTC-USDT-SWAP", "pos": "-2", "posSide": "net", "mgnMode": "cross"}],
            "summary": {},
        },
    )

    def fake_close(environment, order):
        calls.append(("close", environment, order.instId, order.posSide))
        return {"ok": True, "event": {"action": "close-position"}}

    def fake_place(environment, order):
        calls.append(("place", environment, order.instId, order.side, order.posSide, order.sz))
        return {"ok": True, "event": {"action": "place"}}

    monkeypatch.setattr(main, "close_position_for_environment", fake_close)
    monkeypatch.setattr(main, "place_order_for_environment", fake_place)

    result = main.execute_automation_order(
        automation_strategy(),
        {"action": "long", "side": "buy", "pos_side": "long", "price": "64000"},
    )

    assert result["action"] == "reverse"
    assert calls == [
        ("close", "simulated", "BTC-USDT-SWAP", "net"),
        ("place", "simulated", "BTC-USDT-SWAP", "buy", "long", "2"),
    ]


def test_execute_automation_order_skips_same_direction_position(monkeypatch):
    monkeypatch.setattr(
        main,
        "refresh_account_cache_sync",
        lambda environment: {
            "positions": [{"instId": "BTC-USDT-SWAP", "pos": "2", "posSide": "long", "mgnMode": "cross"}],
            "summary": {},
        },
    )

    def fail_place(environment, order):
        raise AssertionError("same-direction positions must not open another order")

    monkeypatch.setattr(main, "place_order_for_environment", fail_place)

    result = main.execute_automation_order(
        automation_strategy(),
        {"action": "long", "side": "buy", "pos_side": "long", "price": "64000"},
    )

    assert result["action"] == "skip_same_direction"


def test_automation_exit_signal_triggers_take_profit():
    signal = main.automation_exit_signal(
        automation_strategy(take_profit_pct="2", stop_loss_pct="1"),
        {
            "positions": [
                {
                    "instId": "BTC-USDT-SWAP",
                    "pos": "2",
                    "posSide": "long",
                    "avgPx": "100",
                    "markPx": "103",
                    "mgnMode": "cross",
                }
            ]
        },
    )

    assert signal is not None
    assert signal["action"] == "take_profit"
    assert signal["pos_side"] == "long"
    assert signal["profit_pct"] == "3"


def test_evaluate_strategy_closes_position_on_stop_loss(monkeypatch):
    class FakeSettings:
        def has_credentials_for_environment(self, environment):
            return True

    class FakeDatabase:
        def insert_automation_signal(self, payload):
            return {"id": 1, **payload}

    close_calls = []
    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(
        main,
        "refresh_account_cache_sync",
        lambda environment: {
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
        },
    )

    def fake_close(environment, order):
        close_calls.append((environment, order.instId, order.posSide))
        return {"ok": True, "event": {"action": "close-position"}}

    monkeypatch.setattr(main, "close_position_for_environment", fake_close)

    result = main.evaluate_automation_strategy(
        automation_strategy(id=2, take_profit_pct="3", stop_loss_pct="1"),
        force=True,
    )
    raw = json.loads(result["raw_json"])

    assert result["action"] == "stop_loss"
    assert result["decision"] == "submitted"
    assert close_calls == [("simulated", "BTC-USDT-SWAP", "long")]
    assert raw["profit_pct"] == "-2"


def test_toggle_llm_strategy_requires_enabled_llm_config(monkeypatch):
    class FakeDatabase:
        def get_automation_strategy(self, strategy_id):
            return automation_strategy(id=strategy_id, enabled=False)

        def list_automation_strategies(self):
            return []

        def update_automation_strategy(self, strategy_id, strategy):
            raise AssertionError("LLM-disabled strategies must not be enabled")

    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})

    with pytest.raises(main.HTTPException) as exc_info:
        main.toggle_automation_strategy(2, main.AutomationToggleRequest(enabled=True))

    assert exc_info.value.status_code == 400
    assert "启用 LLM" in exc_info.value.detail


def test_disabled_llm_runtime_signal_is_blocked_not_failed(monkeypatch):
    class FakeDatabase:
        def __init__(self):
            self.last_eval = None

        def set_automation_strategy_last_eval(self, strategy_id, candle_ts, updated_at):
            self.last_eval = (strategy_id, candle_ts, updated_at)

        def insert_automation_signal(self, payload):
            return {"id": 1, **payload}

    candles = [
        {"ts": str(1000 + index), "open": "64000", "high": "64100", "low": "63900", "close": "64000", "volume": "10"}
        for index in range(30)
    ]
    fake_database = FakeDatabase()

    monkeypatch.setattr(main, "database", fake_database)
    monkeypatch.setattr(main, "stored_llm_config", lambda: {"enabled": False})
    monkeypatch.setattr(main, "closed_strategy_candles", lambda inst_id, bar, limit: candles)
    monkeypatch.setattr(main, "llm_account_payload_for_signal", lambda: {"positions": [], "summary": {}})

    result = main.evaluate_automation_strategy(automation_strategy(id=2), force=True)
    raw = json.loads(result["raw_json"])

    assert result["decision"] == "blocked"
    assert "LLM 未启用" in result["message"]
    assert raw["llm_config_error"] is True


def test_llm_runtime_error_uses_ai_failure_decision(monkeypatch):
    class FakeDatabase:
        def set_automation_strategy_last_eval(self, strategy_id, candle_ts, updated_at):
            self.last_eval = (strategy_id, candle_ts, updated_at)

        def insert_automation_signal(self, payload):
            return {"id": 1, **payload}

    candles = [
        {"ts": str(1000 + index), "open": "64000", "high": "64100", "low": "63900", "close": "64000", "volume": "10"}
        for index in range(30)
    ]
    monkeypatch.setattr(main, "database", FakeDatabase())
    monkeypatch.setattr(main, "closed_strategy_candles", lambda inst_id, bar, limit: candles)
    monkeypatch.setattr(main, "llm_account_payload_for_signal", lambda: {"positions": [], "summary": {}})
    monkeypatch.setattr(
        main,
        "llm_direct_signal",
        lambda strategy, candles, account: {
            "action": "hold",
            "side": None,
            "pos_side": None,
            "price": "64000",
            "candle_ts": 1029,
            "reason": "LLM 判断失败：LLM 请求超时（20秒）。",
            "llm_error": "LLM 请求超时（20秒）。",
            "record_hold": True,
        },
    )

    result = main.evaluate_automation_strategy(automation_strategy(id=2), force=True)

    assert result["decision"] == "llm_failed"
    assert "LLM 判断失败" in result["message"]


def test_signal_api_normalizes_legacy_llm_failures(monkeypatch):
    class FakeDatabase:
        def list_automation_signals(self, strategy_id, limit):
            return [
                {
                    "id": 79,
                    "decision": "failed",
                    "raw_json": json.dumps({"llm_error": "LLM 请求超时。"}, ensure_ascii=False),
                },
                {"id": 80, "decision": "failed", "raw_json": "{}"},
            ]

    monkeypatch.setattr(main, "database", FakeDatabase())

    result = main.automation_signals(strategyId=0, limit=10)

    assert result["data"][0]["decision"] == "llm_failed"
    assert result["data"][1]["decision"] == "failed"


def test_signal_detail_api_returns_single_signal(monkeypatch):
    class FakeDatabase:
        def get_automation_signal(self, signal_id):
            assert signal_id == 79
            return {
                "id": 79,
                "strategy_id": 2,
                "decision": "failed",
                "raw_json": json.dumps({"llm_error": "LLM 请求超时。"}, ensure_ascii=False),
            }

    monkeypatch.setattr(main, "database", FakeDatabase())

    result = main.automation_signal_detail(79)

    assert result["data"]["id"] == 79
    assert result["data"]["decision"] == "llm_failed"


def test_signal_detail_api_returns_404_for_missing_signal(monkeypatch):
    class FakeDatabase:
        def get_automation_signal(self, signal_id):
            return None

    monkeypatch.setattr(main, "database", FakeDatabase())

    with pytest.raises(main.HTTPException) as exc_info:
        main.automation_signal_detail(404)

    assert exc_info.value.status_code == 404


def test_pause_and_resume_automation_updates_global_state(monkeypatch):
    stored_settings = {}
    alerts = []

    class FakeDatabase:
        def get_app_setting(self, key):
            return stored_settings.get(key)

        def set_app_setting(self, key, value, ts):
            stored_settings[key] = value

        def insert_automation_alert(self, payload):
            alert = {"id": len(alerts) + 1, **payload}
            alerts.append(alert)
            return alert

        def list_automation_alerts(self, active_only=False, severity="", source="", limit=100):
            rows = list(alerts)
            if active_only:
                rows = [item for item in rows if item.get("acknowledged_at") is None]
            if severity:
                rows = [item for item in rows if item.get("severity") == severity]
            if source:
                rows = [item for item in rows if item.get("source") == source]
            return rows[:limit]

        def count_automation_alerts(self, active_only=False, severity="", source=""):
            return len(self.list_automation_alerts(active_only=active_only, severity=severity, source=source))

        def acknowledge_automation_alert(self, alert_id, acknowledged_at):
            for alert in alerts:
                if alert["id"] == alert_id:
                    alert["acknowledged_at"] = acknowledged_at

        def list_automation_strategies(self, include_archived=False):
            return []

    monkeypatch.setattr(main, "database", FakeDatabase())

    paused = main.pause_automation(main.AutomationPauseRequest(reason="手动暂停"))
    status_after_pause = main.automation_status_payload()
    resumed = main.resume_automation()
    status_after_resume = main.automation_status_payload()

    assert paused["data"]["globalPaused"] is True
    assert status_after_pause["globalPaused"] is True
    assert status_after_pause["alertCount"] == 1
    assert resumed["data"]["globalPaused"] is False
    assert status_after_resume["globalPaused"] is False
    assert status_after_resume["alertCount"] == 0


def test_stored_llm_config_migrates_legacy_default_prompt(monkeypatch):
    class FakeDatabase:
        def get_app_setting(self, key):
            assert key == main.LLM_CONFIG_KEY
            return json.dumps(
                {
                    "enabled": True,
                    "provider": "openai_compatible",
                    "baseUrl": "https://api.example.test/v1",
                    "apiKey": "secret",
                    "model": "model-a",
                    "mode": "explain_only",
                    "systemPrompt": main.LEGACY_LLM_SYSTEM_PROMPT,
                },
                ensure_ascii=False,
            )

    monkeypatch.setattr(main, "database", FakeDatabase())

    config = main.stored_llm_config()

    assert config["mode"] == "direct_signal"
    assert config["systemPrompt"] == main.DEFAULT_LLM_SYSTEM_PROMPT


def test_deepseek_llm_request_enables_json_output(monkeypatch):
    captured = {}

    class FakeDatabase:
        def __init__(self):
            self.logs = []

        def insert_llm_usage_log(self, payload):
            self.logs.append(payload)
            return {"id": len(self.logs), **payload}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return (
                b'{"choices":[{"finish_reason":"stop","message":{"content":"{\\"recommendation\\":\\"hold\\"}"}}],'
                b'"usage":{"prompt_tokens":12,"completion_tokens":5,"total_tokens":17,'
                b'"prompt_tokens_details":{"cached_tokens":3},"completion_tokens_details":{"reasoning_tokens":1}}}'
            )

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    fake_database = FakeDatabase()
    monkeypatch.setattr(main, "database", fake_database)
    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    result = main.llm_chat_completion(
        {
            "baseUrl": "https://api.deepseek.com",
            "apiKey": "secret",
            "model": "deepseek-v4-flash",
            "temperature": 0.2,
            "maxTokens": 800,
            "timeoutSeconds": 8,
        },
        [{"role": "user", "content": "输出 JSON"}],
    )

    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["thinking"] == {"type": "disabled"}
    assert captured["body"]["model"] == "deepseek-v4-flash"
    assert captured["timeout"] == main.LLM_DIRECT_MIN_TIMEOUT_SECONDS
    assert result["content"] == '{"recommendation":"hold"}'
    assert result["usage"]["total_tokens"] == 17
    assert result["usage"]["cached_tokens"] == 3
    assert result["usage"]["reasoning_tokens"] == 1
    assert result["usage_log"]["id"] == 1
    assert fake_database.logs[0]["request_type"] == "unknown"
    assert fake_database.logs[0]["status"] == "success"


def test_llm_usage_endpoint_returns_summary_and_paging(monkeypatch):
    class FakeDatabase:
        def list_llm_usage_logs(self, limit, offset, request_type, status, strategy_id):
            assert (limit, offset, request_type, status, strategy_id) == (10, 10, "direct_signal", "success", 7)
            return [
                {
                    "id": 2,
                    "request_id": "req-2",
                    "ts": "1786658424150",
                    "request_type": "direct_signal",
                    "status": "success",
                    "strategy_id": 7,
                    "prompt_tokens": "12",
                    "completion_tokens": "5",
                    "total_tokens": "17",
                    "cached_tokens": "3",
                    "reasoning_tokens": "1",
                    "cache_hit_tokens": "0",
                    "cache_miss_tokens": "0",
                    "duration_ms": "250",
                    "timeout_seconds": "20",
                }
            ]

        def count_llm_usage_logs(self, request_type, status, strategy_id):
            assert (request_type, status, strategy_id) == ("direct_signal", "success", 7)
            return 21

        def llm_usage_summary(self, since_ts=0):
            return {
                "calls": 21 if since_ts == 0 else 3,
                "prompt_tokens": 120,
                "completion_tokens": 50,
                "total_tokens": 170,
                "cached_tokens": 30,
                "reasoning_tokens": 10,
                "cache_hit_tokens": 30,
                "cache_miss_tokens": 90,
                "failed_calls": 0,
                "avg_duration_ms": 250,
            }

    monkeypatch.setattr(main, "database", FakeDatabase())

    result = main.llm_usage(limit=10, offset=10, requestType="direct_signal", status="success", strategyId=7)

    assert result["data"][0]["ts"] == 1786658424150
    assert result["data"][0]["total_tokens"] == 17
    assert result["summary"]["totalTokens"] == 170
    assert result["last24h"]["calls"] == 3
    assert result["paging"] == {"limit": 10, "offset": 10, "hasMore": False, "total": 21, "page": 2, "pageCount": 3}
