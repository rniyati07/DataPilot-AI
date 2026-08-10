"""Chat endpoint contract tests.

The Phase 2 canned response was replaced by the real agent in Phase 6 —
agent behavior itself is covered in `test_agent.py`. What remains here is
the endpoint's request-validation contract, which must not regress.
"""


def test_chat_rejects_empty_message(client):
    assert client.post("/api/chat", json={"message": ""}).status_code == 422


def test_chat_rejects_malformed_payload(client):
    assert client.post("/api/chat", json={}).status_code == 422


def test_chat_rejects_oversized_message(client):
    assert client.post("/api/chat", json={"message": "x" * 5000}).status_code == 422


def test_chat_no_longer_returns_the_phase_two_placeholder(client, monkeypatch):
    """Regression guard: the canned Batch 1 response must be gone."""
    from app.agent import agent_service
    from tests.fake_llm import ScriptedChatModel, final_answer

    monkeypatch.setattr(
        agent_service,
        "get_chat_model",
        lambda: ScriptedChatModel(responses=[final_answer("A real agent answer.")]),
    )
    body = client.post("/api/chat", json={"message": "hello"}).json()
    assert body["message"] == "A real agent answer."
    assert body["message"] != "Chat agent will be connected in Batch 2."
