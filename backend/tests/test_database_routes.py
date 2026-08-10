from app.db import access_layer
from tests.helpers import make_sqlite_bytes


def test_current_database_defaults_to_ecommerce(client):
    r = client.get("/api/database/current", headers={"X-Session-Id": "s1"})
    assert r.status_code == 200
    assert r.json() == {"name": "ecommerce.db", "source": "default", "active": True}


def test_upload_valid_db_becomes_active(client):
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("mydata.db", make_sqlite_bytes(), "application/octet-stream")},
    )
    assert r.status_code == 200
    assert r.json() == {"name": "mydata.db", "source": "upload", "active": True}

    r = client.get("/api/database/current", headers={"X-Session-Id": "s1"})
    assert r.json()["source"] == "upload"
    assert r.json()["name"] == "mydata.db"


def test_upload_valid_sqlite_extension(client):
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("mydata.sqlite", make_sqlite_bytes(), "application/octet-stream")},
    )
    assert r.status_code == 200


def test_upload_valid_sqlite3_extension(client):
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("mydata.sqlite3", make_sqlite_bytes(), "application/octet-stream")},
    )
    assert r.status_code == 200


def test_upload_invalid_file_rejected(client):
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("notes.txt", b"just some text", "text/plain")},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["type"] == "invalid_upload"


def test_upload_non_sqlite_with_allowed_extension_rejected(client):
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("fake.db", b"not really sqlite data here", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_response_never_exposes_filesystem_path(client):
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("mydata.db", make_sqlite_bytes(), "application/octet-stream")},
    )
    body = r.json()
    assert "path" not in body
    assert ":" not in body["name"]  # no drive letter / absolute path leaking through


def test_replace_active_database(client):
    client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("database_a.db", make_sqlite_bytes("a"), "application/octet-stream")},
    )
    r = client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("database_b.db", make_sqlite_bytes("b"), "application/octet-stream")},
    )
    assert r.json()["name"] == "database_b.db"

    r = client.get("/api/database/current", headers={"X-Session-Id": "s1"})
    assert r.json()["name"] == "database_b.db"


def test_delete_reverts_to_default(client):
    client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "s1"},
        files={"file": ("mydata.db", make_sqlite_bytes(), "application/octet-stream")},
    )
    r = client.delete("/api/database/current", headers={"X-Session-Id": "s1"})
    assert r.status_code == 200
    assert r.json()["source"] == "default"


def test_session_isolation_across_uploads(client):
    client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "session-A"},
        files={"file": ("a.db", make_sqlite_bytes("table_a"), "application/octet-stream")},
    )

    r_a = client.get("/api/database/current", headers={"X-Session-Id": "session-A"})
    r_b = client.get("/api/database/current", headers={"X-Session-Id": "session-B"})

    assert r_a.json()["source"] == "upload"
    assert r_b.json()["source"] == "default"


def test_differently_shaped_database_discovered_with_no_code_change(client):
    client.post(
        "/api/database/upload",
        headers={"X-Session-Id": "custom-session"},
        files={"file": ("custom.db", make_sqlite_bytes("custom_table"), "application/octet-stream")},
    )
    tables = access_layer.list_tables_for_session("custom-session")
    assert tables == ["custom_table"]
