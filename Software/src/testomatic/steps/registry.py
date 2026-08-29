"""Registry mapping a Test Step's `step_type` to the callable that executes it.

Mirrors the driver-registry pattern testomatic-io uses for IOMOD expander chips (`DRIVERS` +
`probe()` in `testomatic_io/iomod/drivers/__init__.py`), adapted for dispatch by a known key
(`step_type`, already present in the parsed Test Step) rather than runtime hardware probing —
so this is a plain dict of functions rather than a class hierarchy with an auto-detection step.
"""

from __future__ import annotations

from typing import Callable

from .base import ExecutionContext, StepResult

StepExecutor = Callable[[dict, ExecutionContext], StepResult]

STEP_EXECUTORS: dict[str, StepExecutor] = {}


def register_step(step_type: str) -> Callable[[StepExecutor], StepExecutor]:
    """Decorator registering the wrapped function as the executor for `step_type`."""

    def decorator(executor: StepExecutor) -> StepExecutor:
        if step_type in STEP_EXECUTORS:
            raise ValueError(f"Step type {step_type!r} is already registered")
        STEP_EXECUTORS[step_type] = executor
        return executor

    return decorator


def get_executor(step_type: str) -> StepExecutor:
    try:
        return STEP_EXECUTORS[step_type]
    except KeyError as exc:
        raise KeyError(f"No executor registered for step type {step_type!r}") from exc
