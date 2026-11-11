from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def load_env(path: str | os.PathLike[str] = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _environment_env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip().lower()
    return value if value in {"simulated", "live"} else default


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_secret: str
    passphrase: str
    demo_api_key: str
    demo_api_secret: str
    demo_passphrase: str
    live_api_key: str
    live_api_secret: str
    live_passphrase: str
    base_url: str
    ws_public_url: str
    simulated_trading: bool
    default_trading_environment: str
    live_trading_enabled: bool
    timeout_seconds: float
    database_url: str
    ticker_cache_seconds: float
    ticker_stale_seconds: float
    account_cache_seconds: float
    account_stale_seconds: float
    ws_demo_public_url: str = "wss://wspap.okx.com/ws/v5/public"
    ws_business_url: str = "wss://ws.okx.com/ws/v5/business"
    ws_demo_business_url: str = "wss://wspap.okx.com/ws/v5/business"
    ws_private_url: str = "wss://ws.okx.com/ws/v5/private"
    ws_demo_private_url: str = "wss://wspap.okx.com/ws/v5/private"

    @classmethod
    def from_env(cls) -> "Settings":
        load_env()
        return cls(
            api_key=os.getenv("OKX_API_KEY", ""),
            api_secret=os.getenv("OKX_API_SECRET", ""),
            passphrase=os.getenv("OKX_API_PASSPHRASE", ""),
            demo_api_key=os.getenv("OKX_DEMO_API_KEY", ""),
            demo_api_secret=os.getenv("OKX_DEMO_API_SECRET", ""),
            demo_passphrase=os.getenv("OKX_DEMO_API_PASSPHRASE", ""),
            live_api_key=os.getenv("OKX_LIVE_API_KEY", ""),
            live_api_secret=os.getenv("OKX_LIVE_API_SECRET", ""),
            live_passphrase=os.getenv("OKX_LIVE_API_PASSPHRASE", ""),
            base_url=os.getenv("OKX_BASE_URL", "https://openapi.okx.com").rstrip("/"),
            ws_public_url=os.getenv("OKX_WS_PUBLIC_URL", "wss://ws.okx.com/ws/v5/public"),
            ws_demo_public_url=os.getenv("OKX_WS_DEMO_PUBLIC_URL", "wss://wspap.okx.com/ws/v5/public"),
            ws_business_url=os.getenv("OKX_WS_BUSINESS_URL", "wss://ws.okx.com/ws/v5/business"),
            ws_demo_business_url=os.getenv(
                "OKX_WS_DEMO_BUSINESS_URL", "wss://wspap.okx.com/ws/v5/business"
            ),
            ws_private_url=os.getenv("OKX_WS_PRIVATE_URL", "wss://ws.okx.com/ws/v5/private"),
            ws_demo_private_url=os.getenv("OKX_WS_DEMO_PRIVATE_URL", "wss://wspap.okx.com/ws/v5/private"),
            simulated_trading=_bool_env("OKX_SIMULATED_TRADING", False),
            default_trading_environment=_environment_env(
                "OKX_TRADING_ENVIRONMENT",
                "simulated" if _bool_env("OKX_SIMULATED_TRADING", False) else "live",
            ),
            live_trading_enabled=_bool_env("OKX_ENABLE_LIVE_TRADING", False),
            timeout_seconds=float(os.getenv("OKX_TIMEOUT_SECONDS", "10")),
            database_url=os.getenv("DATABASE_URL")
            or f"sqlite:///{os.getenv('DATABASE_PATH', 'data/okx_dashboard.sqlite3')}",
            ticker_cache_seconds=float(os.getenv("OKX_TICKER_CACHE_SECONDS", "15")),
            ticker_stale_seconds=float(os.getenv("OKX_TICKER_STALE_SECONDS", "300")),
            account_cache_seconds=float(os.getenv("OKX_ACCOUNT_CACHE_SECONDS", "20")),
            account_stale_seconds=float(os.getenv("OKX_ACCOUNT_STALE_SECONDS", "600")),
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.api_secret and self.passphrase)

    def credentials_for_environment(self, environment: str) -> tuple[str, str, str]:
        if environment == "simulated":
            specific = (self.demo_api_key, self.demo_api_secret, self.demo_passphrase)
            if all(specific):
                return specific
            if self.simulated_trading:
                return (self.api_key, self.api_secret, self.passphrase)
            return ("", "", "")

        specific = (self.live_api_key, self.live_api_secret, self.live_passphrase)
        if all(specific):
            return specific
        if not self.simulated_trading:
            return (self.api_key, self.api_secret, self.passphrase)
        return ("", "", "")

    def has_credentials_for_environment(self, environment: str) -> bool:
        return all(self.credentials_for_environment(environment))

    def ws_public_url_for_environment(self, environment: str) -> str:
        return self.ws_demo_public_url if environment == "simulated" else self.ws_public_url

    def ws_business_url_for_environment(self, environment: str) -> str:
        return self.ws_demo_business_url if environment == "simulated" else self.ws_business_url

    def ws_private_url_for_environment(self, environment: str) -> str:
        return self.ws_demo_private_url if environment == "simulated" else self.ws_private_url

    def for_environment(self, environment: str) -> "Settings":
        api_key, api_secret, passphrase = self.credentials_for_environment(environment)
        return replace(
            self,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            simulated_trading=environment == "simulated",
        )

    def require_credentials(self) -> None:
        if not self.has_credentials:
            raise ValueError("当前交易环境未配置 OKX API Key")

    @property
    def database_label(self) -> str:
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.removeprefix("sqlite:///")
        parsed = urlsplit(self.database_url)
        if not parsed.password:
            return self.database_url
        username = parsed.username or ""
        host = parsed.hostname or ""
        netloc = f"{username}:***@{host}"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
