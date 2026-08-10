"""Database Manager (TRD §5, Architecture §2/§13).

Owns the *active database* concept: validates uploads, stores them under a
controlled directory with a generated filename, and maps
`session_id -> active database file`. The agent/tools (Batch 2) and the
Database Access Layer never decide which file is active themselves — they
always ask this module.
"""
import sqlite3
import uuid
from pathlib import Path

from app.config import settings
from app.session import store as session_store

ALLOWED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}
SQLITE_HEADER = b"SQLite format 3\x00"


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation. Message is user-safe."""


def _ensure_upload_dir() -> Path:
    upload_dir = settings.upload_dir_path
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def validate_upload(filename: str, content: bytes) -> None:
    """Validate extension, size, and genuine-SQLite header (NFR-9).

    Raises UploadValidationError with a human-readable, non-technical
    message on any failure. Never trusts the extension alone.
    """
    if not filename:
        raise UploadValidationError("Uploaded file is missing a filename.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file type '{extension or 'unknown'}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    max_bytes = settings.database_upload_max_mb * 1024 * 1024
    if len(content) == 0:
        raise UploadValidationError("Uploaded file is empty.")
    if len(content) > max_bytes:
        raise UploadValidationError(
            f"File exceeds the {settings.database_upload_max_mb}MB upload limit."
        )

    if content[:16] != SQLITE_HEADER:
        raise UploadValidationError(
            "File does not look like a valid SQLite database."
        )


def _is_openable_sqlite(path: Path) -> bool:
    """Confirms the file genuinely opens as SQLite, beyond the header check."""
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
        finally:
            conn.close()
        return True
    except sqlite3.Error:
        return False


def _generate_stored_filename(extension: str) -> str:
    # Deliberately ignores the user-supplied filename entirely for the
    # on-disk name — the only path-traversal-safe approach (NFR-9).
    return f"{uuid.uuid4().hex}{extension}"


def _sanitize_display_name(filename: str) -> str:
    # Display-only: strip any path components from the original filename.
    return Path(filename).name


def register_database(session_id: str, filename: str, content: bytes) -> str:
    """Validate, store, and mark the upload as this session's active database.

    Returns the display name for the frontend. Never returns/exposes the
    on-disk path.
    """
    validate_upload(filename, content)

    upload_dir = _ensure_upload_dir()
    extension = Path(filename).suffix.lower()
    stored_name = _generate_stored_filename(extension)
    stored_path = upload_dir / stored_name

    stored_path.write_bytes(content)

    if not _is_openable_sqlite(stored_path):
        stored_path.unlink(missing_ok=True)
        raise UploadValidationError(
            "File could not be opened as a valid SQLite database."
        )

    # Replace (not accumulate) this session's previous upload, if any.
    _remove_previous_upload(session_id)

    display_name = _sanitize_display_name(filename)
    session_store.set_active_database(session_id, stored_path, display_name)
    return display_name


def _remove_previous_upload(session_id: str) -> None:
    record = session_store.get_active_database(session_id)
    if record and record.active_db_path and record.active_db_path.exists():
        try:
            record.active_db_path.unlink()
        except OSError:
            pass  # best-effort cleanup; never block the new upload on this


def get_active_database_path(session_id: str) -> Path:
    """Resolve the session's active database file: its upload, or the seeded
    demo database if none has been uploaded (or the prior upload's file is
    missing)."""
    record = session_store.get_active_database(session_id)
    if record and record.active_db_path and record.active_db_path.exists():
        return record.active_db_path
    return settings.default_database_path


def get_active_database_info(session_id: str) -> tuple[str, str]:
    """Returns (display_name, source) where source is 'default' or 'upload'."""
    record = session_store.get_active_database(session_id)
    if record and record.active_db_path and record.active_db_path.exists():
        return record.active_db_display_name or "uploaded database", "upload"
    return settings.default_database_path.name, "default"


def clear_active_database(session_id: str) -> None:
    """Revert the session to the default/demo database (PRD §11 fallback)."""
    _remove_previous_upload(session_id)
    session_store.clear_active_database(session_id)


def get_connection_path(session_id: str) -> Path:
    """The one entry point the Database Access Layer uses to resolve which
    file to connect to for a given session."""
    return get_active_database_path(session_id)


def get_active_database_identity(session_id: str) -> str:
    """A stable identifier for whichever database is active for this session.

    Used to key the schema cache (04_AGENT_TOOLS.md Tool 1 §7) so a
    mid-session database switch invalidates it. Internal use only — never
    returned to the frontend or the LLM, since it is a filesystem path.
    """
    return str(get_active_database_path(session_id).resolve())
