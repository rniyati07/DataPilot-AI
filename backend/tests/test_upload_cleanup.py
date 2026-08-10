"""Windows SQLite cleanup — uploaded files must be removable after the
session's database lifecycle ends (orphan-file hardening).

Root cause (reproduced on Windows): SQLAlchemy's connection pool retains an
open connection to an uploaded database file after a query, and Windows
blocks unlink() on the open handle. The old cleanup path swallowed the
OSError, leaving orphan files in the upload directory. The fix disposes the
session's cached engines before removing the file.

The file-removal assertions are the strongest portable regression signal:
they fail on Windows before the fix and pass after it.
"""
import sqlite3

from app.config import settings
from app.db import access_layer
from app.db import database_manager
from app.db import engine as engine_factory


def _make_real_db(tmp_path, statements: list[str]) -> bytes:
    path = tmp_path / "src.db"
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA user_version = 1")
    for statement in statements:
        conn.execute(statement)
    conn.commit()
    conn.close()
    return path.read_bytes()


def test_upload_creates_file_in_upload_dir(tmp_path):
    database_manager.register_database(
        "s", "up.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    stored = database_manager.get_active_database_path("s")
    assert stored.exists()
    assert stored.parent == settings.upload_dir_path


def test_uploaded_db_becomes_active(tmp_path):
    database_manager.register_database(
        "s", "up.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    name, source = database_manager.get_active_database_info("s")
    assert source == "upload"
    assert name == "up.db"


def test_uploaded_db_can_be_queried(tmp_path):
    database_manager.register_database(
        "s",
        "up.db",
        _make_real_db(
            tmp_path,
            [
                "CREATE TABLE emp (id INTEGER PRIMARY KEY, name TEXT)",
                "INSERT INTO emp VALUES (1, 'Ada'), (2, 'Grace')",
            ],
        ),
    )
    columns, rows, _ = access_layer.execute_read_only(
        "s", "SELECT name FROM emp ORDER BY id", 200
    )
    assert columns == ["name"]
    assert rows == [["Ada"], ["Grace"]]


def test_clear_removes_uploaded_file_even_after_engine_connection(tmp_path):
    """The orphan regression: a query opens the pooled engine, then cleanup
    must still be able to remove the file (fails on Windows pre-fix)."""
    database_manager.register_database(
        "s", "up.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    stored = database_manager.get_active_database_path("s")
    access_layer.execute_read_only("s", "SELECT 1", 200)  # opens + pools a connection

    database_manager.clear_active_database("s")
    assert not stored.exists()


def test_clear_does_not_touch_default_database(tmp_path):
    database_manager.register_database(
        "s", "up.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    database_manager.clear_active_database("s")
    assert settings.default_database_path.exists()  # seeded demo DB untouched
    assert database_manager.get_active_database_path("s") == settings.default_database_path


def test_repeated_cleanup_is_safe(tmp_path):
    database_manager.register_database(
        "s", "up.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    database_manager.clear_active_database("s")
    database_manager.clear_active_database("s")  # second call, nothing to remove
    assert database_manager.get_active_database_path("s") == settings.default_database_path


def test_cleanup_is_safe_when_file_already_missing(tmp_path):
    database_manager.register_database(
        "s", "up.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    stored = database_manager.get_active_database_path("s")
    stored.unlink()  # simulate external deletion
    database_manager.clear_active_database("s")  # must not raise
    assert database_manager.get_active_database_path("s") == settings.default_database_path


def test_reupload_removes_previous_uploaded_file(tmp_path):
    database_manager.register_database(
        "s", "first.db", _make_real_db(tmp_path, ["CREATE TABLE t (x INTEGER)"])
    )
    first = database_manager.get_active_database_path("s")
    access_layer.execute_read_only("s", "SELECT 1", 200)
    database_manager.register_database(
        "s", "second.db", _make_real_db(tmp_path, ["CREATE TABLE u (y INTEGER)"])
    )
    assert not first.exists()
    assert database_manager.get_active_database_path("s").exists()


def test_dispose_engine_evicts_both_registries(tmp_path):
    path = tmp_path / "engine.db"
    sqlite3.connect(path).close()
    first_ro = engine_factory.get_readonly_engine(path)
    first_rw = engine_factory.get_engine(path)
    engine_factory.dispose_engine(path)
    assert engine_factory.get_readonly_engine(path) is not first_ro
    assert engine_factory.get_engine(path) is not first_rw


def test_dispose_engine_unknown_path_is_noop(tmp_path):
    engine_factory.dispose_engine(tmp_path / "never_created.db")  # must not raise
