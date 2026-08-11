"""Phase 11 tests — SQL Transparency (FR-9, PRD §5.6).

Every data-producing turn must visibly carry the generated SQL in the
envelope, in the mandated field order (sql → table → chart → diagram →
explanation). Deterministic via the scripted model; the tools are real.
"""
from types import SimpleNamespace

import app.tools.explain_data as explain_data_module
from app.agent import agent_service
from app.models.schemas import ChatResponse
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call

TOP_PRODUCTS_SQL = (
    "SELECT p.name AS name, SUM(oi.quantity * oi.unit_price) AS revenue "
    "FROM products p JOIN order_items oi ON oi.product_id = p.id "
    "GROUP BY p.name ORDER BY revenue DESC LIMIT 5"
)


def test_successful_data_turn_exposes_generated_sql():
    model = ScriptedChatModel(
        responses=[
            tool_call("get_schema", {}, "c1"),
            tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
            final_answer("Here are the top 5 products by revenue."),
        ]
    )
    response = agent_service.run_agent("sql-ok", "top products", model=model)
    assert response.error is None
    assert response.sql == TOP_PRODUCTS_SQL
    assert response.columns == ["name", "revenue"]
    assert len(response.rows) == 5


def test_failed_turn_exposes_attempted_sql_and_structured_error():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "DROP TABLE customers"}, "c1"),
            final_answer("read-only"),
        ]
    )
    response = agent_service.run_agent("sql-fail", "delete everything", model=model)
    assert response.error is not None
    assert response.error.type == "validation_rejected"
    assert response.sql == "DROP TABLE customers"
    # The raw statement never leaks into the user-facing message.
    assert "DROP" not in response.message


def test_non_data_turn_has_no_sql():
    model = ScriptedChatModel(responses=[final_answer("I can only read data.")])
    response = agent_service.run_agent("sql-none", "hi", model=model)
    assert response.sql is None
    assert response.columns == []
    assert response.rows == []


def test_envelope_field_order_matches_prd_5_6():
    """sql → table (columns/rows) → chart → diagram → explanation → error."""
    fields = list(ChatResponse.model_fields.keys())
    assert fields == [
        "message",
        "sql",
        "columns",
        "rows",
        "chart",
        "diagram",
        "explanation",
        "error",
    ]


# --- Regression: prose must match the SAME result as sql/table -------------
#
# When the agent runs more than one successful execute_query in a turn, the
# envelope's sql/rows always reflect the LAST one. Before this fix, the
# model's own closing prose was used verbatim regardless — so it could
# describe an EARLIER query's numbers while the table showed the last query's
# numbers. These tests pin down both directions of the fix.


def test_single_successful_query_still_uses_raw_prose():
    """Baseline: with exactly one successful query, the model's own closing
    text is used directly, unchanged — the fix only touches multi-query turns."""
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "SELECT 1 AS value"}, "c1"),
            final_answer("The value is 1."),
        ]
    )
    response = agent_service.run_agent("sql-single", "one query", model=model)
    assert response.message == "The value is 1."


def test_multiple_successful_queries_prose_cannot_describe_an_earlier_result():
    """Reproduces the originally observed mismatch: two successful queries,
    with the model's final text narrating the FIRST one's numbers. The
    envelope must still show the LAST query's sql/rows, and the message must
    no longer carry the earlier, now-inconsistent numbers."""
    model = ScriptedChatModel(
        responses=[
            tool_call(
                "execute_query", {"sql": "SELECT 'exploratory' AS note, 111 AS value"}, "c1"
            ),
            tool_call("execute_query", {"sql": "SELECT 'final' AS note, 999 AS value"}, "c2"),
            final_answer("The value is 111, from the exploratory query."),
        ]
    )
    response = agent_service.run_agent("sql-multi-mismatch", "run two queries", model=model)

    assert response.error is None
    assert response.sql == "SELECT 'final' AS note, 999 AS value"
    assert response.rows == [["final", 999]]
    # The stale, mismatched number from the earlier query must not appear.
    assert "111" not in response.message
    assert response.message == "Here are the results."


def test_multiple_successful_queries_uses_grounded_explanation_when_it_matches(monkeypatch):
    """When `explain_data` IS called with the SAME data as the final query,
    its grounded explanation is trusted as the message — proving the fix
    doesn't just blank out every multi-query turn, only ungrounded ones."""

    class _FakeExplainModel:
        def invoke(self, messages):
            return SimpleNamespace(content="The final value is 999.")

    monkeypatch.setattr(explain_data_module, "_llm_factory", lambda: _FakeExplainModel())

    model = ScriptedChatModel(
        responses=[
            tool_call(
                "execute_query", {"sql": "SELECT 'exploratory' AS note, 111 AS value"}, "c1"
            ),
            tool_call("execute_query", {"sql": "SELECT 'final' AS note, 999 AS value"}, "c2"),
            tool_call(
                "explain_data",
                {
                    "data": {"columns": ["note", "value"], "rows": [["final", 999]]},
                    "question": "run two queries",
                },
                "c3",
            ),
            final_answer("(closing text that must NOT be used as the message)"),
        ]
    )
    response = agent_service.run_agent("sql-multi-grounded", "run two queries", model=model)

    assert response.error is None
    assert response.sql == "SELECT 'final' AS note, 999 AS value"
    assert response.rows == [["final", 999]]
    assert response.message == "The final value is 999."
    assert response.explanation == "The final value is 999."


def test_multiple_successful_queries_ignores_explanation_grounded_in_an_earlier_result(
    monkeypatch,
):
    """If `explain_data` was called with an EARLIER query's data (not the
    final one), its explanation must not be used as the message either —
    only an explanation verifiably grounded in the final result is trusted."""

    class _FakeExplainModel:
        def invoke(self, messages):
            return SimpleNamespace(content="The exploratory value is 111.")

    monkeypatch.setattr(explain_data_module, "_llm_factory", lambda: _FakeExplainModel())

    model = ScriptedChatModel(
        responses=[
            tool_call(
                "execute_query", {"sql": "SELECT 'exploratory' AS note, 111 AS value"}, "c1"
            ),
            tool_call(
                "explain_data",
                {
                    "data": {"columns": ["note", "value"], "rows": [["exploratory", 111]]},
                    "question": "run two queries",
                },
                "c2",
            ),
            tool_call("execute_query", {"sql": "SELECT 'final' AS note, 999 AS value"}, "c3"),
            final_answer("The value is 111, from the exploratory query."),
        ]
    )
    response = agent_service.run_agent("sql-multi-stale-explain", "run two queries", model=model)

    assert response.error is None
    assert response.sql == "SELECT 'final' AS note, 999 AS value"
    assert response.rows == [["final", 999]]
    assert "111" not in response.message
    assert response.message == "Here are the results."
