"""BEEP step: sound the piezo beeper, optionally as a sequence of beeps.

Per TEST_RUNNER_PLAN.md's BEEP timing note: a silent gap of `duration_ms` separates each beep —
e.g. duration_ms=100, count=3 is beep-silence-beep-silence-beep, not three beeps back-to-back.
No trailing silence after the last beep.
"""

from __future__ import annotations

import time

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("BEEP")
def execute(config: dict, context: ExecutionContext) -> StepResult:
    duration_ms = config["duration_ms"]
    count = config.get("count", 1)
    duration_s = duration_ms / 1000

    for i in range(count):
        context.chassis.beeper.beep(duration_s)
        if i < count - 1:
            time.sleep(duration_s)

    return StepResult(passed=True, message=f"Beeped {count}x{duration_ms}ms")
