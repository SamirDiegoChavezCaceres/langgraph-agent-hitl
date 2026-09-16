"""Run the agent through its three routes and the approval loop.

    python scripts/demo.py
"""

from __future__ import annotations

from agent import Agent


def main() -> None:
    agent = Agent()

    print("FAQ       ->", agent.submit("what is your return policy?", token="1")["response"])
    print("Smalltalk ->", agent.submit("hey", token="2")["response"])

    paused = agent.submit("I'd like to order 3 shirts", token="3")
    print("\nOrder paused for approval:", paused)

    approved = agent.resume("3", "approve")
    print("After approval:", approved["response"])

    paused2 = agent.submit("order 10 posters", token="4")
    print("\nOrder paused for approval:", paused2)
    print("After rejection:", agent.resume("4", "no")["response"])


if __name__ == "__main__":
    main()
