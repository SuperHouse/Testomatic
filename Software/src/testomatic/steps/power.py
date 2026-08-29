"""CONTROL_POWER_RAIL / READ_RAIL_VOLTAGE / READ_RAIL_CURRENT steps: drive and read the
3.3V/5V/12V power rails via `chassis.power`.

The runner only ever touches a rail because a Test Suite's own CONTROL_POWER_RAIL step told it
to — see TEST_RUNNER_PLAN.md's "Power rail control is Test-Suite-only" note. The one exception,
turning every rail off on an abort-on-fail, lives in `runner.py`, not here.
"""

from __future__ import annotations

from .base import ExecutionContext, StepResult
from .registry import register_step

_RAIL_CONTROL = {
    "3.3V": "rail_3v3",
    "5V": "rail_5v",
    "12V": "rail_12v",
}

_RAIL_READ = {
    "3.3V": "read_3v3",
    "5V": "read_5v",
    "12V": "read_12v",
}


@register_step("CONTROL_POWER_RAIL")
def execute_control(config: dict, context: ExecutionContext) -> StepResult:
    rail = config["rail"]
    action = config["action"]
    getattr(context.chassis.power, _RAIL_CONTROL[rail])(action == "ON")
    return StepResult(passed=True, message=f"{rail} rail {action}")


@register_step("READ_RAIL_VOLTAGE")
def execute_read_voltage(config: dict, context: ExecutionContext) -> StepResult:
    rail = config["rail"]
    min_v = config["min_v"]
    max_v = config["max_v"]
    reading = getattr(context.chassis.power, _RAIL_READ[rail])()
    passed = min_v <= reading.voltage <= max_v
    message = f"{rail} rail: {reading.voltage:.3f}V (expected {min_v}-{max_v}V)"
    return StepResult(passed=passed, message=message, measured={"voltage": reading.voltage})


@register_step("READ_RAIL_CURRENT")
def execute_read_current(config: dict, context: ExecutionContext) -> StepResult:
    rail = config["rail"]
    min_ma = config["min_ma"]
    max_ma = config["max_ma"]
    reading = getattr(context.chassis.power, _RAIL_READ[rail])()
    passed = min_ma <= reading.current <= max_ma
    message = f"{rail} rail: {reading.current:.1f}mA (expected {min_ma}-{max_ma}mA)"
    return StepResult(passed=passed, message=message, measured={"current": reading.current})
