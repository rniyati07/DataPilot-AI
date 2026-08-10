"""In-memory session store (Architecture §7).

Per session it holds: the active-database reference, the Phase 4 schema
cache hook, the Phase 7 bounded conversation memory, and the most recent
result set. Memory is process-local and ephemeral by design — the deployment
target is a single local/demo instance (Architecture §7).
"""
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.agent.memory import ConversationMemory

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
    # Phase 7 conversation memory + most recent result set (Architecture §7).
    memory: Optional[ConversationMemory] = None
    last_results: Optional[dict[str, Any]] = None


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
    # A different active database invalidates prior conversation context:
    # entity references from before the switch no longer apply.
    record.memory = None
    record.last_results = None


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
        record.memory = None
        record.last_results = None


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


def get_memory(session_id: str) -> ConversationMemory:
    """Returns the session's bounded conversation memory, creating it on
    first use (Phase 7, FR-8)."""
    record = _get_or_create(session_id)
    if record.memory is None:
        record.memory = ConversationMemory()
    return record.memory


def get_last_results(session_id: str) -> Optional[dict[str, Any]]:
    """The most recent `execute_query` payload for the session, if any
    (Architecture §7) — lets follow-ups reference prior result sets."""
    record = _sessions.get(session_id)
    return record.last_results if record is not None else None


def set_last_results(session_id: str, payload: Optional[dict[str, Any]]) -> None:
    record = _get_or_create(session_id)
    record.last_results = payload
