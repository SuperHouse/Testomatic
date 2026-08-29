"""LED_SPECTRAL_READING step: stub.

Deferred: a driver for the VEML3328SL colour sensor (`ColourSensor/` in this repo) already
exists elsewhere and will be wired in later, either as a `chassis.colour_sensor` subsystem in
testomatic-io or directly in this executor — not decided yet. See TEST_RUNNER_PLAN.md's
"Deferred work" section. This stub lets suites containing an LED_SPECTRAL_READING step still run
end-to-end.
"""

from __future__ import annotations

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("LED_SPECTRAL_READING")
def execute(config: dict, context: ExecutionContext) -> StepResult:
    print("LED test")
    return StepResult(passed=True, message="LED test (stub)")
