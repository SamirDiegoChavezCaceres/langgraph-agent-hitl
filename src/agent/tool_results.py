"""A three-state result contract for tools.

Most tool code collapses "found nothing" and "something broke" into the same
empty-ish string, and the model then fills the silence with a guess. Forcing
every tool to return one of three explicit states - ``ok``, ``empty``, or
``fail`` - lets the agent tell "the search ran and found nothing" apart from
"the search errored", and respond honestly to each.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class Status(str, Enum):
    OK = "ok"        # succeeded with a usable result
    EMPTY = "empty"  # ran fine, but there was nothing to return (legitimate)
    FAIL = "fail"    # errored; the result cannot be trusted


@dataclass
class ToolResult:
    status: Status
    message: str
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_ok(self) -> bool:
        return self.status is Status.OK

    def render(self) -> str:
        """How the tool output is handed to the model."""
        return f"[{self.status.value}] {self.message}"


def ok(message: str, **data: Any) -> ToolResult:
    return ToolResult(Status.OK, message, dict(data))


def empty(message: str) -> ToolResult:
    return ToolResult(Status.EMPTY, message)


def fail(message: str) -> ToolResult:
    return ToolResult(Status.FAIL, message)
