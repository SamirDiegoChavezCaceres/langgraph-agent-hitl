"""A thin wrapper over the compiled graph: submit a request, and if the agent
pauses for approval, resume it later by its token.

The token is the LangGraph thread id. With a persistent checkpointer
(:meth:`Agent.with_sqlite`) the paused run survives a process restart, so the
human approval can come from a different process entirely.
"""

from __future__ import annotations

from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from .classifier import IntentClassifier
from .graph import build_graph


class Agent:
    def __init__(self, checkpointer=None, classifier: Optional[IntentClassifier] = None) -> None:
        self.graph = build_graph(classifier).compile(checkpointer=checkpointer or MemorySaver())

    @classmethod
    def with_sqlite(cls, path: str, classifier: Optional[IntentClassifier] = None) -> "Agent":
        import sqlite3

        from langgraph.checkpoint.sqlite import SqliteSaver

        saver = SqliteSaver(sqlite3.connect(path, check_same_thread=False))
        saver.setup()
        return cls(checkpointer=saver, classifier=classifier)

    def submit(self, request: str, token: str) -> dict:
        state = {"request": request, "intent": "", "response": "", "proposal": None}
        return self._interpret(self.graph.invoke(state, self._config(token)), token)

    def resume(self, token: str, decision: str) -> dict:
        result = self.graph.invoke(Command(resume=decision), self._config(token))
        return self._interpret(result, token)

    @staticmethod
    def _config(token: str) -> dict:
        return {"configurable": {"thread_id": token}}

    @staticmethod
    def _interpret(result: dict, token: str) -> dict:
        interrupts = result.get("__interrupt__")
        if interrupts:
            payload = dict(interrupts[0].value)
            return {"status": "awaiting_approval", "token": token, **payload}
        return {"status": "completed", "response": result.get("response", "")}
