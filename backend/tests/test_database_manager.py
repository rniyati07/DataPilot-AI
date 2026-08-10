import pytest

from app.db import database_manager
from tests.helpers import make_sqlite_bytes


def test_validate_upload_accepts_valid_sqlite():
    content = make_sqlite_bytes()
    database_manager.validate_upload("sample.db", content)  # should not raise


@pytest.mark.parametrize("filename", ["sample.txt", "sample", "sample.exe", "sample.DBX"])
def test_validate_upload_rejects_unsupported_extension(filename):
    with pytest.raises(database_manager.UploadValidationError):
        database_manager.validate_upload(filename, make_sqlite_bytes())


def test_validate_upload_rejects_non_sqlite_content():
    with pytest.raises(database_manager.UploadValidationError):
        database_manager.validate_upload("sample.db", b"not a real sqlite file at all")


def test_validate_upload_rejects_empty_file():
    with pytest.raises(database_manager.UploadValidationError):
        database_manager.validate_upload("sample.db", b"")


def test_validate_upload_rejects_oversized_file(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "database_upload_max_mb", 0)
    with pytest.raises(database_manager.UploadValidationError):
        database_manager.validate_upload("sample.db", make_sqlite_bytes())


def test_validate_upload_accepts_case_insensitive_extension():
    database_manager.validate_upload("sample.SQLITE3", make_sqlite_bytes())


def test_register_database_stores_under_generated_name(tmp_path):
    content = make_sqlite_bytes()
    display_name = database_manager.register_database("session-x", "my data.db", content)
    assert display_name == "my data.db"

    stored_path = database_manager.get_active_database_path("session-x")
    assert stored_path.exists()
    assert stored_path.name != "my data.db"  # generated filename, not the original


def test_register_database_sanitizes_path_traversal_filename():
    content = make_sqlite_bytes()
    display_name = database_manager.register_database(
        "session-y", "../../../etc/passwd.db", content
    )
    assert display_name == "passwd.db"
    stored_path = database_manager.get_active_database_path("session-y")
    # Must remain inside the configured upload directory.
    from app.config import settings

    assert stored_path.parent == settings.upload_dir_path


def test_get_active_database_defaults_to_seed_db():
    from app.config import settings

    path = database_manager.get_active_database_path("brand-new-session")
    assert path == settings.default_database_path


def test_get_active_database_info_reports_default():
    name, source = database_manager.get_active_database_info("brand-new-session")
    assert source == "default"
    assert name == "ecommerce.db"


def test_uploading_twice_replaces_not_accumulates(tmp_path):
    database_manager.register_database("session-z", "first.db", make_sqlite_bytes("a"))
    first_path = database_manager.get_active_database_path("session-z")
    assert first_path.exists()

    database_manager.register_database("session-z", "second.db", make_sqlite_bytes("b"))
    second_path = database_manager.get_active_database_path("session-z")

    assert second_path != first_path
    assert not first_path.exists()  # old upload cleaned up
    assert second_path.exists()


def test_clear_active_database_reverts_to_default():
    from app.config import settings

    database_manager.register_database("session-clear", "up.db", make_sqlite_bytes())
    assert database_manager.get_active_database_info("session-clear")[1] == "upload"

    database_manager.clear_active_database("session-clear")
    name, source = database_manager.get_active_database_info("session-clear")
    assert source == "default"
    assert database_manager.get_active_database_path("session-clear") == settings.default_database_path


def test_sessions_do_not_share_active_database():
    database_manager.register_database("session-1", "a.db", make_sqlite_bytes())
    name_1, source_1 = database_manager.get_active_database_info("session-1")
    name_2, source_2 = database_manager.get_active_database_info("session-2")

    assert source_1 == "upload"
    assert source_2 == "default"
    assert name_1 != name_2
