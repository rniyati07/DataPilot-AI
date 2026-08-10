"""Database Access Layer — the only module that opens a SQLAlchemy
engine/Inspector against the active database (Architecture Rule 5/7/13).

Batch 1 only needs enough of this layer to prove the active-database
concept works (used by a throwaway verification and by tests). The full
`execute_query`/`get_schema` tools land in Phases 4-5.
"""
from sqlalchemy import Engine, Inspector, inspect

from app.db import database_manager, engine as engine_factory


def get_engine_for_session(session_id: str) -> Engine:
    db_path = database_manager.get_connection_path(session_id)
    return engine_factory.get_engine(db_path)


def get_inspector_for_session(session_id: str) -> Inspector:
    return inspect(get_engine_for_session(session_id))


def list_tables_for_session(session_id: str) -> list[str]:
    return get_inspector_for_session(session_id).get_table_names()
