"""Tiny example tools that speak the three-state result contract."""

from __future__ import annotations

from .tool_results import ToolResult, empty, ok

_FAQ = {
    "shipping": "Orders ship worldwide within 3-5 business days.",
    "returns": "Returns are free within 30 days of delivery.",
    "payment": "We accept major cards and PayPal.",
}


def lookup_faq(topic: str) -> ToolResult:
    """Look a topic up in the FAQ. Returns ``empty`` (not ``fail``) when the
    topic simply is not covered - a legitimate 'I don't have that' answer."""
    key = topic.strip().lower()
    for name, answer in _FAQ.items():
        if name in key:
            return ok(answer, topic=name)
    return empty(f"No FAQ entry matches '{topic}'.")
