"""Command-line entry point: `python -m testomatic run <suite.json>`.

Not yet run against real hardware — see TEST_RUNNER_PLAN.md.
"""

from __future__ import annotations

import argparse

from .runner import TestRunner, format_report
from .suite import load_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="testomatic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute a Test Suite JSON file")
    run_parser.add_argument("suite_path", help="Path to a Test Suite JSON export")

    args = parser.parse_args(argv)

    if args.command == "run":
        return _run(args.suite_path)

    return 1


def _run(suite_path: str) -> int:
    from testomatic_io import Chassis, TestModule  # imported here: only importable on real hardware

    suite = load_suite(suite_path)

    chassis = Chassis()
    chassis.init()
    test_module = TestModule()
    test_module.init()

    runner = TestRunner(chassis, test_module)
    report = runner.run(suite)

    print(format_report(report, suite.manual_checks))

    return 0 if report.passed else 1
