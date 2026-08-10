"""Phase 6 tests — LLM provider, tool registry, and the agent service.

The LLM is mocked throughout (TRD §11): agent behavior is verified
deterministically, while the tools and database underneath are real.
"""
import pytest

from app.agent import agent_service, llm_provider, tool_registry
from app.config import settings
from tests.fake_llm import FailingChatModel, ScriptedChatModel, final_answer, tool_call

TOP_PRODUCTS_SQL = (
    "SELECT p.name AS name, SUM(oi.quantity * oi.unit_price) AS revenue "
    "FROM products p JOIN order_items oi ON oi.product_id = p.id "
    "GROUP BY p.name ORDER BY revenue DESC LIMIT 5"
)


def _scripted(*messages) -> ScriptedChatModel:
    return ScriptedChatModel(responses=list(messages))


# --- LLM provider configuration ------------------------------------------


def test_missing_api_key_raises_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    with pytest.raises(llm_provider.LlmConfigurationError, match="No LLM API key"):
        llm_provider.get_chat_model()


def test_unsupported_provider_raises_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "not-a-provider")
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    with pytest.raises(llm_provider.LlmConfigurationError, match="Unsupported LLM_PROVIDER"):
        llm_provider.get_chat_model()


def test_supported_providers_have_default_models():
    for provider in llm_provider.SUPPORTED_PROVIDERS:
        assert llm_provider.DEFAULT_MODELS[provider]


def test_explicit_model_overrides_default(monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "custom-model-name")
    assert llm_provider._resolve_model_name("openai") == "custom-model-name"


def test_configuration_error_message_never_contains_the_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "bogus")
    monkeypatch.setattr(settings, "llm_api_key", "super-secret-key")
    with pytest.raises(llm_provider.LlmConfigurationError) as exc:
        llm_provider.get_chat_model()
    assert "super-secret-key" not in str(exc.value)


# --- Tool registry --------------------------------------------------------


def test_registry_contains_get_schema_and_execute_query():
    assert tool_registry.registered_tool_names() == ["get_schema", "execute_query"]


def test_future_phase_tools_are_not_registered_yet():
    """Phases 8-10 tools must not appear until their phase."""
    registered = set(tool_registry.registered_tool_names())
    assert not registered & {"generate_chart", "explain_data", "generate_flowchart"}


def test_registered_tools_do_not_expose_session_id_to_the_llm():
    """Pending correction 2: session context travels out-of-band."""
    for tool in tool_registry.build_tools():
        assert "session_id" not in tool.args_schema.model_fields


def test_registered_tools_have_descriptions():
    for tool in tool_registry.build_tools():
        assert tool.description.strip()


# --- Agent tool invocation ------------------------------------------------


def test_agent_can_invoke_get_schema():
    model = _scripted(
        tool_call("get_schema", {}, "c1"),
        final_answer("This database has 7 tables."),
    )
    response = agent_service.run_agent("agent-s1", "What tables exist?", model=model)
    assert response.error is None
    assert response.message == "This database has 7 tables."


def test_agent_can_invoke_execute_query_and_fills_envelope():
    model = _scripted(
        tool_call("get_schema", {}, "c1"),
        tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
        final_answer("Here are the top 5 products by revenue."),
    )
    response = agent_service.run_agent(
        "agent-s2", "Show me the top 5 products by revenue.", model=model
    )

    assert response.error is None
    assert response.sql == TOP_PRODUCTS_SQL
    assert response.columns == ["name", "revenue"]
    assert len(response.rows) == 5
    # Results are ordered by revenue descending, and are real numbers.
    revenues = [row[1] for row in response.rows]
    assert revenues == sorted(revenues, reverse=True)
    assert all(isinstance(value, (int, float)) for value in revenues)


def test_agent_binds_only_the_two_phase_six_tools():
    model = _scripted(final_answer("Hello."))
    agent_service.run_agent("agent-s3", "hi", model=model)
    assert model.bound_tools == ["get_schema", "execute_query"]


def test_response_leaves_later_phase_fields_empty():
    """Charts/diagrams/explanations belong to Phases 8-10."""
    model = _scripted(
        tool_call("execute_query", {"sql": "SELECT name FROM products LIMIT 2"}, "c1"),
        final_answer("Two products."),
    )
    response = agent_service.run_agent("agent-s4", "list products", model=model)
    assert response.chart is None
    assert response.diagram is None
    assert response.explanation is None


# --- Dynamic database behavior -------------------------------------------


def test_agent_queries_a_differently_shaped_database(make_db):
    make_db(
        "lib-session",
        [
            "CREATE TABLE library_books (id INTEGER PRIMARY KEY, title TEXT, author TEXT)",
            "INSERT INTO library_books (title, author) VALUES ('Dune', 'Herbert')",
            "INSERT INTO library_books (title, author) VALUES ('Neuromancer', 'Gibson')",
        ],
    )
    model = _scripted(
        tool_call("get_schema", {}, "c1"),
        tool_call("execute_query", {"sql": "SELECT title, author FROM library_books"}, "c2"),
        final_answer("There are two books."),
    )
    response = agent_service.run_agent("lib-session", "List the books.", model=model)

    assert response.error is None
    assert response.columns == ["title", "author"]
    assert ["Dune", "Herbert"] in response.rows


def test_agent_uses_the_correct_session_database(make_db):
    """Session isolation: each agent run must hit its own active database."""
    make_db(
        "iso-a",
        ["CREATE TABLE only_in_a (id INTEGER PRIMARY KEY, marker TEXT)"],
    )

    # Session A sees its uploaded table.
    model_a = _scripted(
        tool_call("get_schema", {}, "c1"), final_answer("done")
    )
    agent_service.run_agent("iso-a", "schema?", model=model_a)

    # Session B (no upload) still sees the seeded demo database.
    model_b = _scripted(
        tool_call("execute_query", {"sql": "SELECT COUNT(*) AS c FROM products"}, "c1"),
        final_answer("done"),
    )
    response_b = agent_service.run_agent("iso-b", "how many products?", model=model_b)
    assert response_b.error is None
    assert response_b.rows[0][0] > 0

    # And session B cannot see session A's table.
    model_b2 = _scripted(
        tool_call("execute_query", {"sql": "SELECT * FROM only_in_a"}, "c1"),
        final_answer("done"),
    )
    response_b2 = agent_service.run_agent("iso-b", "select from only_in_a", model=model_b2)
    assert response_b2.error is not None
    assert response_b2.error.type == "sql_error"


# --- Graceful failure handling -------------------------------------------


def test_provider_failure_is_handled_gracefully():
    response = agent_service.run_agent("fail-1", "hello", model=FailingChatModel())
    assert response.error is not None
    assert response.error.type == "agent_error"
    assert "simulated provider outage" not in response.message


def test_missing_llm_configuration_returns_structured_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    response = agent_service.run_agent("fail-2", "hello")
    assert response.error is not None
    assert response.error.type == "llm_unavailable"
    assert response.rows == []


def test_sql_execution_failure_returned_gracefully():
    model = _scripted(
        tool_call("execute_query", {"sql": "SELECT nope FROM products"}, "c1"),
        final_answer("I could not run that query."),
    )
    response = agent_service.run_agent("fail-3", "bad query", model=model)
    assert response.error is not None
    assert response.error.type == "sql_error"
    assert response.sql == "SELECT nope FROM products"


def test_destructive_sql_from_the_model_is_rejected_by_the_tool():
    """Even if the model emits a write, the tool layer stops it."""
    model = _scripted(
        tool_call("execute_query", {"sql": "DROP TABLE customers"}, "c1"),
        final_answer("I cannot modify data."),
    )
    response = agent_service.run_agent("fail-4", "delete everything", model=model)
    assert response.error is not None
    assert response.error.type == "validation_rejected"

    # And the table is untouched.
    check = _scripted(
        tool_call("execute_query", {"sql": "SELECT COUNT(*) FROM customers"}, "c1"),
        final_answer("ok"),
    )
    assert agent_service.run_agent("fail-4", "count", model=check).rows[0][0] > 0


def test_empty_result_is_not_an_error():
    model = _scripted(
        tool_call("execute_query", {"sql": "SELECT name FROM products WHERE price < 0"}, "c1"),
        final_answer("No products matched."),
    )
    response = agent_service.run_agent("empty-1", "cheap products?", model=model)
    assert response.error is None
    assert response.rows == []
    assert response.message == "No products matched."


def test_truncation_is_reported_to_the_user(monkeypatch):
    monkeypatch.setattr(settings, "hard_row_ceiling", 3)
    model = _scripted(
        tool_call("execute_query", {"sql": "SELECT * FROM order_items"}, "c1"),
        final_answer("Here are the order items."),
    )
    response = agent_service.run_agent("trunc-1", "all order items", model=model)
    assert len(response.rows) == 3
    assert "truncated" in response.message.lower()


# --- Chat route integration ----------------------------------------------


def test_chat_route_invokes_the_agent_not_a_canned_response(client, monkeypatch):
    model = _scripted(
        tool_call("get_schema", {}, "c1"),
        tool_call("execute_query", {"sql": TOP_PRODUCTS_SQL}, "c2"),
        final_answer("Here are the top 5 products by revenue."),
    )
    monkeypatch.setattr(agent_service, "get_chat_model", lambda: model)

    response = client.post(
        "/api/chat",
        headers={"X-Session-Id": "route-1"},
        json={"message": "Show me the top 5 products by revenue."},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["message"] != "Chat agent will be connected in Batch 2."
    assert body["sql"] == TOP_PRODUCTS_SQL
    assert body["columns"] == ["name", "revenue"]
    assert len(body["rows"]) == 5
    assert body["error"] is None


def test_chat_route_preserves_the_response_envelope(client, monkeypatch):
    model = _scripted(final_answer("Hello."))
    monkeypatch.setattr(agent_service, "get_chat_model", lambda: model)

    body = client.post("/api/chat", json={"message": "hi"}).json()
    assert set(body) == {
        "message",
        "sql",
        "columns",
        "rows",
        "chart",
        "diagram",
        "explanation",
        "error",
    }


def test_chat_route_still_validates_input(client):
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={}).status_code == 422


def test_chat_route_returns_structured_error_without_llm(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    body = client.post("/api/chat", json={"message": "hi"}).json()
    assert body["error"]["type"] == "llm_unavailable"
    assert body["rows"] == []


def test_chat_route_uses_the_session_from_the_header(client, monkeypatch, make_db):
    make_db("hdr-session", ["CREATE TABLE marker_table (id INTEGER PRIMARY KEY)"])
    model = _scripted(
        tool_call("execute_query", {"sql": "SELECT COUNT(*) AS c FROM marker_table"}, "c1"),
        final_answer("Counted."),
    )
    monkeypatch.setattr(agent_service, "get_chat_model", lambda: model)

    body = client.post(
        "/api/chat",
        headers={"X-Session-Id": "hdr-session"},
        json={"message": "count marker rows"},
    ).json()
    assert body["error"] is None
    assert body["columns"] == ["c"]
