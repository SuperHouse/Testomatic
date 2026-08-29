"""Tests for TestRunner orchestration, including abort-on-fail power shutoff."""

from __future__ import annotations

from testomatic.runner import TestRunner
from testomatic.suite import Design, TestStep, TestSuiteFile, TestSuiteMeta


def make_suite(steps):
    return TestSuiteFile(
        export_schema_version=1,
        design=Design(id=1, sku="X", name="X", hw_version="1"),
        test_suite=TestSuiteMeta(version=1, status="DRAFT", notes=None, created_dt="now"),
        test_steps=steps,
        manual_checks=[],
    )


def make_step(order, step_type, config, abort_on_fail=False, name=None):
    return TestStep(
        order=order,
        step_type=step_type,
        name=name or step_type,
        abort_on_fail=abort_on_fail,
        config_schema_version=1,
        config=config,
    )


def test_runs_all_steps_when_nothing_fails(chassis, test_module):
    runner = TestRunner(chassis, test_module)
    suite = make_suite([
        make_step(1, "DELAY", {"delay_ms": 0}),
        make_step(2, "BEEP", {"duration_ms": 1, "count": 1}),
    ])

    report = runner.run(suite)

    assert report.passed
    assert not report.aborted
    assert len(report.outcomes) == 2


def test_abort_on_fail_stops_run_and_turns_off_all_rails(chassis, test_module):
    chassis.power.rails = {"3v3": True, "5v": True, "12v": True}
    runner = TestRunner(chassis, test_module)
    suite = make_suite([
        make_step(
            1, "READ_RAIL_VOLTAGE", {"rail": "5V", "min_v": 100.0, "max_v": 200.0},
            abort_on_fail=True,
        ),
        make_step(2, "DELAY", {"delay_ms": 0}),
    ])

    report = runner.run(suite)

    assert not report.passed
    assert report.aborted
    assert len(report.outcomes) == 1
    assert chassis.power.rails == {"3v3": False, "5v": False, "12v": False}


def test_soft_fail_continues_run(chassis, test_module):
    runner = TestRunner(chassis, test_module)
    suite = make_suite([
        make_step(
            1, "READ_RAIL_VOLTAGE", {"rail": "5V", "min_v": 100.0, "max_v": 200.0},
            abort_on_fail=False,
        ),
        make_step(2, "DELAY", {"delay_ms": 0}),
    ])

    report = runner.run(suite)

    assert not report.passed
    assert not report.aborted
    assert len(report.outcomes) == 2


def test_unknown_step_type_fails_without_crashing(chassis, test_module):
    runner = TestRunner(chassis, test_module)
    suite = make_suite([make_step(1, "NOT_A_REAL_TYPE", {})])

    report = runner.run(suite)

    assert not report.passed
    assert not report.outcomes[0].result.passed
