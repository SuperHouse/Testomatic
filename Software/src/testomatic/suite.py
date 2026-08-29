"""Parsing and validation for the Test Suite Definition JSON.

Format reference: test-suite-package.md (mirrors the format Register's
`testing.views._serialize_test_suite` produces).
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXPORT_SCHEMA_VERSION = 1
TEST_SUITE_DEFINITION_FILENAME = "test-suite-definition.json"


class SuiteFormatError(ValueError):
    """A Test Suite JSON file doesn't match the expected envelope shape."""


@dataclass(frozen=True)
class Design:
    id: int
    sku: str
    name: str
    hw_version: str


@dataclass(frozen=True)
class TestSuiteMeta:
    version: int
    status: str
    notes: str | None
    created_dt: str


@dataclass(frozen=True)
class TestStep:
    order: int
    step_type: str
    name: str
    abort_on_fail: bool
    config_schema_version: int | None
    config: dict


@dataclass(frozen=True)
class ManualCheck:
    order: int
    text: str


@dataclass(frozen=True)
class TestSuiteFile:
    export_schema_version: int
    design: Design
    test_suite: TestSuiteMeta
    test_steps: list[TestStep]
    manual_checks: list[ManualCheck]


def load_suite(path: str | Path) -> TestSuiteFile:
    """Load and validate a Test Suite Definition from `path`.

    `path` may point directly at a Test Suite Definition JSON file, or at a Test Suite Package
    ZIP archive (see test-suite-package.md) — the package's wrapped test-suite-definition.json is
    located and parsed automatically.
    """
    path = Path(path)
    if path.suffix == ".zip":
        text = _read_definition_from_package(path)
    else:
        text = path.read_text()
    return parse_suite(json.loads(text))


def _read_definition_from_package(path: Path) -> str:
    """Finds and reads test-suite-definition.json from inside a Test Suite Package ZIP.

    Located by filename suffix rather than a hardcoded path, since the definition sits inside a
    top-level folder named after the package (e.g. `abc-hw1-0-test-suite-v3/test-suite-
    definition.json`), not at the archive root.
    """
    with zipfile.ZipFile(path) as archive:
        matches = [name for name in archive.namelist() if name.endswith(TEST_SUITE_DEFINITION_FILENAME)]
        if not matches:
            raise SuiteFormatError(f"No {TEST_SUITE_DEFINITION_FILENAME} found in Test Suite Package {path}")
        if len(matches) > 1:
            raise SuiteFormatError(
                f"Multiple {TEST_SUITE_DEFINITION_FILENAME} entries found in Test Suite Package "
                f"{path}: {matches}"
            )
        return archive.read(matches[0]).decode("utf-8")


def parse_suite(data: dict) -> TestSuiteFile:
    """Parse and validate a Test Suite JSON export already loaded as a dict."""
    export_schema_version = _require(data, "export_schema_version")
    if export_schema_version != SUPPORTED_EXPORT_SCHEMA_VERSION:
        raise SuiteFormatError(
            f"Unsupported export_schema_version {export_schema_version!r}; "
            f"this runner supports {SUPPORTED_EXPORT_SCHEMA_VERSION}"
        )

    test_steps = sorted(
        (_parse_test_step(step) for step in _require(data, "test_steps")),
        key=lambda step: step.order,
    )
    manual_checks = sorted(
        (_parse_manual_check(check) for check in _require(data, "manual_checks")),
        key=lambda check: check.order,
    )

    return TestSuiteFile(
        export_schema_version=export_schema_version,
        design=_parse_design(_require(data, "design")),
        test_suite=_parse_test_suite_meta(_require(data, "test_suite")),
        test_steps=test_steps,
        manual_checks=manual_checks,
    )


def _require(data: dict, key: str):
    try:
        return data[key]
    except KeyError as exc:
        raise SuiteFormatError(f"Missing required key: {key}") from exc


def _parse_design(data: dict) -> Design:
    return Design(
        id=_require(data, "id"),
        sku=_require(data, "sku"),
        name=_require(data, "name"),
        hw_version=_require(data, "hw_version"),
    )


def _parse_test_suite_meta(data: dict) -> TestSuiteMeta:
    return TestSuiteMeta(
        version=_require(data, "version"),
        status=_require(data, "status"),
        notes=data.get("notes"),
        created_dt=_require(data, "created_dt"),
    )


def _parse_test_step(data: dict) -> TestStep:
    config = _require(data, "config")
    config_schema_version = data.get("config_schema_version")
    inner_version = config.get("schema_version")
    if (
        config_schema_version is not None
        and inner_version is not None
        and config_schema_version != inner_version
    ):
        raise SuiteFormatError(
            f"Step {data.get('name')!r}: config_schema_version "
            f"({config_schema_version}) does not match config['schema_version'] "
            f"({inner_version})"
        )

    return TestStep(
        order=_require(data, "order"),
        step_type=_require(data, "step_type"),
        name=_require(data, "name"),
        abort_on_fail=data.get("abort_on_fail", False),
        config_schema_version=config_schema_version,
        config=config,
    )


def _parse_manual_check(data: dict) -> ManualCheck:
    return ManualCheck(order=_require(data, "order"), text=_require(data, "text"))
