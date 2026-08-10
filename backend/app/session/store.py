"""In-memory session store (Architecture §7).

Current scope: the session's active-database reference plus the Phase 4
schema cache hook. Conversation memory / recent result sets are added in
Phase 7 — do not add them here.
"""
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

FALLBACK_SESSION_ID = "anonymous"


@dataclass
class SessionRecord:
    active_db_path: Optional[Path] = None
    active_db_display_name: Optional[str] = None
    # Phase 4 schema cache. `schema_cache_db_identity` records which database
    # the cached schema was read from, so a mid-session upload/switch can
    # never be served the previous database's schema (04_AGENT_TOOLS.md §7).
    schema_cache: Optional[dict[str, Any]] = None
    schema_cache_db_identity: Optional[str] = None


_sessions: dict[str, SessionRecord] = {}
_lock = threading.Lock()


def _get_or_create(session_id: str) -> SessionRecord:
    with _lock:
        record = _sessions.get(session_id)
        if record is None:
            record = SessionRecord()
            _sessions[session_id] = record
        return record


def set_active_database(session_id: str, path: Path, display_name: str) -> None:
    record = _get_or_create(session_id)
    record.active_db_path = path
    record.active_db_display_name = display_name


def get_active_database(session_id: str) -> Optional[SessionRecord]:
    record = _sessions.get(session_id)
    if record is None or record.active_db_path is None:
        return None
    return record


def clear_active_database(session_id: str) -> None:
    record = _sessions.get(session_id)
    if record is not None:
        record.active_db_path = None
        record.active_db_display_name = None
        record.schema_cache = None
        record.schema_cache_db_identity = None


def get_cached_schema(session_id: str, db_identity: str) -> Optional[dict[str, Any]]:
    """Returns the cached schema only if it was read from the database that
    is *currently* active for this session; otherwise None."""
    record = _sessions.get(session_id)
    if record is None or record.schema_cache is None:
        return None
    if record.schema_cache_db_identity != db_identity:
        return None
    return record.schema_cache


def set_cached_schema(session_id: str, db_identity: str, schema: dict[str, Any]) -> None:
    record = _get_or_create(session_id)
    record.schema_cache = schema
    record.schema_cache_db_identity = db_identity


def resolve_session_id(header_value: Optional[str]) -> str:
    """Sessions are identified by a UUID the frontend issues on first load
    (TRD §3). A missing header falls back to a fixed id so the API remains
    directly testable (curl, pytest) without a frontend in the loop.
    """
    if header_value and header_value.strip():
        return header_value.strip()
    return FALLBACK_SESSION_ID
