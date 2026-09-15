"""The agent graph: a hub router that dispatches to small sub-flows, one of
which pauses for human approval.

    route ─┬─► faq          ─► END
           ├─► place_order  ─► (interrupt for approval) ─► END
           └─► smalltalk    ─► END

``place_order`` calls ``interrupt()``. The graph stops there and persists its
state through the checkpointer; resuming with ``Command(resume=decision)``
continues from exactly that point. The resume "token" is just the thread id, so
approval can arrive seconds or days later, from another process.
"""

from __future__ import annotations

import re
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .classifier import FAQ, ORDER, SMALLTALK, IntentClassifier, KeywordClassifier
from .tools import lookup_faq


class AgentState(TypedDict):
    request: str
    intent: str
    response: str
    proposal: Optional[dict]


def _parse_order(request: str) -> dict:
    match = re.search(r"(\d+)\s+(\w+)", request)
    qty = int(match.group(1)) if match else 1
    item = match.group(2) if match else "item"
    return {"item": item, "qty": qty}


def build_graph(classifier: Optional[IntentClassifier] = None) -> StateGraph:
    """Return the (uncompiled) graph. Compile it with a checkpointer."""
    classifier = classifier or KeywordClassifier()

    def route(state: AgentState) -> dict:
        return {"intent": classifier.classify(state["request"])}

    def faq(state: AgentState) -> dict:
        result = lookup_faq(state["request"])
        if result.is_ok:
            return {"response": result.message}
        # 'empty' is not a failure: say so plainly instead of improvising.
        return {"response": "I don't have an answer for that in the FAQ."}

    def place_order(state: AgentState) -> dict:
        proposal = _parse_order(state["request"])
        # Pause here and hand the proposal to a human.
        decision = interrupt({"question": "Approve this order?", "proposal": proposal})
        approved = str(decision).strip().lower() in ("approve", "approved", "yes", "y")
        if approved:
            return {
                "proposal": None,
                "response": f"Order confirmed: {proposal['qty']} x {proposal['item']}.",
            }
        return {"proposal": None, "response": "Order cancelled by the reviewer."}

    def smalltalk(state: AgentState) -> dict:
        return {"response": "Hi! Ask me about shipping, returns, or place an order."}

    builder = StateGraph(AgentState)
    builder.add_node("route", route)
    builder.add_node("faq", faq)
    builder.add_node("place_order", place_order)
    builder.add_node("smalltalk", smalltalk)

    builder.add_edge(START, "route")
    builder.add_conditional_edges(
        "route",
        lambda state: state["intent"],
        {FAQ: "faq", ORDER: "place_order", SMALLTALK: "smalltalk"},
    )
    for node in ("faq", "place_order", "smalltalk"):
        builder.add_edge(node, END)
    return builder
