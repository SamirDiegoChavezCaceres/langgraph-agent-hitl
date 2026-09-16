# langgraph-agent-hitl

A small LangGraph agent that shows three patterns you need the moment an agent
does anything real:

1. **A hub router.** One node classifies intent and dispatches to a small
   sub-flow, instead of one giant prompt trying to do everything.
2. **Human-in-the-loop by token.** A sensitive action (placing an order) pauses
   for approval and resumes later from a persistent checkpoint - the approval
   can arrive from another process, minutes or days later.
3. **A three-state tool contract.** Tools return `ok` / `empty` / `fail`, so the
   agent can tell "found nothing" apart from "errored" and stop making things up.

It runs with no LLM and no API key: intent classification defaults to a keyword
classifier you can swap for an LLM.

## The graph

```
route ─┬─► faq          ─► END
       ├─► place_order  ─► (interrupt: approve?) ─► END
       └─► smalltalk    ─► END
```

`place_order` calls `interrupt()`. The run stops there, its state is saved by
the checkpointer, and `Command(resume=decision)` continues from exactly that
point.

## Use it

```python
from agent import Agent

agent = Agent()

agent.submit("what is your shipping policy?", token="t1")
# {'status': 'completed', 'response': 'Orders ship worldwide within 3-5 business days.'}

agent.submit("I want to order 3 shirts", token="t2")
# {'status': 'awaiting_approval', 'token': 't2',
#  'question': 'Approve this order?', 'proposal': {'item': 'shirts', 'qty': 3}}

agent.resume("t2", "approve")
# {'status': 'completed', 'response': 'Order confirmed: 3 x shirts.'}
```

### The token survives a restart

The resume token is the LangGraph thread id. With the SQLite checkpointer, a
paused run can be resumed by a completely different process:

```python
Agent.with_sqlite("state.sqlite").submit("order 5 books", token="abc")
# ... later, elsewhere ...
Agent.with_sqlite("state.sqlite").resume("abc", "approve")
# {'status': 'completed', 'response': 'Order confirmed: 5 x books.'}
```

That is exactly what an approval queue needs: the worker that proposes an action
and the human who approves it are not the same process.

## Swapping the classifier

`Agent(classifier=...)` takes anything with `classify(text) -> str`. The default
`KeywordClassifier` keeps the demo and tests deterministic; a real deployment
drops in an LLM-backed one without touching the graph.

```bash
python scripts/demo.py
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Covers routing, the approval/rejection paths, the "don't improvise on an unknown
FAQ" behaviour, and resume-from-a-fresh-instance via the SQLite checkpointer.

## License

MIT.
