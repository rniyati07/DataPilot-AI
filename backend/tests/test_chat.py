def test_chat_returns_placeholder_envelope(client):
    r = client.post("/api/chat", json={"message": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Chat agent will be connected in Batch 2."
    for key in ("sql", "chart", "diagram", "explanation", "error"):
        assert body[key] is None
    assert body["columns"] == []
    assert body["rows"] == []


def test_chat_rejects_empty_message(client):
    r = client.post("/api/chat", json={"message": ""})
    assert r.status_code == 422


def test_chat_rejects_malformed_payload(client):
    r = client.post("/api/chat", json={})
    assert r.status_code == 422
