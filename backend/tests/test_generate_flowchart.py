"""Phase 10 tests — Tool 4 `generate_flowchart` (04_AGENT_TOOLS.md §12).

The Mermaid builder is deterministic pure code; ER diagrams are proven against
non-e-commerce schemas so nothing is hardcoded to the seeded database.
"""
import pytest

from app.agent import agent_service, tool_registry
from app.diagrams import mermaid_builder
from app.tools.generate_flowchart import GenerateFlowchartInput, generate_flowchart
from tests.fake_llm import ScriptedChatModel, final_answer, tool_call


def _employees_schema():
    return [
        {
            "name": "departments",
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "name", "type": "TEXT", "nullable": False, "primary_key": False},
            ],
            "foreign_keys": [],
        },
        {
            "name": "employees",
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "department_id", "type": "INTEGER", "nullable": True, "primary_key": False},
                {"name": "name", "type": "TEXT", "nullable": False, "primary_key": False},
            ],
            "foreign_keys": [
                {"column": "department_id", "references_table": "departments", "references_column": "id"}
            ],
        },
    ]


# --- ER diagram (live schema, never hardcoded) -----------------------------


def test_er_diagram_reflects_live_schema():
    result = generate_flowchart("s1", "er", {"schema": _employees_schema()})
    assert result["success"] is True
    assert result["diagram_type"] == "er"
    syntax = result["mermaid_syntax"]
    assert syntax.startswith("erDiagram")
    assert "EMPLOYEES {" in syntax
    assert "DEPARTMENTS {" in syntax
    assert "int id PK" in syntax
    # Relationship derived from the FK column name — not a hardcoded semantic.
    assert "DEPARTMENTS ||--o{ EMPLOYEES : department_id" in syntax


def test_er_diagram_not_hardcoded_to_ecommerce():
    result = generate_flowchart("s1", "er", {"schema": _employees_schema()})
    syntax = result["mermaid_syntax"]
    assert "CUSTOMERS" not in syntax
    assert "ORDERS" not in syntax
    assert "PRODUCTS" not in syntax


def test_er_diagram_auto_discovers_active_database(make_db):
    make_db(
        "er-discover",
        [
            "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE employees (id INTEGER PRIMARY KEY, department_id INTEGER REFERENCES departments(id), name TEXT)",
        ],
    )
    result = generate_flowchart("er-discover", "er", {})
    assert result["success"] is True
    syntax = result["mermaid_syntax"]
    assert "EMPLOYEES {" in syntax
    assert "DEPARTMENTS ||--o{ EMPLOYEES : department_id" in syntax


def test_er_diagram_unavailable_database_returns_schema_unavailable(monkeypatch):
    from app.db import access_layer

    def _boom(*args, **kwargs):
        raise access_layer.DatabaseUnavailableError("nope")

    monkeypatch.setattr(access_layer, "discover_schema", _boom)
    result = generate_flowchart("er-nodb", "er", {})
    assert result["success"] is False
    assert result["error"]["type"] == "schema_unavailable"


# --- Process diagram (agent-supplied steps only) ---------------------------


def test_process_diagram_from_steps():
    steps = [
        {"id": "s1", "label": "Order placed", "next": ["s2"]},
        {"id": "s2", "label": "Payment processed", "next": ["s3"]},
        {"id": "s3", "label": "Shipped", "next": []},
    ]
    result = generate_flowchart("s1", "process", {"description": "how orders move", "steps": steps})
    assert result["success"] is True
    syntax = result["mermaid_syntax"]
    assert syntax.startswith("flowchart TD")
    assert 's1["Order placed"]' in syntax
    assert "s1 --> s2" in syntax
    assert "s2 --> s3" in syntax
    assert result["title"] == "How Orders Move"


def test_process_diagram_requires_steps():
    result = generate_flowchart("s1", "process", {"steps": []})
    assert result["success"] is False
    assert result["error"]["type"] == "generation_failed"
    assert "steps are required" in result["error"]["message"]


def test_process_diagram_rejects_duplicate_ids():
    steps = [
        {"id": "s1", "label": "a", "next": []},
        {"id": "s1", "label": "b", "next": []},
    ]
    result = generate_flowchart("s1", "process", {"steps": steps})
    assert result["success"] is False
    assert "unique" in result["error"]["message"]


def test_process_diagram_rejects_unknown_next():
    steps = [{"id": "s1", "label": "a", "next": ["ghost"]}]
    result = generate_flowchart("s1", "process", {"steps": steps})
    assert result["success"] is False
    assert "references unknown step" in result["error"]["message"]


def test_process_diagram_escapes_dangerous_label_characters():
    steps = [{"id": "s1", "label": 'Order "placed" [now] {fast}', "next": []}]
    result = generate_flowchart("s1", "process", {"steps": steps})
    assert result["success"] is True
    syntax = result["mermaid_syntax"]
    assert '"' not in syntax.split('s1["', 1)[1].split('"]', 1)[0]
    assert mermaid_builder.validate_mermaid(syntax)


# --- Decision diagram (bonus) ----------------------------------------------


def test_decision_diagram_from_entities():
    result = generate_flowchart("s1", "decision", {"description": "approval path", "entities": ["Approved", "Rejected"]})
    assert result["success"] is True
    syntax = result["mermaid_syntax"]
    assert syntax.startswith("flowchart TD")
    assert 'decision{"approval path?"}' in syntax
    assert '|"Approved"|' in syntax


def test_decision_diagram_requires_context():
    result = generate_flowchart("s1", "decision", {})
    assert result["success"] is False
    assert result["error"]["type"] == "generation_failed"


# --- Structural validation -------------------------------------------------


@pytest.mark.parametrize(
    "syntax",
    [
        "erDiagram\n    A ||--o{ B : id",
        'flowchart TD\n    a["x"] --> b["y"]',
        'graph TD\n    a{{"q?"}} -->|"yes"| b["done"]',
    ],
)
def test_valid_mermaid_passes_validation(syntax):
    assert mermaid_builder.validate_mermaid(syntax)


@pytest.mark.parametrize(
    "syntax",
    [
        "",
        "not a diagram",
        'flowchart TD\n    a["x"] --> b["y"',  # unbalanced bracket outside quotes
        'flowchart TD\n    a{{"q?"',  # unbalanced brace outside quotes
    ],
)
def test_invalid_mermaid_fails_validation(syntax):
    assert mermaid_builder.validate_mermaid(syntax) is False


# --- Input model -----------------------------------------------------------


def test_input_model_rejects_unknown_diagram_type():
    with pytest.raises(ValueError):
        GenerateFlowchartInput(diagram_type="pie", context={})


def test_input_model_has_no_session_id_field():
    assert "session_id" not in GenerateFlowchartInput.model_fields


# --- Registry + agent wiring ----------------------------------------------


def test_generate_flowchart_is_registered():
    assert "generate_flowchart" in tool_registry.registered_tool_names()


def test_agent_er_diagram_appears_in_response(monkeypatch):
    model = ScriptedChatModel(
        responses=[
            tool_call("get_schema", {}, "c1"),
            tool_call("generate_flowchart", {"diagram_type": "er", "context": {}}, "c2"),
            final_answer("Here is the ER diagram."),
        ]
    )
    response = agent_service.run_agent("er-agent", "draw the er diagram", model=model)
    assert response.error is None
    assert response.diagram is not None
    assert response.diagram.startswith("erDiagram")


def test_agent_process_diagram_appears_in_response(monkeypatch):
    model = ScriptedChatModel(
        responses=[
            tool_call(
                "generate_flowchart",
                {
                    "diagram_type": "process",
                    "context": {
                        "steps": [
                            {"id": "s1", "label": "Order placed", "next": ["s2"]},
                            {"id": "s2", "label": "Shipped", "next": []},
                        ]
                    },
                },
                "c2",
            ),
            final_answer("Here is the process flow."),
        ]
    )
    response = agent_service.run_agent("process-agent", "how do orders flow", model=model)
    assert response.error is None
    assert response.diagram is not None
    assert response.diagram.startswith("flowchart TD")


def test_turn_without_diagram_leaves_diagram_empty():
    model = ScriptedChatModel(
        responses=[
            tool_call("execute_query", {"sql": "SELECT name FROM products LIMIT 2"}, "c1"),
            final_answer("Two products."),
        ]
    )
    response = agent_service.run_agent("no-diagram", "list products", model=model)
    assert response.diagram is None
