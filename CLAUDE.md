# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Testomatic is an open-source PCB test jig system: a Raspberry Pi-based hardware tester with a
custom PCB, removable "Test Modules" per device-under-test (DUT), and a touchscreen UI. This repo
is a **hardware design repo** (Fusion 360, EAGLE/KiCAD, DXF, STL) — no code lives here. The
software that drives this hardware lives in sibling repos; see Ecosystem below. Most directories
contain CAD/PCB source files:

- `Hardware/` — Testomatic main PCB (EAGLE `.brd`/`.sch`, Fusion `.f3z`/`.fbrd`/`.fsch`), versions v1.0–v2.3
- `Chassis/` — laser-cut chassis plates (`.dxf` for cutting, `.f3d` Fusion source)
- `TestModules/` — Test Pin Carrier Board (TPCB) reference design and module templates
- `ColourSensor/` — VEML3328SL sensor shrouds (Fusion/STL) for automated LED colour verification
- `Images/`, `Resources/` — photos/diagrams and datasheets/misc binaries (not code)

## Terminology

`README.md`'s **Terminology** section is the controlled vocabulary for this project (Chassis,
Design, Device, Test Module, Test Item, Test Step, Manual Check, Test Suite, Test Run, Test
Result, Register, Test Runner, plus two introduced for the artifact that carries a Test Suite
from Register to a Test Runner — **Test Suite Definition** and **Test Suite Package**, see below).
Use those terms as defined there rather than looser language like "export."

- **Test Suite Definition** — a JSON document containing a Test Suite's Test Steps and Manual
  Checks. Deliberately not "Test Suite Export": it is delivered as `test-suite-definition.json`
  inside a Test Suite Package (see below), not as a stand-alone download — a future goal is
  Testomatic discovering and fetching Test Suite Definitions from a Register API instead.
- **Test Suite Package** — a Test Suite Definition plus the additional artifacts it references
  and needs to run (e.g. firmware binaries for `UPLOAD_FIRMWARE`). Register now delivers this as a
  ZIP archive (filename pattern `{sku}-hw{hw_version}-test-suite-v{version}.zip`, its contents all
  inside one top-level folder of that same name, holding `test-suite-definition.json` plus any
  referenced files — so extracting it can never scatter loose files into whatever directory it
  lands in) — see the `testomatic-runner` repo's `test-suite-package.md` for the format. This
  supersedes the older bare-JSON download.

## Ecosystem — sibling repos, each with its own CLAUDE.md

This repo (chassis hardware design) is one part of a multi-repo system. Read the other repos'
`CLAUDE.md` files directly when working on anything that crosses a boundary — don't rely on
summaries here going stale:

- **This repo (Testomatic)** — the physical chassis/PCB/Test Module hardware only. No code.
- **`testomatic-runner`** (`~/Dropbox/src/testomatic-runner`) — the test-runner software: parses a
  Test Suite Package and executes its Test Steps in order against real hardware. Formerly lived in
  this repo's `Software/` directory; extracted into its own repo so it can depend on
  `testomatic-io` as a normal sibling package.
- **`testomatic-io`** (`~/Dropbox/src/testomatic-io`) — the Python HAL that `testomatic-runner`
  drives the chassis through. Its `Chassis`/`TestModule` facade classes (`chassis.iomod`,
  `chassis.power`, `chassis.button`, `chassis.beeper`, etc.) map directly onto the GPIO/I2C wiring
  in this repo's `PinAllocation.md` — e.g. `chassis.power.rail_5v()` against `IO27`,
  `chassis.button` against `IO20`. It only imports on real Raspberry Pi hardware (Adafruit Blinka
  does platform detection at import time).
- **Register** (`/Users/jon/Dropbox/src/register-macbook`, Django app under `pyproj/`) — the
  central production/test database. Its `testing` app defines `TestSuite`/`TestStep`/
  `ManualCheck` models, staff-edited per PCB `Design`, and currently serves a Test Suite Package
  (a ZIP containing `test-suite-definition.json`) for download, in the format documented in
  `testomatic-runner`'s `test-suite-package.md` (that file, and the sample fixture
  `aqs-hw41-test-suite-v1.zip`, both originate from Register's `docs/api/test-suite-export.md` and
  `testing.views.test_suite_download`/`_serialize_test_suite` — keep that copy in sync if the
  format changes on the Register side). Register's `testing.TestStep.STEP_TYPE_CHOICES` is the
  authoritative list of step types; it currently has placeholder choice sets
  (`POWER_RAIL_CHOICES`, `IOMOD_CHOICES`) explicitly pending fuller integration with this project.

**The intended pipeline:** a Test Suite is authored/versioned in Register against a `Design` →
conveyed to `testomatic-runner` as a Test Suite Package (today: ZIP download containing
`test-suite-definition.json`; a future goal is discovering and fetching a Test Suite Definition
directly from a Register API) → `testomatic-runner` parses it and executes each `TestStep` in
order → each step's hardware action (drive a rail, read an IOMOD pin, read the colour sensor,
etc.) is carried out via `testomatic-io`'s `Chassis`/`TestModule` API. The staged implementation
plan, including what's done vs. still pending real-hardware verification, lives in
`testomatic-runner`'s `TEST_RUNNER_PLAN.md`.

## Hardware I/O reference (`PinAllocation.md`)

Raspberry Pi GPIO assignments on the Testomatic main board — relevant when writing control code
in the sibling `testomatic-runner`/`testomatic-io` repos:

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
