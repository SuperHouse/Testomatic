# Test Suite Package Format

A Test Suite is the ordered list of Test Steps and Manual Checks for a
[Design](../user-guide/designs.md). You can download a Test Suite as a **Test Suite Package**: a
ZIP archive containing the Test Suite Definition plus any other files it needs to run (for
example, firmware binaries for `UPLOAD_FIRMWARE` steps). This page describes the package layout
and the Test Suite Definition JSON format inside it. Use it to build external tools, such as a
Testomatic tester, that read or write Test Suites.

## Downloading a Test Suite Package

Only staff users can download a Test Suite Package. To download one, open the Design detail page
and go to the **Test Suite** tab. Click **Download**.

The download contains the version shown on the tab. This is the draft version if one exists. If
not, it is the current saved version.

The package filename follows this pattern:

```
{sku}-hw{hw_version}-test-suite-v{version}.zip
```

For example, `abc123-hw1-0-test-suite-v3.zip`. (This is the same pattern the JSON file used
before it moved inside a ZIP archive — only the extension changed, from `.json` to `.zip`.)

## Package contents

At minimum, a Test Suite Package contains one file, at the root of the archive:

```
test-suite-definition.json
```

This is the **Test Suite Definition** — a single JSON document listing the Test Suite's steps and
manual checks. Its format is described below, under
[Test Suite Definition format](#test-suite-definition-format).

A package may also contain other files that `test_steps` reference by filename — for example, a
firmware binary named by an `UPLOAD_FIRMWARE` step's `firmware_file` field. A consumer resolves
those filenames relative to the package root (see [Example](#example) below).

## Test Suite Definition format

`test-suite-definition.json` is a single JSON object with four top-level keys:

```json
{
  "export_schema_version": 1,
  "design": { "...": "..." },
  "test_suite": { "...": "..." },
  "test_steps": [ "..." ],
  "manual_checks": [ "..." ]
}
```

`export_schema_version` identifies the shape of the envelope: its top-level keys and their
nesting. The Register increases this number only when that shape changes, for example when a
top-level key changes name. It differs from `config_schema_version`, described below, which
tracks the shape of one step's own configuration fields.

### `design`

This object identifies the Design that the Test Suite belongs to:

| Field | Type | Description |
|---|---|---|
| `id` | integer | The Design's database ID |
| `sku` | string | The Design's SKU |
| `name` | string | The Design's name |
| `hw_version` | string | The Design's hardware version |

### `test_suite`

This object describes this version of the Test Suite:

| Field | Type | Description |
|---|---|---|
| `version` | integer | Version number, starting at 1 |
| `status` | string | `"DRAFT"` or `"SAVED"` |
| `notes` | string or `null` | Free-text notes the user enters when saving this version |
| `created_dt` | string | ISO 8601 timestamp showing when the Register created this version |

### `test_steps`

This is an array of Test Step objects, listed in execution order. Every step has the same outer
shape, regardless of type:

| Field | Type | Description |
|---|---|---|
| `order` | integer | Position within the suite (ascending) |
| `step_type` | string | One of the step type codes listed below |
| `name` | string | The step's display name |
| `abort_on_fail` | boolean | If `true`, a failure of this step stops the rest of the suite |
| `config_schema_version` | integer or `null` | The schema version of `config` below (`null` if the step predates schema versioning) |
| `config` | object | Type-specific configuration fields. See [Test Step types](#test-step-types) below |

`config_schema_version` copies the `schema_version` key already inside `config`. The Register
places it at this outer level so a consumer does not need to open the nested object to find it.
This number increases only when a step type's own config fields change shape. It is independent
of `export_schema_version` above.

### `manual_checks`

This is an array of Manual Check objects, listed in order. It is a plain checklist shown
alongside the Test Steps. Each item has no type or config fields of its own:

| Field | Type | Description |
|---|---|---|
| `order` | integer | Position within the list (ascending) |
| `text` | string | The checklist item's text |

## Test Step types

Each step's `config` object holds only the fields for its `step_type`. The Register omits an
**optional** field from `config` when it has no value. A consumer should apply its own default
instead of expecting a null or empty value for that key.

### `DELAY`

Waits a fixed number of milliseconds.

| Field | Type | Required | Description |
|---|---|---|---|
| `delay_ms` | integer | Yes | Delay in milliseconds |

### `UPLOAD_FIRMWARE`

Uploads a firmware image to the device under test.

| Field | Type | Required | Description |
|---|---|---|---|
| `upload_tool` | string | Yes | One of `avrdude`, `esptool.py`, `openocd`, `stm32cubeprogrammer` |
| `port` | string | Yes | Serial port / device identifier |
| `firmware_file` | string | Yes | Firmware binary filename, resolved relative to the Test Suite Package root |

### `BEEP`

Sounds a beep, or a sequence of beeps.

| Field | Type | Required | Description |
|---|---|---|---|
| `duration_ms` | integer | Yes | Duration of each beep, in milliseconds |
| `count` | integer | No | Number of beeps. A consumer should use `1` as the default when this field is absent |

### `READ_RAIL_VOLTAGE`

Reads a power rail's voltage. Checks that the reading falls within the given range.

| Field | Type | Required | Description |
|---|---|---|---|
| `rail` | string | Yes | One of `3.3V`, `5V`, `12V` |
| `min_v` | number | Yes | Minimum acceptable voltage |
| `max_v` | number | Yes | Maximum acceptable voltage |

### `READ_RAIL_CURRENT`

Reads a power rail's current draw. Checks that the reading falls within the given range.

| Field | Type | Required | Description |
|---|---|---|---|
| `rail` | string | Yes | One of `3.3V`, `5V`, `12V` |
| `min_ma` | number | Yes | Minimum acceptable current, in mA |
| `max_ma` | number | Yes | Maximum acceptable current, in mA |

### `CONTROL_POWER_RAIL`

Turns a power rail on or off.

| Field | Type | Required | Description |
|---|---|---|---|
| `rail` | string | Yes | One of `3.3V`, `5V`, `12V` |
| `action` | string | Yes | `ON` or `OFF` |

### `PYTHON`

Runs a block of Python code as the test step. The Register does not execute this code. It is
configuration data for a Testomatic tester, or another consumer, to run.

| Field | Type | Required | Description |
|---|---|---|---|
| `python_code` | string | Yes | Python source code |

### `IOMOD_ANALOG_READ`

Reads an analog value from an IOMOD pin. Optionally checks that the value falls within a range.

| Field | Type | Required | Description |
|---|---|---|---|
| `iomod` | string | Yes | IOMOD identifier, `A`–`G` |
| `pin` | string | Yes | Pin number, `0`–`7` |
| `expect_min` | integer | No | Minimum acceptable reading |
| `expect_max` | integer | No | Maximum acceptable reading |

### `IOMOD_DIGITAL_READ`

Reads a digital value from an IOMOD pin. Checks the value against an expected value.

| Field | Type | Required | Description |
|---|---|---|---|
| `iomod` | string | Yes | IOMOD identifier, `A`–`G` |
| `pin` | string | Yes | Pin number, `0`–`7` |
| `expect` | string | Yes | Expected value, `"0"` or `"1"` |

### `IOMOD_DIGITAL_WRITE`

Writes a digital value to an IOMOD pin.

| Field | Type | Required | Description |
|---|---|---|---|
| `iomod` | string | Yes | IOMOD identifier, `A`–`G` |
| `pin` | string | Yes | Pin number, `0`–`7` |
| `digital_write` | string | Yes | Value to write, `"0"` or `"1"` |

### `IOMOD_ANALOG_WRITE`

Writes an analog value to an IOMOD pin.

| Field | Type | Required | Description |
|---|---|---|---|
| `iomod` | string | Yes | IOMOD identifier, `A`–`G` |
| `pin` | string | Yes | Pin number, `0`–`7` |
| `analog_write` | integer | Yes | Value to write |

### `LED_SPECTRAL_READING`

Reads color and light values from an I2C spectral sensor. The sensor may connect through a MUX.
The step can optionally check that each channel falls within a range.

| Field | Type | Required | Description |
|---|---|---|---|
| `i2c_addr` | string | Yes | Sensor's I2C address, as hex text, for example `"0x29"` |
| `mux_chan` | string | Yes | MUX channel, `0`–`7` |
| `mux_addr` | string | No | MUX's I2C address, as hex text, for example `"0x71"`. Omitted if the board has no MUX in the path |
| `r_min` / `r_max` | integer | No | Red channel acceptable range |
| `g_min` / `g_max` | integer | No | Green channel acceptable range |
| `b_min` / `b_max` | integer | No | Blue channel acceptable range |
| `lux_min` / `lux_max` | integer | No | Lux (brightness) acceptable range |
| `ir_min` / `ir_max` | integer | No | Infrared channel acceptable range |

### `OPERATOR_INTERVENTION`

Displays an instruction to a human operator and waits for the operator to act. Unlike other step
types, it does not take an automated reading.

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | Instruction text shown to the operator |

## Example

A Test Suite Package for a board with an `UPLOAD_FIRMWARE` step unzips to:

```
abc123-hw1-0-test-suite-v3.zip
├── test-suite-definition.json
└── main.hex
```

`test-suite-definition.json`:

```json
{
  "export_schema_version": 1,
  "design": {
    "id": 42,
    "sku": "ABC123",
    "name": "Example Board",
    "hw_version": "1.0"
  },
  "test_suite": {
    "version": 3,
    "status": "SAVED",
    "notes": "Added LED spectral check",
    "created_dt": "2026-08-20T09:15:00+10:00"
  },
  "test_steps": [
    {
      "order": 1,
      "step_type": "DELAY",
      "name": "Settle",
      "abort_on_fail": false,
      "config_schema_version": 1,
      "config": { "schema_version": 1, "delay_ms": 250 }
    },
    {
      "order": 2,
      "step_type": "UPLOAD_FIRMWARE",
      "name": "Program microcontroller",
      "abort_on_fail": true,
      "config_schema_version": 1,
      "config": {
        "schema_version": 1,
        "upload_tool": "avrdude",
        "port": "/dev/ttyUSB0",
        "firmware_file": "main.hex"
      }
    },
    {
      "order": 3,
      "step_type": "READ_RAIL_VOLTAGE",
      "name": "Check 5V rail",
      "abort_on_fail": true,
      "config_schema_version": 1,
      "config": { "schema_version": 1, "rail": "5V", "min_v": 4.8, "max_v": 5.2 }
    },
    {
      "order": 4,
      "step_type": "LED_SPECTRAL_READING",
      "name": "Check status LED",
      "abort_on_fail": false,
      "config_schema_version": 1,
      "config": {
        "schema_version": 1,
        "i2c_addr": "0x29",
        "mux_addr": "0x71",
        "mux_chan": "2",
        "r_min": 100, "r_max": 255
      }
    }
  ],
  "manual_checks": [
    { "order": 1, "text": "Confirm LED lights up green" }
  ]
}
```
