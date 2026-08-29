"""OPERATOR_INTERVENTION step: show an instruction and wait for the operator to confirm.

CLI-only for v1 (blocks on `input()`); a future touchscreen UI can replace the confirmation
mechanism later without changing this executor's signature.
"""

from __future__ import annotations

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("OPERATOR_INTERVENTION")
def execute(config: dict, context: ExecutionContext) -> StepResult:
    message = config["message"]
    print(message)
    input("Press Enter once complete...")
    return StepResult(passed=True, message=message)
