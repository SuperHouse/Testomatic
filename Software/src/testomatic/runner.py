"""Executes a parsed Test Suite's steps against real hardware."""

from __future__ import annotations

from dataclasses import dataclass, field

from .steps import ExecutionContext, StepResult, get_executor
from .suite import ManualCheck, TestStep, TestSuiteFile


@dataclass
class StepOutcome:
    step: TestStep
    result: StepResult


@dataclass
class RunReport:
    outcomes: list[StepOutcome] = field(default_factory=list)
    aborted: bool = False

    @property
    def passed(self) -> bool:
        return not self.aborted and all(outcome.result.passed for outcome in self.outcomes)


class TestRunner:
    def __init__(self, chassis, test_module=None):
        self.context = ExecutionContext(chassis=chassis, test_module=test_module)

    def run(self, suite: TestSuiteFile) -> RunReport:
        report = RunReport()

        for step in suite.test_steps:
            result = self._run_step(step)
            report.outcomes.append(StepOutcome(step=step, result=result))

            if not result.passed and step.hard_fail:
                self._all_rails_off()
                report.aborted = True
                break

        return report

    def _run_step(self, step: TestStep) -> StepResult:
        try:
            executor = get_executor(step.step_type)
        except KeyError as exc:
            return StepResult(passed=False, message=str(exc))

        try:
            return executor(step.config, self.context)
        except Exception as exc:  # a bug in one step's executor must not crash the whole run
            return StepResult(passed=False, message=f"{step.step_type} raised: {exc}")

    def _all_rails_off(self) -> None:
        """Safety shutdown on hard-fail: turn off all three power rails unconditionally,
        regardless of what the runner believes their current state to be.
        """
        power = self.context.chassis.power
        power.rail_3v3(False)
        power.rail_5v(False)
        power.rail_12v(False)


def format_report(report: RunReport, manual_checks: list[ManualCheck]) -> str:
    lines = []

    for outcome in report.outcomes:
        status = "PASS" if outcome.result.passed else "FAIL"
        lines.append(f"[{status}] {outcome.step.name}: {outcome.result.message}")

    if report.aborted:
        lines.append("ABORTED: hard-fail step failed, all power rails turned off")

    lines.append("")
    lines.append(f"Result: {'PASS' if report.passed else 'FAIL'}")

    if manual_checks:
        lines.append("")
        lines.append("Manual checks (perform by hand):")
        for check in manual_checks:
            lines.append(f"  [ ] {check.text}")

    return "\n".join(lines)
