"""策略表单「模拟盘账户金额」回显接口的回归测试。"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app import main


class FakeSettings:
    account_cache_seconds = 60

    def __init__(self, configured=True):
        self.configured = configured

    def has_credentials_for_environment(self, environment):
        return self.configured


def fake_account(summary=None, **overrides):
    payload = {
        "environment": "simulated",
        "summary": summary if summary is not None else {"totalEq": "80796.80", "availEq": "70000.00"},
        "positions": [],
        "source": "okx",
        "ts": 1_700_000_000_000,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def equity_env(monkeypatch):
    """把外部依赖收敛到可控桩上，避免测试真的请求 OKX 或数据库。"""
    monkeypatch.setattr(main, "settings", FakeSettings())
    monkeypatch.setattr(main, "automation_equity_snapshot", lambda force=False: (fake_account(), "okx"))
    monkeypatch.setattr(main, "automation_daily_used_notional", lambda strategy_id, day_start: Decimal("100"))
    return monkeypatch


def test_equity_endpoint_returns_simulated_account_and_derived_limit(equity_env):
    data = main.automation_equity(dailyPositionPct="20", strategyId=7)["data"]

    assert data["environment"] == "simulated"
    assert data["configured"] is True
    assert data["available"] is True
    assert data["currency"] == "USDT"
    assert data["totalEq"] == "80796.80"
    assert data["availEq"] == "70000.00"
    assert data["equity"] == "80796.80"
    assert data["equityBasis"] == "totalEq"
    assert data["dailyPositionPct"] == "20"
    assert data["dailyLimit"] == "16159.36"
    assert data["dailyUsed"] == "100.00"
    assert data["dailyUsedAvailable"] is True
    assert data["dailyRemaining"] == "16059.36"
    assert data["dailyResetAt"] - data["dailyDayStart"] == 86_400_000
    assert data["message"] == ""


def test_zero_pct_still_echoes_account_amount(equity_env):
    data = main.automation_equity(dailyPositionPct="0")["data"]

    assert data["equity"] == "80796.80"
    assert data["dailyLimit"] == "0.00"
    assert data["available"] is True


def test_equity_falls_back_to_avail_eq(equity_env):
    equity_env.setattr(
        main,
        "automation_equity_snapshot",
        lambda force=False: (fake_account(summary={"availEq": "5000"}), "okx"),
    )
    data = main.automation_equity(dailyPositionPct="10")["data"]

    assert data["equity"] == "5000.00"
    assert data["equityBasis"] == "availEq"
    assert data["dailyLimit"] == "500.00"


@pytest.mark.parametrize("value", ["", "abc", "-1", "101", "1e999"])
def test_invalid_pct_never_breaks_the_form(equity_env, value):
    data = main.automation_equity(dailyPositionPct=value)["data"]

    assert data["pctInvalid"] is True
    assert data["dailyPositionPct"] == "0"
    assert data["equity"] == "80796.80"
    assert data["dailyLimit"] == "0.00"


def test_unconfigured_credentials_report_unavailable(equity_env):
    equity_env.setattr(main, "settings", FakeSettings(configured=False))
    equity_env.setattr(
        main,
        "automation_equity_snapshot",
        lambda force=False: pytest.fail("未配置凭证时不应请求账户"),
    )

    data = main.automation_equity(dailyPositionPct="20")["data"]

    assert data["configured"] is False
    assert data["available"] is False
    assert data["source"] == "not-configured"
    assert "未配置" in data["message"]
    assert "拦截" in data["message"]


def test_unreadable_equity_explains_fail_closed(equity_env):
    equity_env.setattr(
        main,
        "automation_equity_snapshot",
        lambda force=False: (fake_account(summary={}, source="error"), "error"),
    )

    data = main.automation_equity(dailyPositionPct="20")["data"]

    assert data["available"] is False
    assert data["equity"] == ""
    assert data["dailyLimit"] == ""
    assert "拦截" in data["message"]


def test_daily_used_unavailable_is_flagged(equity_env):
    equity_env.setattr(main, "automation_daily_used_notional", lambda strategy_id, day_start: None)

    data = main.automation_equity(dailyPositionPct="20")["data"]

    assert data["dailyUsedAvailable"] is False
    assert data["dailyUsed"] == ""
    assert data["dailyRemaining"] == ""
    assert "拦截" in data["warning"]


def test_fresh_cache_does_not_hit_okx(monkeypatch):
    monkeypatch.setattr(main, "settings", FakeSettings())
    cached = fake_account()
    monkeypatch.setattr(
        main,
        "account_cache_values",
        lambda environment: (cached, main.now_ms(), False, 0, 0),
    )
    monkeypatch.setattr(
        main,
        "refresh_account_cache_sync",
        lambda environment: pytest.fail("缓存有效时不应同步请求 OKX"),
    )

    payload, source = main.automation_equity_snapshot(force=False)

    assert source == "cache"
    assert payload["summary"]["totalEq"] == "80796.80"


def test_force_refresh_and_failure_fallback(monkeypatch):
    monkeypatch.setattr(main, "settings", FakeSettings())
    calls = []
    cached = fake_account()

    monkeypatch.setattr(
        main,
        "account_cache_values",
        lambda environment: (cached, main.now_ms(), False, 0, 0),
    )

    def failing_refresh(environment):
        calls.append(environment)
        raise RuntimeError("OKX timeout")

    monkeypatch.setattr(main, "refresh_account_cache_sync", failing_refresh)
    monkeypatch.setattr(
        main,
        "account_fallback_response",
        lambda environment, warning: fake_account(source="database-cache", ts=1_700_000_000_000),
    )

    payload, source = main.automation_equity_snapshot(force=True)

    assert calls == ["simulated"]
    assert source == "cache"
    assert payload["source"] == "database-cache"


def test_equity_route_is_registered():
    paths = main.app.openapi()["paths"]
    assert "/api/automation/equity" in paths
    assert "get" in paths["/api/automation/equity"]
