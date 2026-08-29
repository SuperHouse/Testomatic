"""Shared pytest fixtures: fake hardware doubles standing in for real testomatic-io hardware.

testomatic-io only imports on real Raspberry Pi hardware (Adafruit Blinka does platform
detection at import time), so these are hand-rolled objects matching its public API shape
(`Chassis.power`/`.beeper`/`.iomod`) rather than an import of the real package.
"""

from __future__ import annotations

from collections import namedtuple

import pytest

from testomatic.steps.base import ExecutionContext

PowerReading = namedtuple("PowerReading", ["voltage", "current", "power"])


class FakePower:
    def __init__(self):
        self.rails = {"3v3": False, "5v": False, "12v": False}
        self.readings = {
            "3v3": PowerReading(3.3, 100.0, 330.0),
            "5v": PowerReading(5.0, 200.0, 1000.0),
            "12v": PowerReading(12.0, 50.0, 600.0),
        }

    def rail_3v3(self, on):
        self.rails["3v3"] = on

    def rail_5v(self, on):
        self.rails["5v"] = on

    def rail_12v(self, on):
        self.rails["12v"] = on

    def read_3v3(self):
        return self.readings["3v3"]

    def read_5v(self):
        return self.readings["5v"]

    def read_12v(self):
        return self.readings["12v"]


class FakeBeeper:
    def __init__(self):
        self.beeps = []

    def beep(self, duration_s):
        self.beeps.append(duration_s)


class FakeIomod:
    def __init__(self):
        self.digital = {}
        self.analog = {}

    def digital_read(self, module_id, pin):
        return self.digital.get((module_id, pin), False)

    def digital_write(self, module_id, pin, value):
        self.digital[(module_id, pin)] = value

    def analog_read(self, module_id, pin, average=1):
        return self.analog.get((module_id, pin), 0)

    def analog_write(self, module_id, pin, value):
        self.analog[(module_id, pin)] = value


class FakeChassis:
    def __init__(self):
        self.power = FakePower()
        self.beeper = FakeBeeper()
        self.iomod = FakeIomod()


class FakeTestModule:
    pass


@pytest.fixture
def chassis():
    return FakeChassis()


@pytest.fixture
def test_module():
    return FakeTestModule()


@pytest.fixture
def context(chassis, test_module):
    return ExecutionContext(chassis=chassis, test_module=test_module)
