def test_schema_stub_returns_not_implemented(client):
    r = client.get("/api/schema")
    assert r.status_code == 200
    assert r.json()["status"] == "not_implemented"
