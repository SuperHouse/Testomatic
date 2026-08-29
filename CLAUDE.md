# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Testomatic is an open-source PCB test jig system: a Raspberry Pi-based hardware tester with a
custom PCB, removable "Test Modules" per device-under-test (DUT), and a touchscreen UI. This repo
is overwhelmingly a **hardware design repo** (Fusion 360, EAGLE/KiCAD, DXF, STL) with one small
Python software component. Most directories contain CAD/PCB source files, not code:

- `Hardware/` — Testomatic main PCB (EAGLE `.brd`/`.sch`, Fusion `.f3z`/`.fbrd`/`.fsch`), versions v1.0–v2.3
- `Chassis/` — laser-cut chassis plates (`.dxf` for cutting, `.f3d` Fusion source)
- `TestModules/` — Test Pin Carrier Board (TPCB) reference design and module templates
- `ColourSensor/` — VEML3328SL sensor shrouds (Fusion/STL) for automated LED colour verification
- `Images/`, `Resources/` — photos/diagrams and datasheets/misc binaries (not code)
- `Software/` — the only actual code in this repo (see below)

## Terminology

`README.md`'s **Terminology** section is the controlled vocabulary for this project (Chassis,
Design, Device, Test Module, Test Item, Test Step, Manual Check, Test Suite, Test Run, Test
Result, Register, Test Runner, plus two introduced for the artifact that carries a Test Suite
from Register to a Test Runner — **Test Suite Definition** and **Test Suite Package**, see below).
Use those terms as defined there rather than looser language like "export."

- **Test Suite Definition** — a JSON document containing a Test Suite's Test Steps and Manual
  Checks. Deliberately not "Test Suite Export": the JSON download currently in `Software/` is one
  transport for it, not the concept itself — a future goal is Testomatic discovering and fetching
  Test Suite Definitions from a Register API instead.
- **Test Suite Package** — a Test Suite Definition plus the additional artifacts it references
  and needs to run (e.g. firmware binaries for `UPLOAD_FIRMWARE`), whether delivered as one
  archive or assembled from multiple sources. Not implemented anywhere yet — this is the concept
  that `TEST_RUNNER_PLAN.md`'s `UPLOAD_FIRMWARE` gap is waiting on a design for.

## Ecosystem — three sibling repos, each with its own CLAUDE.md

This repo (chassis hardware design + eventual test-runner software) is one part of a three-repo
system. Read the other two repos' `CLAUDE.md` files directly when working on anything that
crosses a boundary — don't rely on summaries here going stale:

- **This repo (Testomatic)** — the physical chassis/PCB/Test Module hardware, plus `Software/`,
  which is meant to become the test runner that executes a Test Suite on that hardware.
- **`testomatic-io`** (`~/Dropbox/src/testomatic-io`) — the Python HAL that `Software/` is
  expected to drive the chassis through. Its `Chassis`/`TestModule` facade classes
  (`chassis.iomod`, `chassis.power`, `chassis.button`, `chassis.beeper`, etc.) map directly onto
  the GPIO/I2C wiring in this repo's `PinAllocation.md` — e.g. `chassis.power.rail_5v()` against
  `IO27`, `chassis.button` against `IO20`. It only imports on real Raspberry Pi hardware
  (Adafruit Blinka does platform detection at import time).
- **Register** (`/Users/jon/Dropbox/src/register-macbook`, Django app under `pyproj/`) — the
  central production/test database. Its `testing` app defines `TestSuite`/`TestStep`/
  `ManualCheck` models, staff-edited per PCB `Design`, and currently serves a Test Suite Definition
  as a JSON download in the format documented in `Software/test-suite-export.md` (that file, and
  the sample `Software/aqs-hw41-test-suite-v1.json`, both originate from Register's
  `docs/api/test-suite-export.md` and `testing.views.test_suite_download`/`_serialize_test_suite`
  — keep this repo's copy in sync if that format changes on the Register side). Register's
  `testing.TestStep.STEP_TYPE_CHOICES` is the authoritative list of step types; it currently has
  placeholder choice sets (`POWER_RAIL_CHOICES`, `IOMOD_CHOICES`) explicitly pending fuller
  integration with this project.

**The intended pipeline:** a Test Suite is authored/versioned in Register against a `Design` →
conveyed to this repo as a Test Suite Definition (today: JSON file download; a future goal is
Testomatic discovering and fetching one from a Register API) → a test runner in this repo's
`Software/` parses it and executes each `TestStep` in order → each step's hardware action (drive a
rail, read an IOMOD pin, read the colour sensor, etc.) is carried out via `testomatic-io`'s
`Chassis`/`TestModule` API. That runner is now partially implemented in `Software/` (see below);
the staged implementation plan, including what's done vs. still pending real-hardware
verification, lives in `Software/TEST_RUNNER_PLAN.md` — check it (and its phase checklist) before
starting runner work.

## Software/ — the Python component

`Software/` is a `testomatic` package implementing the test runner, plus its reference docs:

- `src/testomatic/suite.py` — parses/validates a Test Suite Definition (JSON) into dataclasses
  (`load_suite(path)` → `TestSuiteFile`); see `test-suite-export.md` below for the format.
- `src/testomatic/steps/` — one executor module per `step_type` (`delay.py`, `beep.py`,
  `power.py`, `iomod.py`, `python_step.py`, `operator_intervention.py`, plus the deferred stubs
  `firmware.py`/`led_spectral.py` — see `TEST_RUNNER_PLAN.md`'s "Deferred work"). Each executor is
  a plain `(config, context) -> StepResult` function registered against its `step_type` string in
  `registry.STEP_EXECUTORS` via `@register_step(...)` (`registry.py`) — dict-of-functions dispatch,
  not a class hierarchy, since (unlike `testomatic-io`'s IOMOD chip drivers) there's no runtime
  probing involved: the `step_type` is already known from the parsed JSON.
- `src/testomatic/runner.py` — `TestRunner.run(suite)` executes `test_steps` in order via the
  registry, stops and turns off all three power rails immediately if a `hard_fail` step fails
  (the one case where the runner touches rails on its own initiative — see `TEST_RUNNER_PLAN.md`),
  and returns a `RunReport`; `format_report()` renders it plus the suite's `manual_checks`.
- `src/testomatic/cli.py` / `__main__.py` — `python -m testomatic run <suite.json>` entry point.
  Only importable/runnable on real Raspberry Pi hardware (imports `testomatic_io` at call time)
  — **not yet exercised against a real chassis**.
- `tests/conftest.py` — `FakeChassis`/`FakePower`/`FakeBeeper`/`FakeIomod` doubles (as pytest
  fixtures `chassis`/`test_module`/`context`) standing in for real `testomatic-io` hardware, since
  step executors only ever duck-type against whatever `chassis` object they're given.
- `test-suite-export.md` — reference documentation (copied from the Register project) describing
  the Test Suite Definition format `suite.py` parses. (File name predates the "Test Suite
  Definition" term — see Terminology above — and hasn't been renamed to match.)
- `aqs-hw41-test-suite-v1.json` — a real sample Test Suite Definition in that format, used as a
  test fixture.
- `TEST_RUNNER_PLAN.md` — the staged implementation plan: what's done, what's stubbed pending
  design decisions, and the phase checklist. Keep it updated as phases land.

### Working here

```bash
cd Software
pip install -e ".[dev]"
pytest
```
- To run a single test: `pytest tests/test_steps.py::test_beep_alternates_beep_and_silence`
- `testomatic-io` is on PyPI but lives in the `pi` extra (`pip install -e ".[pi]"`), not core
  dependencies: it pulls in `gpiod`, whose native extension only builds on Linux — a core
  dependency broke `pip install -e ".[dev]"` outright on macOS. Install the `pi` extra on the
  Raspberry Pi itself to actually run `cli.py`; see `TEST_RUNNER_PLAN.md` for detail.

### The Test Suite Definition format (`test-suite-export.md`)

This is the key contract for any test-runner code added here. A Test Suite Definition is one JSON
object with four top-level keys: `design`, `test_suite`, `test_steps` (array, execution order),
and `manual_checks` (array). Each `test_steps` entry has a fixed outer shape
(`order`, `step_type`, `name`, `hard_fail`, `config_schema_version`, `config`) with a
`step_type`-specific `config` payload. Known step types: `DELAY`, `UPLOAD_FIRMWARE`, `BEEP`,
`READ_RAIL_VOLTAGE`, `READ_RAIL_CURRENT`, `CONTROL_POWER_RAIL`, `PYTHON`, `IOMOD_ANALOG_READ`,
`IOMOD_DIGITAL_READ`, `IOMOD_DIGITAL_WRITE`, `IOMOD_ANALOG_WRITE`, `LED_SPECTRAL_READING`,
`OPERATOR_INTERVENTION`. Optional `config` fields are omitted rather than null when unset — a
consumer must apply its own default, not expect `null`/empty. `export_schema_version` versions
the envelope shape; each step's `config_schema_version` independently versions that step type's
own config shape — don't conflate the two when adding parsing logic.

## Hardware I/O reference (`PinAllocation.md`)

Raspberry Pi GPIO assignments on the Testomatic main board — relevant when writing control code
in `Software/`:

- I2C bus 0 (IO0/IO1): HAT EEPROM, on the Testomatic main board
- I2C bus 1 (IO2/IO3): general-purpose, for Test Module peripherals
- SPI: CE0/CE1 = IO8/IO7, MISO/MOSI/SCK = IO9/IO10/IO11
- IO18: tester reset (active low)
- IO20: external button / footswitch input (active low)
- IO23: piezo buzzer (active high)
- IO24/IO25: available on the tester breakout, usable as extra SPI CE lines
- 7 GPIO blocks of 8 pins each (IOMOD A–G) are exposed via I2C I/O-expander modules
  (AD5593R-based), each pin independently configurable as digital in/out or 12-bit ADC/DAC

## Notes

- `Notes.md` and `ToDo.md` are running scratch notes (setup recipes for the Pi/kiosk display,
  webcam light-box, receipt printer, sensor libraries, open hardware TODOs) — useful background,
  not authoritative documentation.
- Licensing: hardware is under the TAPR Open Hardware License.
