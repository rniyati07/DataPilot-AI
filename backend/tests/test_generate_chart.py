"""Phase 8 tests — Tool 3 `generate_chart` (04_AGENT_TOOLS.md §12).

The builder is deterministic pure code: no LLM, no database. Agent-level
tests drive the exact tool-call sequence with the scripted model.
"""
import pytest

from app.agent import agent_service, tool_registry
from app.tools.generate_chart import GenerateChartInput, generate_chart
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call

TOP_PRODUCTS_SQL = (
    "SELECT p.name AS name, SUM(oi.quantity * oi.unit_price) AS revenue "
    "FROM products p JOIN order_items oi ON oi.product_id = p.id "
    "GROUP BY p.name ORDER BY revenue DESC LIMIT 5"
)


def _bar_data():
    return {
        "columns": ["name", "revenue"],
        "rows": [
            ["Wireless Earbuds Pro", 18420.5],
            ["Smart Fitness Band", 15310.0],
            ["Noise-Cancelling Headset", 12050.0],
        ],
    }


def _date_data():
    return {
        "columns": ["order_date", "sales"],
        "rows": [
            ["2026-01-01", 100],
            ["2026-01-02", 150],
            ["2026-01-03", 90],
        ],
    }


# --- Chart-type selection (deterministic rules) ----------------------------


def test_bar_for_categorical_plus_numeric():
    result = generate_chart("s1", _bar_data(), intent="compare product revenue")
    assert result["success"] is True
    assert result["chart_type"] == "bar"
    assert result["plotly_spec"]["data"][0]["type"] == "bar"
    assert result["title"] == "Revenue by Name"
    assert result["x_label"] == "Name"
    assert result["y_label"] == "Revenue"
    assert result["plotly_spec"]["data"][0]["x"] == ["Wireless Earbuds Pro", "Smart Fitness Band", "Noise-Cancelling Headset"]


def test_line_for_date_plus_numeric():
    result = generate_chart("s1", _date_data(), intent="trend over time")
    assert result["success"] is True
    assert result["chart_type"] == "line"
    assert result["plotly_spec"]["data"][0]["type"] == "scatter"
    assert result["plotly_spec"]["data"][0]["mode"] == "lines+markers"


def test_pie_when_intent_suggests_share():
    result = generate_chart("s1", _bar_data(), intent="share of total revenue by product")
    assert result["success"] is True
    assert result["chart_type"] == "pie"
    assert result["plotly_spec"]["data"][0]["type"] == "pie"


def test_same_shape_defaults_to_bar_without_share_intent():
    result = generate_chart("s1", _bar_data())
    assert result["chart_type"] == "bar"


def test_scatter_for_two_numerics_with_correlation_intent():
    data = {"columns": ["price", "units_sold"], "rows": [[10, 500], [20, 300], [30, 200], [40, 150]]}
    result = generate_chart("s1", data, intent="correlation between price and units sold")
    assert result["success"] is True
    assert result["chart_type"] == "scatter"
    assert result["plotly_spec"]["data"][0]["mode"] == "markers"


def test_single_scalar_returns_none_not_error():
    result = generate_chart("s1", {"columns": ["total"], "rows": [[42]]})
    assert result["success"] is True
    assert result["chart_type"] == "none"
    assert "scalar" in result["reason"].lower()


def test_empty_rows_returns_none_not_crash():
    result = generate_chart("s1", {"columns": ["name", "revenue"], "rows": []})
    assert result["success"] is True
    assert result["chart_type"] == "none"
    assert result["reason"]


def test_high_cardinality_categories_fall_back_to_none():
    names = [f"Customer {index}" for index in range(200)]
    rows = [[name, index] for index, name in enumerate(names)]
    result = generate_chart("s1", {"columns": ["customer", "spend"], "rows": rows})
    assert result["success"] is True
    assert result["chart_type"] == "none"
    assert "200 distinct" in result["reason"]


def test_all_text_data_returns_none():
    result = generate_chart(
        "s1",
        {"columns": ["a", "b"], "rows": [["x", "y"], ["p", "q"]]},
    )
    assert result["success"] is True
    assert result["chart_type"] == "none"


def test_labels_always_populated_when_chart_produced():
    result = generate_chart("s1", _bar_data())
    assert result["title"]
    assert result["x_label"]
    assert result["y_label"]


# --- Shape validation ------------------------------------------------------


def test_row_length_mismatch_is_invalid_data_shape():
    data = {"columns": ["a", "b"], "rows": [[1, 2], [3]]}
    result = generate_chart("s1", data)
    assert result["success"] is False
    assert result["error"]["type"] == "invalid_data_shape"


def test_empty_columns_is_invalid_data_shape():
    result = generate_chart("s1", {"columns": [], "rows": []})
    assert result["success"] is False
    assert result["error"]["type"] == "invalid_data_shape"


def test_unexpected_exception_becomes_unsupported(monkeypatch):
    from app.viz import plotly_builder

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(plotly_builder, "build_chart_spec", _boom)
    result = generate_chart("s1", _bar_data())
    assert result["success"] is False
    assert result["error"]["type"] == "unsupported"


# --- Input model -----------------------------------------------------------


def test_input_model_rejects_blank_intent():
    with pytest.raises(ValueError):
        GenerateChartInput(data={"columns": ["a"], "rows": [[1]]}, intent="   ")


def test_input_model_defaults():
    parsed = GenerateChartInput(data={"columns": ["a"], "rows": [[1]]})
    assert parsed.intent is None
    assert parsed.x_field is None
    assert parsed.y_field is None


def test_input_model_has_no_session_id_field():
    assert "session_id" not in GenerateChartInput.model_fields


# --- Registry + agent wiring ----------------------------------------------


def test_generate_chart_is_registered():
    assert "generate_chart" in tool_registry.registered_tool_names()


def test_agent_chart_appears_in_response_envelope():
    model = ScriptedChatModel(
        responses=[
            tool_call("get_schema", {}, "c1"),
            tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
            tool_call(
                "generate_chart",
                {
                    "data": {
                        "columns": ["name", "revenue"],
                        "rows": [
                            ["Wireless Earbuds Pro", 18420.5],
                            ["Smart Fitness Band", 15310.0],
                            ["Noise-Cancelling Headset", 12050.0],
                        ],
                    },
                    "intent": "compare product revenue",
                },
                "c3",
            ),
            final_answer("Here is the revenue comparison chart."),
        ]
    )
    response = agent_service.run_agent("chart-agent", "compare product revenue", model=model)

    assert response.error is None
    assert response.chart is not None
    assert response.chart["chart_type"] == "bar"
    assert response.chart["plotly_spec"]["data"][0]["type"] == "bar"


def test_turn_without_chart_leaves_chart_empty():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "SELECT name FROM products LIMIT 2"}, "c1"),
            final_answer("Two products."),
        ]
    )
    response = agent_service.run_agent("chart-empty", "list products", model=model)
    assert response.chart is None
