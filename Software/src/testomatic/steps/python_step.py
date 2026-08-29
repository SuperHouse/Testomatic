"""PYTHON step: run operator-authored Python source against the live hardware handles.

Register validates that the code parses (`ast.parse`) when the step is authored but never
executes it — this repo's runner is the only thing that ever runs it. The Test Suite JSON a
runner loads comes from a staff-only Register export, so this trust boundary is deliberate;
still worth knowing this executor runs arbitrary code with the same privileges as the runner
process. A raised exception is treated as a failed step rather than crashing the run.
"""

from __future__ import annotations

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("PYTHON")
def execute(config: dict, context: ExecutionContext) -> StepResult:
    python_code = config["python_code"]
    namespace = {"chassis": context.chassis, "test_module": context.test_module}

    try:
        exec(python_code, namespace)  # noqa: S102 -- deliberate, see module docstring
    except Exception as exc:
        return StepResult(passed=False, message=f"Python step raised: {exc}")

    return StepResult(passed=True, message="Python step executed")
