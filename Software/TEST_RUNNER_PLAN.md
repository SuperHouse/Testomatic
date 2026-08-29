# Test Runner — Implementation Plan

Status: Phases 1, 2 and 4 implemented and unit-tested (against fake hardware, see Testing below).
Phase 3's code is written and unit-tested the same way; `cli.py` has now been run against a real
chassis and confirmed working for `BEEP` and `READ_RAIL_VOLTAGE`, but the rest of Phase 3
(`CONTROL_POWER_RAIL`, `READ_RAIL_CURRENT`, both `IOMOD_*` step types) is **still unverified on
real hardware**. Phases 5/6 remain deferred stubs. Staged implementation — check off phases as
they land.

## Scope for v1

Parse a Test Suite Definition (the `test-suite-definition.json` inside a Test Suite Package —
format documented in [test-suite-package.md](test-suite-package.md)) and execute its `test_steps`
in order against real hardware via `testomatic-io` (`~/Dropbox/src/testomatic-io`), respecting
`abort_on_fail`, and print a pass/fail report. `manual_checks` are surfaced to the operator, not
executed. Firmware upload and the colour-sensor step are stubbed for now (see below) —
everything else maps cleanly onto `testomatic-io`'s existing API.

`suite.py`'s `load_suite()` accepts either a Test Suite Package `.zip` or a bare Test Suite
Definition JSON file — dispatched on the path's extension. For a `.zip`, it locates
`test-suite-definition.json` by filename suffix (it sits inside a top-level folder named after the
package, not at the archive root — see `test-suite-package.md`) rather than assuming a fixed path,
so it doesn't care whether the wrapping folder name matches the archive's own name. `cli.py`'s
`run` command accepts either form the same way, since it just forwards its argument to
`load_suite()`. **Still not handled**: resolving other files a step might reference from inside
the package (e.g. `UPLOAD_FIRMWARE`'s `firmware_file`) — that's tied up with the deferred
`UPLOAD_FIRMWARE` work below, not with loading the suite itself.

## Package layout

Build inside the `testomatic` package already scaffolded under `src/` rather than inventing a new
top-level name:

```
Software/
  pyproject.toml          # [build-system] + dev extra (pytest) — done. testomatic-io is a `pi`
                           # extra, not a core dependency, see pyproject.toml changes below
  src/testomatic/
    suite.py              # dataclasses + parsing/validation for the JSON envelope — done
    steps/
      base.py             # StepResult + ExecutionContext dataclasses — done
      registry.py          # STEP_EXECUTORS: dict[str, StepExecutor] + @register_step — done
      delay.py, beep.py, power.py, iomod.py, python_step.py, operator_intervention.py  # done
      firmware.py           # stub for now — see Deferred work below — done
      led_spectral.py       # stub for now — see Deferred work below — done
    runner.py              # TestRunner: iterate steps, call executor, honour abort_on_fail, build report — done
    cli.py                 # entry point, `python -m testomatic run suite.zip|suite.json` — done,
                             # confirmed working on real hardware for BEEP/READ_RAIL_VOLTAGE
    __main__.py             # `python -m testomatic` dispatch — done
  tests/
    conftest.py             # FakePower/FakeBeeper/FakeIomod/FakeChassis fixtures — done
    test_suite_parsing.py  # exercises aqs-hw41-test-suite-v1/test-suite-definition.json as a fixture — done
    test_steps.py           # one test module per executor, against the fake hardware — done
    test_runner.py          # abort-on-fail/soft-fail/unknown-step-type orchestration — done
```

`steps/registry.py` mirrors the driver-registry pattern `testomatic-io` already uses for IOMOD
chips (`DRIVERS` + `probe()` in `testomatic_io/iomod/drivers/__init__.py`), adapted for dispatch
by a known key (`step_type`) rather than runtime probing — so it's a dict of plain functions
(`STEP_EXECUTORS: dict[str, StepExecutor]`), not a class hierarchy. The original idea of a
`StepExecutor` ABC was dropped since there's no per-executor state or polymorphic instantiation
to justify a class — every executor is a stateless `(config, context) -> StepResult` function.
`operator.py` was renamed `operator_intervention.py` to avoid shadowing the stdlib `operator`
module.

## Step type → `testomatic-io` mapping

| `step_type` | Executor calls |
|---|---|
| `DELAY` | `time.sleep(delay_ms / 1000)` |
| `BEEP` | see BEEP timing below — not a plain repeated `beep()` call |
| `CONTROL_POWER_RAIL` | dispatch `rail` (`3.3V`/`5V`/`12V`) → `chassis.power.rail_3v3/5v/12v(action == 'ON')` |
| `READ_RAIL_VOLTAGE` | `chassis.power.read_<rail>().voltage`, check `min_v`/`max_v` |
| `READ_RAIL_CURRENT` | `chassis.power.read_<rail>().current`, check `min_ma`/`max_ma` |
| `IOMOD_DIGITAL_READ` / `_WRITE` | `chassis.iomod.digital_read/write(iomod, pin, ...)` |
| `IOMOD_ANALOG_READ` / `_WRITE` | `chassis.iomod.analog_read/write(iomod, pin, ...)` |
| `OPERATOR_INTERVENTION` | print `message`, block on operator confirmation (CLI `input()` for v1) |
| `PYTHON` | `exec()` the code string with `chassis`/`test_module` bound in its namespace |
| `UPLOAD_FIRMWARE` | stub for now — prints `"Firmware upload"` and returns a pass. See Deferred work below |
| `LED_SPECTRAL_READING` | stub for now — prints `"LED test"` and returns a pass. See Deferred work below |

### BEEP timing

`BEEP` inserts a silent gap of `duration_ms` between each beep, not just `count` back-to-back
beeps — e.g. `duration_ms=100, count=3` is beep 100ms, silence 100ms, beep 100ms, silence 100ms,
beep 100ms (silence only *between* beeps, none trailing after the last one). Implementation:
alternate `chassis.beeper.beep(duration_ms / 1000)` and `time.sleep(duration_ms / 1000)` for
`count` beeps, skipping the trailing sleep after the last one.

### Power rail control is Test-Suite-only, with one safety exception

The runner must never turn a power rail on/off itself outside of an explicit `CONTROL_POWER_RAIL`
step — rail state is entirely the Test Suite's responsibility, and step ordering already encodes
whatever preconditions a `READ_RAIL_VOLTAGE`/`READ_RAIL_CURRENT` step needs (e.g. an earlier
`CONTROL_POWER_RAIL` step having turned that rail on) — the runner doesn't need to enforce that
itself.

**Exception:** on an abort-on-fail (a step with `abort_on_fail: true` fails), the runner must immediately
turn off all three rails — `chassis.power.rail_3v3(False)`, `rail_5v(False)`, `rail_12v(False)` —
before stopping, regardless of what the runner believes their current state to be and regardless
of what step is executing. This is a safety measure (protecting the DUT/chassis on abort), not
part of normal step execution, so it belongs in `runner.py`'s abort-on-fail handling, not in
`power.py`'s `CONTROL_POWER_RAIL` executor.

## Deferred work (stubbed for v1)

1. **`LED_SPECTRAL_READING`** needs the VEML3328SL colour sensor (`ColourSensor/` in this repo),
   reached through an I2C address plus an optional mux channel/address. `testomatic-io`'s
   `Chassis` facade has no colour-sensor subsystem yet — only `iomod`, `power`, `interrupts`,
   `button`, `beeper`, `hat_eeprom`. A driver for this sensor already exists elsewhere and will be
   wired in later, either as a `chassis.colour_sensor` subsystem in `testomatic-io` (consistent
   with how it wraps INA260/EEPROM via `i2c_probe.py`) or directly in this executor — not decided
   yet. **For now**, `steps/led_spectral.py` is a stub that just prints `"LED test"` and returns a
   pass `StepResult`, so suites containing this step type can still run end-to-end.
2. **`UPLOAD_FIRMWARE`** — the JSON only carries a `firmware_file` name, not the binary itself.
   Register doesn't currently attach firmware bytes to a Test Suite export (only a `DesignAsset`
   of type `FIRMWARE` on the Design, separately), and the design for associating firmware files
   with Test Suites more generally isn't settled. This is a moderately complex piece of work on
   its own (tool dispatch, port selection, file resolution) and is deferred. **For now**,
   `steps/firmware.py` is a stub that just prints `"Firmware upload"` and returns a pass
   `StepResult`.

## Runner semantics

- `TestRunner.run(suite, chassis, test_module)` executes steps by `order`, collecting a
  `StepResult` per step.
- On a step result of failure: if `abort_on_fail` is `True`, turn off all three power rails (see
  Power rail control above) and stop immediately; otherwise continue and record the failure.
- `config_schema_version` should be checked per step (`== 1` for now) so a future format change
  fails loudly instead of misreading fields — matches the guidance in `test-suite-package.md` about
  not conflating it with `export_schema_version`.
- Optional `config` fields: apply the documented defaults (e.g. `BEEP.count` defaults to `1` when
  absent) rather than assuming `null`.
- End-of-run: print a summary (step name, pass/fail, measured value where relevant) and list
  `manual_checks` for the operator to work through by hand.

## Testing without a Pi

Implemented more simply than originally planned: step executors never import `testomatic_io`
themselves — they only call methods on whatever `chassis`/`test_module` object `runner.py` was
given, via plain duck typing. So instead of stubbing `board`/`tca9548a`/`gpiod`/`busio` in
`sys.modules` before importing the real package, `tests/conftest.py` defines hand-rolled
`FakeChassis`/`FakePower`/`FakeBeeper`/`FakeIomod`/`FakeTestModule` classes matching
`testomatic-io`'s public API shape, exposed as pytest fixtures (`chassis`, `test_module`,
`context`). That stubbing approach is still exactly what `cli.py` will need when it's actually
exercised on the Pi (its `from testomatic_io import Chassis, TestModule` only succeeds on real
hardware — see the `pi` extra note below, it's not just an import-time platform check, the
package can't even be *installed* on macOS) — just not needed for unit-testing the
runner/executors themselves.
`suite.py`'s JSON parsing/validation needs no stubbing at all — tested directly against both the
extracted `aqs-hw41-test-suite-v1/test-suite-definition.json` and the packaged
`aqs-hw41-test-suite-v1.zip`.

## `pyproject.toml` changes made

- `[build-system]` (setuptools, src layout) — done
- `pytest` as a dev extra (`pip install -e ".[dev]"`) — done
- `python_classes = ["*Tests"]` under `[tool.pytest.ini_options]` — added so pytest doesn't try
  (and warn about failing) to collect `TestStep`/`TestSuiteFile`/`TestRunner` etc. as test classes
  just because of the `Test` prefix; they're plain domain dataclasses, not test classes
- `testomatic-io>=0.1.0` is on PyPI, but is a `pi` extra (`pip install -e ".[pi]"`), **not** a core
  dependency: it pulls in `gpiod` (libgpiod's Python bindings), which has a native C extension
  that only builds on Linux (needs `linux/const.h`) — installing it as a core dependency broke
  `pip install -e ".[dev]"` outright on macOS (a wheel build failure, confirmed by trying it), not
  just an import-time platform check. Install the `pi` extra on the Raspberry Pi itself when
  `cli.py`'s real-hardware path is actually exercised.
- **Not added**: `click`/`typer` — `cli.py` uses stdlib `argparse`, which was enough for the one
  `run <suite_path>` subcommand

## Staged order of work

- [x] **Phase 1** — `suite.py` parsing/validation against the sample JSON. No hardware needed,
      fully testable now.
- [x] **Phase 2** — `steps/base.py` + registry + the hardware-free executors (`DELAY`, `PYTHON`,
      `OPERATOR_INTERVENTION`) against a mocked `Chassis`.
- [ ] **Phase 3** — `power.py` and `iomod.py` are written and unit-tested against fake hardware
      (see Testing above), plus the `firmware.py`/`led_spectral.py` stubs (print-and-pass) so full
      suites containing those step types can run end-to-end. `READ_RAIL_VOLTAGE` (`power.py`) is
      confirmed working on the real chassis; `CONTROL_POWER_RAIL`/`READ_RAIL_CURRENT` and both
      `IOMOD_*` step types (`iomod.py`) are **still unverified** against real hardware.
- [x] **Phase 4** — `runner.py` orchestration + abort-on-fail/report logic, including the all-rails-off
      safety behaviour on abort-on-fail — implemented and unit-tested, and `BEEP`/`READ_RAIL_VOLTAGE`
      have now run successfully end-to-end via `cli.py` on a real chassis.
- [ ] **Phase 5** — `UPLOAD_FIRMWARE`, once the firmware-source question above is settled.
- [ ] **Phase 6** — `LED_SPECTRAL_READING`, once the existing sensor driver is wired in (either via
      a `testomatic-io` `chassis.colour_sensor` subsystem or directly in this executor).
