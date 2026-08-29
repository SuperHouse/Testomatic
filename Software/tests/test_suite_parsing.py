"""Tests for suite.py against the sample export and hand-built envelopes."""

from __future__ import annotations

from pathlib import Path

import pytest

from testomatic.suite import SuiteFormatError, load_suite, parse_suite

FIXTURE = Path(__file__).parent.parent / "aqs-hw41-test-suite-v1" / "test-suite-definition.json"


def _envelope(**overrides) -> dict:
    envelope = {
        "export_schema_version": 1,
        "design": {"id": 1, "sku": "X", "name": "X Board", "hw_version": "1.0"},
        "test_suite": {"version": 1, "status": "DRAFT", "notes": None, "created_dt": "now"},
        "test_steps": [],
        "manual_checks": [],
    }
    envelope.update(overrides)
    return envelope


def test_loads_sample_suite_fixture():
    suite = load_suite(FIXTURE)

    assert suite.export_schema_version == 1
    assert suite.design.sku == "AQS"
    assert suite.design.hw_version == "4.1"
    assert suite.test_suite.status == "DRAFT"

    assert len(suite.test_steps) == 1
    step = suite.test_steps[0]
    assert step.step_type == "BEEP"
    assert step.config == {"duration_ms": 100, "count": 3, "schema_version": 1}

    assert len(suite.manual_checks) == 1
    assert suite.manual_checks[0].text == "Check me please"


def test_rejects_unsupported_export_schema_version():
    with pytest.raises(SuiteFormatError):
        parse_suite(_envelope(export_schema_version=99))


def test_rejects_missing_required_key():
    envelope = _envelope()
    del envelope["design"]

    with pytest.raises(SuiteFormatError):
        parse_suite(envelope)


def test_sorts_steps_and_manual_checks_by_order():
    step_a = {
        "order": 1, "step_type": "DELAY", "name": "a", "abort_on_fail": False,
        "config_schema_version": 1, "config": {"schema_version": 1, "delay_ms": 1},
    }
    step_b = {
        "order": 2, "step_type": "DELAY", "name": "b", "abort_on_fail": False,
        "config_schema_version": 1, "config": {"schema_version": 1, "delay_ms": 1},
    }
    suite = parse_suite(_envelope(
        test_steps=[step_b, step_a],
        manual_checks=[{"order": 2, "text": "second"}, {"order": 1, "text": "first"}],
    ))

    assert [step.name for step in suite.test_steps] == ["a", "b"]
    assert [check.text for check in suite.manual_checks] == ["first", "second"]


def test_rejects_config_schema_version_mismatch():
    step = {
        "order": 1, "step_type": "DELAY", "name": "a", "abort_on_fail": False,
        "config_schema_version": 2, "config": {"schema_version": 1, "delay_ms": 1},
    }

    with pytest.raises(SuiteFormatError):
        parse_suite(_envelope(test_steps=[step]))


def test_optional_notes_defaults_to_none():
    envelope = _envelope()
    del envelope["test_suite"]["notes"]

    suite = parse_suite(envelope)

    assert suite.test_suite.notes is None
