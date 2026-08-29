"""DELAY step: pause for a fixed number of milliseconds."""

from __future__ import annotations

import time

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("DELAY")
def execute(config: dict, context: ExecutionContext) -> StepResult:
    delay_ms = config["delay_ms"]
    time.sleep(delay_ms / 1000)
    return StepResult(passed=True, message=f"Delayed {delay_ms} ms")
