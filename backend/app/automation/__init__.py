"""自动化交易服务层：风控规则与执行闸门。"""

from .guard import (
    AutomationExecutionError,
    ExecutionGuard,
    client_order_id_for_execution,
    execution_key,
)
from .risk import (
    EXIT_SKIP_KEYS,
    EvaluationContext,
    classify_signal_action,
    decide,
    global_block_from_state,
)

__all__ = [
    "EXIT_SKIP_KEYS",
    "AutomationExecutionError",
    "EvaluationContext",
    "ExecutionGuard",
    "classify_signal_action",
    "client_order_id_for_execution",
    "decide",
    "execution_key",
    "global_block_from_state",
]
