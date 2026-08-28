# Test Runner — Implementation Plan

Status: draft, not started. Staged implementation — check off phases as they land.

## Scope for v1

Parse a Test Suite JSON export (format documented in [test-suite-export.md](test-suite-export.md))
and execute its `test_steps` in order against real hardware via `testomatic-io`
(`~/Dropbox/src/testomatic-io`), respecting `hard_fail`, and print a pass/fail report.
`manual_checks` are surfaced to the operator, not executed. Firmware upload and the colour-sensor
step are stubbed for now (see below) — everything else maps cleanly onto `testomatic-io`'s
existing API.

## Package layout

Build inside the `testomatic` package already scaffolded under `src/` rather than inventing a new
top-level name:

```
Software/
  pyproject.toml          # add [build-system], deps: testomatic-io, pytest
  src/testomatic/
    suite.py              # dataclasses + parsing/validation for the JSON envelope
    steps/
      base.py             # StepExecutor ABC + StepResult dataclass
      registry.py          # STEP_EXECUTORS: dict[str, StepExecutor] + @register_step
      delay.py, beep.py, power.py, iomod.py, python_step.py, operator.py
      firmware.py           # stub for now — see Deferred work below
      led_spectral.py       # stub for now — see Deferred work below
    runner.py              # TestRunner: iterate steps, call executor, honour hard_fail, build report
    cli.py                 # entry point, e.g. `python -m testomatic run suite.json`
  tests/
    test_suite_parsing.py  # exercises aqs-hw41-test-suite-v1.json as a fixture
    test_steps_*.py        # mock testomatic_io, per its own tests' pattern (see Testing below)
```

`steps/registry.py` mirrors the driver-registry pattern `testomatic-io` already uses for IOMOD
chips (`DRIVERS` + `probe()` in `testomatic_io/iomod/drivers/__init__.py`) — same idiom, so
anyone who knows one codebase recognises the other.

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

**Exception:** on a hard-fail (a step with `hard_fail: true` fails), the runner must immediately
turn off all three rails — `chassis.power.rail_3v3(False)`, `rail_5v(False)`, `rail_12v(False)` —
before stopping, regardless of what the runner believes their current state to be and regardless
of what step is executing. This is a safety measure (protecting the DUT/chassis on abort), not
part of normal step execution, so it belongs in `runner.py`'s hard-fail handling, not in
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
- On a step result of failure: if `hard_fail` is `True`, turn off all three power rails (see
  Power rail control above) and stop immediately; otherwise continue and record the failure.
- `config_schema_version` should be checked per step (`== 1` for now) so a future format change
  fails loudly instead of misreading fields — matches the guidance in `test-suite-export.md` about
  not conflating it with `export_schema_version`.
- Optional `config` fields: apply the documented defaults (e.g. `BEEP.count` defaults to `1` when
  absent) rather than assuming `null`.
- End-of-run: print a summary (step name, pass/fail, measured value where relevant) and list
  `manual_checks` for the operator to work through by hand.

## Testing without a Pi

`testomatic_io` refuses to import off real hardware (Blinka does platform detection at import
time). Follow the same approach its own test suite uses — stub `board`/`tca9548a`/`gpiod`/`busio`
in `sys.modules` (or reuse fixtures from `testomatic-io/tests/conftest.py` if it exposes a fake
`Chassis`) before importing, so step-executor logic is fully testable off-hardware.
`suite.py`'s JSON parsing/validation needs no stubbing at all — test it directly against
`aqs-hw41-test-suite-v1.json`.

## `pyproject.toml` changes needed

Currently has no `[build-system]`, deps, or tool config. Add:
- `[build-system]` (setuptools, src layout)
- a dependency on `testomatic-io` (path/git dependency for now — it isn't on PyPI)
- `pytest` as a dev dependency
- possibly `click` or `typer` for `cli.py`, or just `argparse` to avoid a new dependency for
  something this small

## Staged order of work

- [ ] **Phase 1** — `suite.py` parsing/validation against the sample JSON. No hardware needed,
      fully testable now.
- [ ] **Phase 2** — `steps/base.py` + registry + the hardware-free executors (`DELAY`, `PYTHON`,
      `OPERATOR_INTERVENTION`) against a mocked `Chassis`.
- [ ] **Phase 3** — wire `power.py` and `iomod.py` against real `testomatic-io`, verify on the
      actual chassis. Include the `firmware.py`/`led_spectral.py` stubs (print-and-pass) so full
      suites containing those step types can run end-to-end.
- [ ] **Phase 4** — `runner.py` orchestration + hard-fail/report logic, including the all-rails-off
      safety behaviour on hard-fail.
- [ ] **Phase 5** — `UPLOAD_FIRMWARE`, once the firmware-source question above is settled.
- [ ] **Phase 6** — `LED_SPECTRAL_READING`, once the existing sensor driver is wired in (either via
      a `testomatic-io` `chassis.colour_sensor` subsystem or directly in this executor).
