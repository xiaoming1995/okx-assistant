"""自动化交易风控规则层。

这里只放纯决策逻辑，不引用 main 模块的任何全局单例；外部依赖由编排层
以 callable 注入，因此规则可以独立单测，也不会因为 main 的 monkeypatch
或数据库状态而漂移。

设计要点：
- 开仓与平仓是两类动作，不能用同一套 allowed 判定。止盈止损是降低风险
  的动作，开仓专属的额度/冷却期/LLM 置信度限制不得阻拦它；
- 全局安全状态读取失败时必须 fail-closed，不能默认「未暂停」；
- 单次策略评估共享一份账户快照，避免风控判定与实际执行依据不一致。
"""

from __future__ import annotations

from typing import Any, Callable

OPEN_ACTIONS = frozenset({"long", "short"})
EXIT_ACTIONS = frozenset({"stop_loss", "take_profit"})

# 开仓专属限制：平仓时既不能据此拦截，也不应在风控快照里显示为「拦截」。
EXIT_SKIP_KEYS = frozenset(
    {"llm", "max_order", "max_position", "cooldown", "exit_risk", "daily_limit"}
)

# 平仓路径仍需检查的项目。冷却期、开仓额度、LLM 置信度等只约束开仓。
EXIT_BLOCK_KEYS = frozenset(
    {
        "signal",
        "execution_mode",
        "global_pause",
        "circuit_breaker",
        "global_state",
        "credentials",
        "account",
        "position",
        "exit_position",
    }
)


def classify_signal_action(action: Any) -> str:
    value = str(action or "").strip().lower()
    if value in OPEN_ACTIONS:
        return "open"
    if value in EXIT_ACTIONS:
        return "exit"
    return "observe"


def _block(key: str, label: str, message: str, value: str) -> dict[str, str]:
    return {"key": key, "label": label, "status": "block", "message": message, "value": value}


def global_block_from_state(state: dict[str, Any] | None) -> dict[str, str] | None:
    """把持久化的安全状态翻译成拦截项；状态不可读时一律按暂停处理。"""
    if not isinstance(state, dict):
        return _block("global_state", "安全状态", "无法读取自动化全局安全状态，已停止自动执行。", "未知")
    if state.get("stateAvailable") is False:
        return _block(
            "global_state",
            "安全状态",
            str(state.get("pauseReason") or "自动化全局安全状态读取失败，已按暂停处理。"),
            "未知",
        )
    if state.get("globalPaused"):
        return _block(
            "global_pause",
            "全局暂停",
            str(state.get("pauseReason") or "自动交易当前处于全局暂停状态，已停止自动执行。"),
            "已暂停",
        )
    if state.get("circuitBreakerActive"):
        return _block(
            "circuit_breaker",
            "熔断状态",
            str(state.get("circuitReason") or "自动交易已触发熔断，需人工恢复后才会继续执行。"),
            "已熔断",
        )
    return None


def decide(
    *,
    checks: list[dict[str, Any]],
    execution_mode: str,
    action_kind: str,
    execution_action: str = "none",
) -> tuple[bool, str, str]:
    """统一产出 allowed / severity / message，开仓与平仓共用一套 checks。"""
    blocking = [
        item
        for item in checks
        if item.get("status") == "block"
        and (action_kind != "exit" or str(item.get("key") or "") in EXIT_BLOCK_KEYS)
    ]
    warnings = [item for item in checks if item.get("status") == "warn"]
    allowed = (
        not blocking
        and execution_mode == "simulated_auto"
        and action_kind in {"open", "exit"}
    )
    severity = "ok" if allowed else "blocked" if blocking else "warning"

    if blocking:
        message = str(blocking[0].get("message") or "自动交易被风控拦截。")
    elif allowed and action_kind == "exit":
        message = "止盈止损已通过风控，将按持仓方向提交平仓。"
    elif allowed and execution_action == "skip_same_direction":
        message = "当前配置通过风控，但已有同向持仓，运行时会跳过重复开仓。"
    elif allowed and execution_action in {"reverse", "close_opposite"}:
        message = "当前配置通过风控，反向信号会先市价全平再开新方向。"
    elif allowed:
        message = "当前配置通过风控，可提交虚拟盘订单。"
    elif warnings:
        message = str(warnings[0].get("message") or "当前配置不会自动提交订单。")
    else:
        message = "当前配置不会自动提交订单。"
    return allowed, severity, message


class EvaluationContext:
    """单次策略评估的共享读取结果。

    风控预览、止盈止损判定、下单执行都通过它取账户/全局状态/LLM 配置，
    保证整轮评估基于同一份快照（避免 TOCTOU），也避免重复拉取 OKX 账户。
    """

    def __init__(self) -> None:
        self._global_state: dict[str, Any] | None = None
        self._llm_config: dict[str, Any] | None = None
        self._account_loaded = False
        self._account: dict[str, Any] | None = None
        self._account_error: Exception | None = None

    def global_state(self, loader: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if self._global_state is None:
            try:
                self._global_state = loader() or {}
            except Exception:
                self._global_state = {"stateAvailable": False}
        return self._global_state

    def llm_config(self, loader: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if self._llm_config is None:
            try:
                self._llm_config = loader() or {}
            except Exception:
                self._llm_config = {}
        return self._llm_config

    def account(
        self, loader: Callable[[str], dict[str, Any]]
    ) -> tuple[dict[str, Any] | None, Exception | None]:
        if not self._account_loaded:
            self._account_loaded = True
            try:
                payload = loader("simulated")
                self._account = payload if isinstance(payload, dict) else {}
            except Exception as exc:
                self._account = None
                self._account_error = exc
        return self._account, self._account_error
