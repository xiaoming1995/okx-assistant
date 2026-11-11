from backend.app.config import Settings, load_env


def test_load_env_keeps_existing_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("OKX_BASE_URL=https://us.okx.com\n", encoding="utf-8")
    monkeypatch.setenv("OKX_BASE_URL", "https://openapi.okx.com")

    load_env(env_file)

    assert Settings.from_env().base_url == "https://openapi.okx.com"


def test_load_env_sets_missing_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OKX_SIMULATED_TRADING=1\nDATABASE_URL=postgresql://okx:secret@postgres:5432/okx_dashboard\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OKX_SIMULATED_TRADING", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    load_env(env_file)
    settings = Settings.from_env()

    assert settings.simulated_trading is True
    assert settings.default_trading_environment == "simulated"
    assert settings.database_url == "postgresql://okx:secret@postgres:5432/okx_dashboard"
    assert settings.database_label == "postgresql://okx:***@postgres:5432/okx_dashboard"


def test_database_path_falls_back_to_sqlite_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("DATABASE_PATH", "data/test.sqlite3")

    assert Settings.from_env().database_url == "sqlite:///data/test.sqlite3"


def test_account_cache_settings_have_defaults(monkeypatch):
    monkeypatch.delenv("OKX_ACCOUNT_CACHE_SECONDS", raising=False)
    monkeypatch.delenv("OKX_ACCOUNT_STALE_SECONDS", raising=False)

    settings = Settings.from_env()

    assert settings.account_cache_seconds == 20
    assert settings.account_stale_seconds == 600


def test_websocket_settings_have_public_and_private_defaults(monkeypatch):
    monkeypatch.delenv("OKX_WS_PUBLIC_URL", raising=False)
    monkeypatch.delenv("OKX_WS_DEMO_PUBLIC_URL", raising=False)
    monkeypatch.delenv("OKX_WS_BUSINESS_URL", raising=False)
    monkeypatch.delenv("OKX_WS_DEMO_BUSINESS_URL", raising=False)
    monkeypatch.delenv("OKX_WS_PRIVATE_URL", raising=False)
    monkeypatch.delenv("OKX_WS_DEMO_PRIVATE_URL", raising=False)

    settings = Settings.from_env()

    assert settings.ws_public_url_for_environment("live") == "wss://ws.okx.com/ws/v5/public"
    assert settings.ws_public_url_for_environment("simulated") == "wss://wspap.okx.com/ws/v5/public"
    assert settings.ws_business_url_for_environment("live") == "wss://ws.okx.com/ws/v5/business"
    assert settings.ws_business_url_for_environment("simulated") == "wss://wspap.okx.com/ws/v5/business"
    assert settings.ws_private_url_for_environment("live") == "wss://ws.okx.com/ws/v5/private"
    assert settings.ws_private_url_for_environment("simulated") == "wss://wspap.okx.com/ws/v5/private"


def test_environment_specific_credentials(monkeypatch):
    monkeypatch.setenv("OKX_DEMO_API_KEY", "demo-key")
    monkeypatch.setenv("OKX_DEMO_API_SECRET", "demo-secret")
    monkeypatch.setenv("OKX_DEMO_API_PASSPHRASE", "demo-pass")
    monkeypatch.setenv("OKX_LIVE_API_KEY", "live-key")
    monkeypatch.setenv("OKX_LIVE_API_SECRET", "live-secret")
    monkeypatch.setenv("OKX_LIVE_API_PASSPHRASE", "live-pass")
    monkeypatch.setenv("OKX_TRADING_ENVIRONMENT", "live")
    monkeypatch.setenv("OKX_ENABLE_LIVE_TRADING", "1")

    settings = Settings.from_env()

    assert settings.credentials_for_environment("simulated") == ("demo-key", "demo-secret", "demo-pass")
    assert settings.credentials_for_environment("live") == ("live-key", "live-secret", "live-pass")
    assert settings.default_trading_environment == "live"
    assert settings.live_trading_enabled is True


def test_legacy_credentials_are_bound_to_legacy_environment(monkeypatch):
    monkeypatch.setenv("OKX_API_KEY", "legacy-key")
    monkeypatch.setenv("OKX_API_SECRET", "legacy-secret")
    monkeypatch.setenv("OKX_API_PASSPHRASE", "legacy-pass")
    monkeypatch.setenv("OKX_SIMULATED_TRADING", "0")
    monkeypatch.setenv("OKX_DEMO_API_KEY", "")
    monkeypatch.setenv("OKX_DEMO_API_SECRET", "")
    monkeypatch.setenv("OKX_DEMO_API_PASSPHRASE", "")
    monkeypatch.setenv("OKX_LIVE_API_KEY", "")
    monkeypatch.setenv("OKX_LIVE_API_SECRET", "")
    monkeypatch.setenv("OKX_LIVE_API_PASSPHRASE", "")

    settings = Settings.from_env()

    assert settings.credentials_for_environment("live") == ("legacy-key", "legacy-secret", "legacy-pass")
    assert settings.credentials_for_environment("simulated") == ("", "", "")
