"""Phase 7 tests — bounded, session-scoped conversation memory (FR-8).

The memory layer is deterministic code; agent turns are driven with the
scripted model, and a recording model asserts what the second turn actually
receives.
"""
from typing import Any, ClassVar, Optional

from app.agent import agent_service
from app.agent.memory import ConversationMemory
from app.session import store as session_store
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call

TOP_PRODUCTS_SQL = (
    "SELECT p.name AS name, SUM(oi.quantity * oi.unit_price) AS revenue "
    "FROM products p JOIN order_items oi ON oi.product_id = p.id "
    "GROUP BY p.name ORDER BY revenue DESC LIMIT 5"
)


def _scripted(*messages) -> ScriptedChatModel:
    return ScriptedChatModel(responses=list(messages))


class RecordingChatModel(ScriptedChatModel):
    """ScriptedChatModel that also records what each turn received."""

    batches: ClassVar[list[list[str]]] = []
    texts: ClassVar[list[list[str]]] = []

    def _generate(
        self,
        messages: list,
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Any:
        RecordingChatModel.batches.append([type(m).__name__ for m in messages])
        RecordingChatModel.texts.append([str(getattr(m, "content", "")) for m in messages])
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


# --- ConversationMemory unit behavior --------------------------------------


def test_memory_is_bounded_by_turn_window():
    memory = ConversationMemory(max_turns=2)
    for index in range(6):
        memory.add_user(f"user-{index}")
        memory.add_assistant(f"assistant-{index}")
    assert memory.turn_count == 2
    messages = memory.to_messages()
    # Only the last two complete turns survive.
    assert messages[0] == {"role": "user", "content": "user-4"}
    assert messages[-1] == {"role": "assistant", "content": "assistant-5"}


def test_memory_preserves_interleaved_order():
    memory = ConversationMemory(max_turns=3)
    memory.add_user("u1")
    memory.add_assistant("a1")
    assert memory.to_messages() == [
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
    ]


def test_memory_clear_resets_turns():
    memory = ConversationMemory()
    memory.add_user("u")
    memory.add_assistant("a")
    memory.clear()
    assert memory.turn_count == 0
    assert memory.to_messages() == []


def test_partial_turn_counts_as_one_turn():
    memory = ConversationMemory(max_turns=2)
    memory.add_user("u1")
    assert memory.turn_count == 1


# --- Session store behavior ------------------------------------------------


def test_memory_is_scoped_per_session():
    assert session_store.get_memory("mem-a") is session_store.get_memory("mem-a")
    assert session_store.get_memory("mem-a") is not session_store.get_memory("mem-b")


def test_switching_database_resets_memory():
    memory = session_store.get_memory("mem-switch")
    memory.add_user("hi")
    memory.add_assistant("hello")
    session_store.set_active_database("mem-switch", __import__("pathlib").Path("/tmp/x.db"), "x")
    assert session_store.get_memory("mem-switch").turn_count == 0


def test_clearing_database_resets_memory():
    memory = session_store.get_memory("mem-clear")
    memory.add_user("hi")
    session_store.clear_active_database("mem-clear")
    assert session_store.get_memory("mem-clear").turn_count == 0


def test_last_results_roundtrip_and_reset():
    assert session_store.get_last_results("mem-results") is None
    session_store.set_last_results("mem-results", {"columns": ["a"], "rows": [[1]]})
    assert session_store.get_last_results("mem-results") == {"columns": ["a"], "rows": [[1]]}
    session_store.clear_active_database("mem-results")
    assert session_store.get_last_results("mem-results") is None


# --- Agent wiring ----------------------------------------------------------


def test_run_populates_memory_and_last_results():
    model = _scripted(
        tool_call("get_schema", {}, "c1"),
        tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
        final_answer("Here are the top 5 products by revenue."),
    )
    response = agent_service.run_agent("mem-run", "top products", model=model)
    assert response.error is None

    memory = session_store.get_memory("mem-run")
    assert memory.turn_count == 1
    assert memory.to_messages()[0]["content"] == "top products"
    assert memory.to_messages()[1]["content"] == "Here are the top 5 products by revenue."

    last = session_store.get_last_results("mem-run")
    assert last["columns"] == ["name", "revenue"]
    assert len(last["rows"]) == 5


def test_failed_query_does_not_set_last_results():
    model = _scripted(
        tool_call("execute_query", {"sql": "DROP TABLE customers"}, "c1"),
        final_answer("read-only"),
    )
    response = agent_service.run_agent("mem-fail", "delete", model=model)
    assert response.error is not None
    assert session_store.get_last_results("mem-fail") is None


def test_second_turn_receives_prior_turns_and_result_set():
    RecordingChatModel.batches = []
    RecordingChatModel.texts = []

    first = _scripted(
        tool_call("get_schema", {}, "c1"),
        tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
        final_answer("Here are the top 5 products by revenue."),
    )
    agent_service.run_agent("mem-two", "Show me the top products", model=first)

    second = RecordingChatModel(responses=[final_answer("Understood.")])
    agent_service.run_agent("mem-two", "now show their trend", model=second)

    assert len(RecordingChatModel.batches) == 1
    joined = "\n".join(RecordingChatModel.texts[0])
    # Prior text turns are present…
    assert "Show me the top products" in joined
    assert "Here are the top 5 products by revenue." in joined
    # …and the previous result set is injected compactly for reference.
    assert "[Result set from your previous question]" in joined
    assert "name, revenue" in joined


def test_memory_does_not_leak_across_sessions():
    model = _scripted(final_answer("hello"))
    agent_service.run_agent("mem-leak-a", "hi", model=model)
    assert session_store.get_memory("mem-leak-a").turn_count == 1
    assert session_store.get_memory("mem-leak-b").turn_count == 0


def test_second_turn_memory_is_bounded(monkeypatch):
    RecordingChatModel.batches = []
    RecordingChatModel.texts = []
    memory = session_store.get_memory("mem-bound")
    for index in range(20):
        memory.add_user(f"u-{index}")
        memory.add_assistant(f"a-{index}")

    model = RecordingChatModel(responses=[final_answer("ok")])
    agent_service.run_agent("mem-bound", "next", model=model)
    joined = "\n".join(RecordingChatModel.texts[0])
    assert "u-0" not in joined  # oldest turns were trimmed
    assert "u-19" in joined
