"""Phase 11 tests — SQL Transparency (FR-9, PRD §5.6).

Every data-producing turn must visibly carry the generated SQL in the
envelope, in the mandated field order (sql → table → chart → diagram →
explanation). Deterministic via the scripted model; the tools are real.
"""
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
