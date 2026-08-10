"""Phase 9 tests — Tool 5 `explain_data` (04_AGENT_TOOLS.md §12).

The tool's LLM call is stubbed via the `_llm_factory` seam; empty and large
result paths are deterministic.
"""
from types import SimpleNamespace

import pytest

import app.tools.explain_data as explain_data_module

from app.agent import agent_service, tool_registry
from app.config import settings
from app.tools.explain_data import ExplainDataInput, explain_data
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call

TOP_PRODUCTS_SQL = (
    "SELECT p.name AS name, SUM(oi.quantity * oi.unit_price) AS revenue "
    "FROM products p JOIN order_items oi ON oi.product_id = p.id "
    "GROUP BY p.name ORDER BY revenue DESC LIMIT 5"
)


class FakeExplainModel:
    """Returns a canned explanation and records the prompt it received."""

    def __init__(self, text="Wireless Earbuds Pro leads the list."):
        self.text = text
        self.prompts = []

    def invoke(self, messages):
        self.prompts.append(messages[0].content)
        return SimpleNamespace(content=self.text)


def _patch_llm(monkeypatch, model):
    monkeypatch.setattr(explain_data_module, "_llm_factory", lambda: model)


def _rows(*items):
    return {"columns": ["name", "revenue"], "rows": [[name, value] for name, value in items]}


# --- Empty result fast path -------------------------------------------------


def test_empty_rows_returns_deterministic_message_without_llm(monkeypatch):
    def _fail(*args, **kwargs):
        raise AssertionError("LLM must not be called for empty results")

    monkeypatch.setattr(explain_data_module, "_llm_factory", _fail)
    result = explain_data("s1", {"columns": ["name", "revenue"], "rows": []}, "top products")
    assert result["success"] is True
    assert "didn't find any matching data" in result["explanation"]


# --- LLM-grounded explanation ----------------------------------------------


def test_explanation_from_llm_and_prompt_grounded_in_data(monkeypatch):
    model = FakeExplainModel()
    _patch_llm(monkeypatch, model)
    data = _rows(("Wireless Earbuds Pro", 18420.5), ("Smart Fitness Band", 15310.0))
    result = explain_data("s1", data, "What are the top products?", chart={"chart_type": "bar", "title": "Revenue"})

    assert result["success"] is True
    assert result["explanation"] == model.text
    assert len(model.prompts) == 1
    prompt = model.prompts[0]
    # The prompt is constrained to the actual data — no room for invention.
    assert "Wireless Earbuds Pro" in prompt
    assert "18420.5" in prompt
    assert "Smart Fitness Band" in prompt
    assert "bar" in prompt  # chart hint included


def test_correction_note_is_included_in_prompt(monkeypatch):
    model = FakeExplainModel()
    _patch_llm(monkeypatch, model)
    explain_data("s1", _rows(("A", 1)), "q", correction_note="My first attempt failed.")
    assert "My first attempt failed." in model.prompts[0]


# --- Large-result aggregation path -----------------------------------------


def test_large_result_aggregates_before_llm(monkeypatch):
    monkeypatch.setattr(settings, "explain_summarize_after_rows", 3)
    model = FakeExplainModel()
    _patch_llm(monkeypatch, model)
    rows = [(f"Product {i}", i * 100) for i in range(10)]
    result = explain_data("s1", _rows(*rows), "list everything")

    assert result["success"] is True
    prompt = model.prompts[0]
    assert "Total rows: 10" in prompt
    assert "min 0" in prompt
    assert "max 900" in prompt
    # The raw full row list is never sent wholesale — a mid-list row is absent.
    assert "Product 5" not in prompt
    # The top rows are still shown as bounded context.
    assert "Product 9" in prompt


# --- Deterministic fallback on LLM failure ---------------------------------


def test_llm_failure_falls_back_to_top_result(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(explain_data_module, "_llm_factory", _boom)
    result = explain_data("s1", _rows(("Wireless Earbuds Pro", 18420.5), ("B", 10)), "top product")
    assert result["success"] is True
    assert "top result" in result["explanation"].lower()
    assert "Wireless Earbuds Pro" in result["explanation"]
    assert "18420.5" in result["explanation"]


# --- Input model -----------------------------------------------------------


def test_input_model_requires_question():
    with pytest.raises(ValueError):
        ExplainDataInput(data={"columns": ["a"], "rows": [[1]]}, question="   ")


def test_input_model_rejects_unknown_chart_type():
    with pytest.raises(ValueError):
        ExplainDataInput(
            data={"columns": ["a"], "rows": [[1]]},
            question="q",
            chart={"chart_type": "donut", "title": "x"},
        )


def test_input_model_defaults():
    parsed = ExplainDataInput(data={"columns": ["a"], "rows": [[1]]}, question="q")
    assert parsed.chart is None
    assert parsed.correction_note is None


def test_input_model_has_no_session_id_field():
    assert "session_id" not in ExplainDataInput.model_fields


# --- Registry + agent wiring ----------------------------------------------


def test_explain_data_is_registered():
    assert "explain_data" in tool_registry.registered_tool_names()


def test_agent_explanation_appears_in_response_envelope(monkeypatch):
    _patch_llm(monkeypatch, FakeExplainModel("The top product is Wireless Earbuds Pro."))
    model = ScriptedChatModel(
        responses=[
            tool_call("get_schema", {}, "c1"),
            tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
            tool_call(
                "explain_data",
                {
                    "data": {
                        "columns": ["name", "revenue"],
                        "rows": [["Wireless Earbuds Pro", 18420.5], ["Smart Fitness Band", 15310.0]],
                    },
                    "question": "What are the top products by revenue?",
                },
                "c3",
            ),
            final_answer("Here's the explanation."),
        ]
    )
    response = agent_service.run_agent("explain-agent", "top products", model=model)
    assert response.error is None
    assert response.explanation == "The top product is Wireless Earbuds Pro."
