"""IOMOD_* steps: digital/analog I/O on IOMOD expander module pins via `chassis.iomod`."""

from __future__ import annotations

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("IOMOD_DIGITAL_READ")
def execute_digital_read(config: dict, context: ExecutionContext) -> StepResult:
    iomod = config["iomod"]
    pin = int(config["pin"])
    expect = config["expect"]

    value = context.chassis.iomod.digital_read(iomod, pin)
    actual = "1" if value else "0"
    passed = actual == expect

    return StepResult(
        passed=passed,
        message=f"IOMOD {iomod} pin {pin}: read {actual}, expected {expect}",
        measured={"value": actual},
    )


@register_step("IOMOD_DIGITAL_WRITE")
def execute_digital_write(config: dict, context: ExecutionContext) -> StepResult:
    iomod = config["iomod"]
    pin = int(config["pin"])
    value = config["digital_write"]

    context.chassis.iomod.digital_write(iomod, pin, value == "1")

    return StepResult(passed=True, message=f"IOMOD {iomod} pin {pin}: wrote {value}")


@register_step("IOMOD_ANALOG_READ")
def execute_analog_read(config: dict, context: ExecutionContext) -> StepResult:
    iomod = config["iomod"]
    pin = int(config["pin"])
    expect_min = config.get("expect_min")
    expect_max = config.get("expect_max")

    value = context.chassis.iomod.analog_read(iomod, pin)

    passed = True
    if expect_min is not None:
        passed = passed and value >= expect_min
    if expect_max is not None:
        passed = passed and value <= expect_max

    return StepResult(
        passed=passed,
        message=f"IOMOD {iomod} pin {pin}: read {value}",
        measured={"value": value},
    )


@register_step("IOMOD_ANALOG_WRITE")
def execute_analog_write(config: dict, context: ExecutionContext) -> StepResult:
    iomod = config["iomod"]
    pin = int(config["pin"])
    value = config["analog_write"]

    context.chassis.iomod.analog_write(iomod, pin, value)

    return StepResult(passed=True, message=f"IOMOD {iomod} pin {pin}: wrote {value}")
