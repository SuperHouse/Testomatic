"""UPLOAD_FIRMWARE step: stub.

Deferred: the design for associating firmware files with Test Suites isn't settled (the JSON
only carries a `firmware_file` name, not the binary), and upload-tool dispatch
(avrdude/esptool.py/openocd/stm32cubeprogrammer) is a moderately complex piece of work on its
own. See TEST_RUNNER_PLAN.md's "Deferred work" section. This stub lets suites containing an
UPLOAD_FIRMWARE step still run end-to-end.
"""

from __future__ import annotations

from .base import ExecutionContext, StepResult
from .registry import register_step


@register_step("UPLOAD_FIRMWARE")
def execute(config: dict, context: ExecutionContext) -> StepResult:
    print("Firmware upload")
    return StepResult(passed=True, message="Firmware upload (stub)")
