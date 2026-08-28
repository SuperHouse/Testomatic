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
  `ManualCheck` models, staff-edited per PCB `Design`, and exports them as the Test Suite JSON
  format documented in `Software/test-suite-export.md` (that file, and the sample
  `Software/aqs-hw41-test-suite-v1.json`, both originate from Register's
  `docs/api/test-suite-export.md` and `testing.views.test_suite_download`/`_serialize_test_suite`
  — keep this repo's copy in sync if that format changes on the Register side). Register's
  `testing.TestStep.STEP_TYPE_CHOICES` is the authoritative list of step types; it currently has
  placeholder choice sets (`POWER_RAIL_CHOICES`, `IOMOD_CHOICES`) explicitly pending fuller
  integration with this project.

**The intended pipeline:** a Test Suite is authored/versioned in Register against a `Design` →
downloaded/served as the JSON format above → a test runner in this repo's `Software/` parses it
and executes each `TestStep` in order → each step's hardware action (drive a rail, read an IOMOD
pin, read the colour sensor, etc.) is carried out via `testomatic-io`'s `Chassis`/`TestModule`
API. None of that runner exists yet — `Software/` today is just the scaffold plus the format
reference (see below). The staged implementation plan for the runner lives in
`Software/TEST_RUNNER_PLAN.md` — check it (and its phase checklist) before starting runner work.

## Software/ — the Python component

`Software/` is an early-stage scaffold, not yet a working test runner:

- `src/testomatic/__init__.py` — empty package (just a docstring)
- `tests/test_testomatic.py` — a single smoke test that the package imports
- `pyproject.toml` — project metadata only; **no `[build-system]`, no dependencies, no tool
  config (pytest/ruff/etc.) declared yet**
- `test-suite-export.md` — reference documentation (copied from the Register project) describing
  the Test Suite JSON export format that a "Testomatic tester" is expected to read
- `aqs-hw41-test-suite-v1.json` — a real sample export in that format, useful as test fixture data
- `TEST_RUNNER_PLAN.md` — the staged implementation plan (draft, not started) for the test runner
  described above: package layout, step-type → `testomatic-io` mapping, known gaps
  (`LED_SPECTRAL_READING`, `UPLOAD_FIRMWARE`), and a phase checklist

### Working here

- There's no build backend or lockfile yet, so `pip install -e .` won't work until
  `[build-system]` is added. Run tests directly instead:
  ```
  cd Software
  pip install pytest
  python -m pytest tests/
  ```
- To run a single test: `python -m pytest tests/test_testomatic.py::test_import`

### The Test Suite JSON format (`test-suite-export.md`)

This is the key contract for any test-runner code added here. A Test Suite export is one JSON
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
