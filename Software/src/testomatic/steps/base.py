"""Shared types every step executor uses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    """The outcome of executing one Test Step."""

    passed: bool
    message: str = ""
    measured: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Hardware handles passed to every step executor."""

    chassis: Any
    test_module: Any = None
