from agent import Agent


def test_faq_is_answered():
    out = Agent().submit("what is your shipping policy?", token="a")
    assert out["status"] == "completed"
    assert "ship" in out["response"].lower()


def test_smalltalk_is_routed():
    out = Agent().submit("hello there", token="b")
    assert out["status"] == "completed"
    assert "ask me" in out["response"].lower()


def test_unknown_faq_is_not_improvised():
    # The topic is phrased as a question (routes to faq) but is not in the KB.
    out = Agent().submit("what is your warranty?", token="c")
    assert out["status"] == "completed"
    assert "don't have an answer" in out["response"].lower()


def test_order_pauses_for_approval():
    out = Agent().submit("I want to order 3 shirts", token="d")
    assert out["status"] == "awaiting_approval"
    assert out["proposal"] == {"item": "shirts", "qty": 3}
