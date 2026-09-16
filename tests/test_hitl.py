from agent import Agent


def test_approve_confirms_the_order():
    agent = Agent()
    agent.submit("order 2 mugs", token="ok")
    done = agent.resume("ok", "approve")
    assert done["status"] == "completed"
    assert done["response"] == "Order confirmed: 2 x mugs."


def test_reject_cancels_the_order():
    agent = Agent()
    agent.submit("order 2 mugs", token="no")
    done = agent.resume("no", "reject")
    assert done["status"] == "completed"
    assert "cancelled" in done["response"].lower()


def test_resume_survives_a_new_instance(tmp_path):
    # The token exists so a paused run can resume from a fresh Agent (standing in
    # for a different process), not only the one that started it.
    db = str(tmp_path / "state.sqlite")

    starting = Agent.with_sqlite(db)
    paused = starting.submit("order 5 books", token="shared-token")
    assert paused["status"] == "awaiting_approval"

    resuming = Agent.with_sqlite(db)  # different instance, same store
    done = resuming.resume("shared-token", "approve")
    assert done["response"] == "Order confirmed: 5 x books."
