"""A guided walkthrough of the agent: routing, approval, and resume-by-token.

    python scripts/demo.py

Uses the OpenAI classifier when OPENAI_API_KEY is set, otherwise the offline
keyword classifier, so it runs with or without a key.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from agent import Agent, KeywordClassifier, get_classifier


def pick_classifier():
    # Load a local .env first so a key configured there is detected.
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True))
    except Exception:
        pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            return get_classifier("openai"), "OpenAIClassifier"
        except Exception:
            pass  # openai not installed -> fall back so the demo still runs
    return KeywordClassifier(), "KeywordClassifier"


def rule(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    classifier, name = pick_classifier()
    agent = Agent(classifier=classifier)
    print(f"classifier: {name}")

    rule("1. The hub router sends each message to a sub-flow")
    for message in ["what is your return policy?", "what is your warranty?", "hi there"]:
        out = agent.submit(message, token=message)
        print(f"  {message!r}")
        print(f"     -> {out['response']}")

    rule("2. A sensitive action pauses for human approval")
    paused = agent.submit("I'd like to order 3 shirts", token="order-A")
    print(f"  submit -> status={paused['status']}")
    print(f"           proposal={paused['proposal']}")
    approved = agent.resume("order-A", "approve")
    print(f"  human approves -> {approved['response']}")

    rule("3. Rejecting cancels it")
    agent.submit("order 10 posters", token="order-B")
    print(f"  human rejects  -> {agent.resume('order-B', 'no')['response']}")

    rule("4. The pause survives a restart (resume by token)")
    db = str(Path(tempfile.mkdtemp()) / "state.sqlite")
    first = Agent.with_sqlite(db, classifier=classifier)
    paused = first.submit("order 5 books", token="order-C")
    print(f"  process #1 submits -> status={paused['status']} (token 'order-C')")
    second = Agent.with_sqlite(db, classifier=classifier)  # a different Agent / process
    done = second.resume("order-C", "approve")
    print(f"  process #2 resumes -> {done['response']}")


if __name__ == "__main__":
    main()
