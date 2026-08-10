"""Session execution context (docs review — pending correction 2).

The agent's tools must operate against the *current session's* active
database, but `session_id` must never appear as an LLM-facing tool argument
(otherwise the model could invent or swap one). A ContextVar carries the
session through the backend execution context instead: the API layer sets
it per request, and the tool wrappers read it when resolving the database.

This is not a second session system — it is a pointer into the existing
Session Store / Database Manager.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from app.session.store import FALLBACK_SESSION_ID

_current_session_id: ContextVar[str] = ContextVar(
    "current_session_id", default=FALLBACK_SESSION_ID
)


def get_current_session_id() -> str:
    return _current_session_id.get()


@contextmanager
def session_scope(session_id: str) -> Iterator[str]:
    token = _current_session_id.set(session_id)
    try:
        yield session_id
    finally:
        _current_session_id.reset(token)
