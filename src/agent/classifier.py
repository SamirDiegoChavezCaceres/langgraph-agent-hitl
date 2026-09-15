"""Intent classification for the hub router.

The router needs an intent; it does not care how it is produced. The default is
a dependency-free keyword classifier so the whole agent runs and is testable
with no model or API key. Swap in an LLM-backed classifier (anything with a
``classify(text) -> str`` method) without touching the graph.
"""

from __future__ import annotations

from typing import Protocol

# Intents the hub router knows how to dispatch.
FAQ = "faq"
ORDER = "order"
SMALLTALK = "smalltalk"


class IntentClassifier(Protocol):
    def classify(self, text: str) -> str: ...


class KeywordClassifier:
    ORDER_WORDS = ("order", "buy", "purchase", "checkout")
    FAQ_WORDS = ("how", "what", "when", "shipping", "return", "returns", "payment", "?")

    def classify(self, text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in self.ORDER_WORDS):
            return ORDER
        if any(word in lowered for word in self.FAQ_WORDS):
            return FAQ
        return SMALLTALK
