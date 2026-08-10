import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.session import store as session_store


@pytest.fixture(autouse=True)
def _isolated_upload_dir(tmp_path, monkeypatch):
    """Every test uploads into its own throwaway directory instead of the
    real backend/data/uploads, and starts with a clean session store."""
    monkeypatch.setattr(settings, "database_upload_dir", str(tmp_path))
    session_store._sessions.clear()
    yield
    session_store._sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_db(tmp_path):
    """Builds a real SQLite file with caller-supplied DDL/DML and registers
    it as a session's active database. Used to prove the tools adapt to any
    schema without code changes."""
    import sqlite3

    from app.db import database_manager

    counter = {"n": 0}

    def _make(session_id: str, statements: list[str], filename: str | None = None) -> None:
        counter["n"] += 1
        name = filename or f"test_{counter['n']}.db"
        path = tmp_path / f"src_{counter['n']}.db"
        conn = sqlite3.connect(path)
        # Forces SQLite to write the file header even when `statements` is
        # empty, so an intentionally table-less database is still a valid file.
        conn.execute("PRAGMA user_version = 1")
        for statement in statements:
            conn.execute(statement)
        conn.commit()
        conn.close()
        database_manager.register_database(session_id, name, path.read_bytes())

    return _make
