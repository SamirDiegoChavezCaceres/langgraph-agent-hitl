"""Intent classification for the hub router.

The router needs an intent; it does not care how it is produced. The default is
a dependency-free keyword classifier so the whole agent runs and is testable
with no model or API key. Swap in an LLM-backed classifier (anything with a
``classify(text) -> str`` method) without touching the graph.
"""

from __future__ import annotations

import os
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


class OpenAIClassifier:
    """Classify intent with an OpenAI chat model (the ``openai`` extra).

    Reads ``OPENAI_API_KEY`` from the environment or a local ``.env`` file. Falls
    back to ``smalltalk`` if the model answers with anything off-list.
    """

    def __init__(self, model: str = None) -> None:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass
        from openai import OpenAI  # lazy import

        self._client = OpenAI()
        self.model = model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    def classify(self, text: str) -> str:
        prompt = (
            f"Classify the message into exactly one label: {FAQ}, {ORDER}, or "
            f"{SMALLTALK}. Reply with only the label.\n\nMessage: {text}"
        )
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            max_tokens=4,
            messages=[{"role": "user", "content": prompt}],
        )
        label = (resp.choices[0].message.content or "").strip().lower()
        return label if label in (FAQ, ORDER, SMALLTALK) else SMALLTALK


# Strategy + Factory: pick a classifier by name; a new provider is one entry.
_CLASSIFIERS = {"keyword": KeywordClassifier, "openai": OpenAIClassifier}


def get_classifier(prefer: str = "keyword") -> IntentClassifier:
    try:
        return _CLASSIFIERS[prefer]()
    except KeyError:
        raise ValueError(
            f"unknown classifier '{prefer}'; options: {', '.join(_CLASSIFIERS)}"
        )
