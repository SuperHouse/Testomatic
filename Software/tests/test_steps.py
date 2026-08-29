"""Tests for individual step executors against the fake hardware in conftest.py."""

from __future__ import annotations

import time

from testomatic.steps import (
    beep,
    delay,
    firmware,
    iomod,
    led_spectral,
    operator_intervention,
    power,
    python_step,
)


def test_delay_sleeps_for_delay_ms(monkeypatch, context):
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    result = delay.execute({"delay_ms": 250}, context)

    assert result.passed
    assert slept == [0.25]


def test_beep_alternates_beep_and_silence(monkeypatch, context):
    events = []
    monkeypatch.setattr(time, "sleep", lambda s: events.append(("sleep", s)))
    context.chassis.beeper.beep = lambda duration_s: events.append(("beep", duration_s))

    result = beep.execute({"duration_ms": 100, "count": 3}, context)

    assert result.passed
    assert events == [
        ("beep", 0.1), ("sleep", 0.1),
        ("beep", 0.1), ("sleep", 0.1),
        ("beep", 0.1),
    ]


def test_beep_defaults_count_to_one_with_no_trailing_sleep(monkeypatch, context):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))

    result = beep.execute({"duration_ms": 50}, context)

    assert result.passed
    assert context.chassis.beeper.beeps == [0.05]
    assert sleeps == []


def test_operator_intervention_prints_message_and_waits(monkeypatch, context, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    result = operator_intervention.execute({"message": "Connect the probe"}, context)

    assert result.passed
    assert "Connect the probe" in capsys.readouterr().out


def test_python_step_runs_code_against_chassis(context):
    result = python_step.execute({"python_code": "chassis.beeper.beep(0.5)"}, context)

    assert result.passed
    assert context.chassis.beeper.beeps == [0.5]


def test_python_step_reports_failure_on_exception(context):
    result = python_step.execute({"python_code": "raise RuntimeError('boom')"}, context)

    assert not result.passed
    assert "boom" in result.message


def test_control_power_rail_turns_rail_on(context):
    result = power.execute_control({"rail": "5V", "action": "ON"}, context)

    assert result.passed
    assert context.chassis.power.rails["5v"] is True


def test_read_rail_voltage_within_range_passes(context):
    result = power.execute_read_voltage({"rail": "3.3V", "min_v": 3.0, "max_v": 3.6}, context)

    assert result.passed
    assert result.measured["voltage"] == 3.3


def test_read_rail_voltage_out_of_range_fails(context):
    result = power.execute_read_voltage({"rail": "3.3V", "min_v": 4.0, "max_v": 4.5}, context)

    assert not result.passed


def test_read_rail_current_within_range_passes(context):
    result = power.execute_read_current({"rail": "5V", "min_ma": 150.0, "max_ma": 250.0}, context)

    assert result.passed
    assert result.measured["current"] == 200.0


def test_iomod_digital_write_then_read_roundtrip(context):
    write_result = iomod.execute_digital_write(
        {"iomod": "C", "pin": "4", "digital_write": "1"}, context
    )
    assert write_result.passed

    read_result = iomod.execute_digital_read({"iomod": "C", "pin": "4", "expect": "1"}, context)
    assert read_result.passed


def test_iomod_digital_read_mismatch_fails(context):
    result = iomod.execute_digital_read({"iomod": "C", "pin": "4", "expect": "1"}, context)

    assert not result.passed


def test_iomod_analog_read_checks_range(context):
    context.chassis.iomod.analog[("B", 3)] = 2048

    result = iomod.execute_analog_read(
        {"iomod": "B", "pin": "3", "expect_min": 1000, "expect_max": 3000}, context
    )

    assert result.passed
    assert result.measured["value"] == 2048


def test_iomod_analog_write_records_value(context):
    result = iomod.execute_analog_write({"iomod": "B", "pin": "3", "analog_write": 1500}, context)

    assert result.passed
    assert context.chassis.iomod.analog[("B", 3)] == 1500


def test_firmware_upload_stub_prints_and_passes(context, capsys):
    result = firmware.execute({}, context)

    assert result.passed
    assert "Firmware upload" in capsys.readouterr().out


def test_led_spectral_reading_stub_prints_and_passes(context, capsys):
    result = led_spectral.execute({}, context)

    assert result.passed
    assert "LED test" in capsys.readouterr().out
