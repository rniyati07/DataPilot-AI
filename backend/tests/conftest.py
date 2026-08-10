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
