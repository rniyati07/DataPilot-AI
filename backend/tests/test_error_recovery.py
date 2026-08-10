"""Phase 12 tests — bounded self-correction (Architecture §6, FR-10).

Exactly one automatic `execute_query` retry, tracked in code. The counter is
unit-tested through the registry tool under a budget scope, and agent-level
tests drive the fail→retry→success / fail→fail→graceful journeys.
"""
from app.agent import agent_service, error_recovery, tool_registry
from app.session.context import session_scope
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call

BAD_SQL = "SELECT nonexistent_column FROM products"
GOOD_SQL = "SELECT name, price FROM products LIMIT 2"


def _scope():
    return session_scope("er-session")


# --- Budget counter (unit level, through the real registry tool) ------------


def test_retryable_failure_consumes_one_budget_slot():
    with _scope(), error_recovery.retry_budget_scope() as budget:
        result = tool_registry._execute_query_tool(BAD_SQL)
        assert result["success"] is False
        assert result["error"]["type"] == "sql_error"
        assert budget.retries == 1


def test_success_does_not_consume_budget():
    with _scope(), error_recovery.retry_budget_scope() as budget:
        result = tool_registry._execute_query_tool(GOOD_SQL)
        assert result["success"] is True
        assert budget.retries == 0


def test_second_retryable_failure_is_capped():
    with _scope(), error_recovery.retry_budget_scope() as budget:
        first = tool_registry._execute_query_tool(BAD_SQL)
        second = tool_registry._execute_query_tool(BAD_SQL)
        third = tool_registry._execute_query_tool(BAD_SQL)
        assert first["error"]["type"] == "sql_error"
        assert second["error"]["type"] == "retry_limit_reached"
        assert third["error"]["type"] == "retry_limit_reached"
        assert budget.retries == 3


def test_write_rejection_never_consumes_budget():
    with _scope(), error_recovery.retry_budget_scope() as budget:
        result = tool_registry._execute_query_tool("DROP TABLE customers")
        assert result["error"]["type"] == "validation_rejected"
        assert budget.retries == 0


def test_budget_is_scoped_per_invocation():
    with _scope():
        with error_recovery.retry_budget_scope() as budget_a:
            tool_registry._execute_query_tool(BAD_SQL)
            assert budget_a.retries == 1
        with error_recovery.retry_budget_scope() as budget_b:
            assert budget_b.retries == 0


# --- Agent journeys --------------------------------------------------------


def test_journey_c_fail_then_retry_succeeds():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": BAD_SQL}, "c1"),
            tool_call("execute_query", {"sql": GOOD_SQL}, "c2"),
            final_answer("I corrected the query and here are the results."),
        ]
    )
    response = agent_service.run_agent("er-journey", "top products", model=model)
    assert response.error is None
    assert response.sql == GOOD_SQL
    assert response.columns == ["name", "price"]
    # The correction was surfaced to the agent; its reply mentions it briefly.
    assert "corrected" in response.message.lower()


def test_second_failure_stops_after_one_retry():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": BAD_SQL}, "c1"),
            tool_call("execute_query", {"sql": BAD_SQL}, "c2"),
            final_answer("I could not complete that query."),
        ]
    )
    response = agent_service.run_agent("er-capped", "top products", model=model)
    # Exactly three model turns — the loop did not run unbounded.
    assert model.calls == 3
    assert response.error is not None
    assert response.error.type == "retry_limit_reached"
    # Graceful, human-readable message — never a raw driver error/stack trace.
    assert "no such column" not in response.message.lower()
    assert "Traceback" not in response.message
    assert "corrected" in response.message.lower() or "could not" in response.message.lower()


def test_validation_rejection_is_not_retried():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "DELETE FROM customers"}, "c1"),
            final_answer("I can only read data."),
        ]
    )
    response = agent_service.run_agent("er-write", "delete", model=model)
    assert model.calls == 2  # no retry loop after a rejected write
    assert response.error is not None
    assert response.error.type == "validation_rejected"


def test_retryable_types_are_explicit():
    assert error_recovery.RETRYABLE_ERROR_TYPES == ("sql_error",)
    assert error_recovery.MAX_EXECUTE_QUERY_RETRIES == 1
