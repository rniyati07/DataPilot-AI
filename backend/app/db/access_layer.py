"""Database Access Layer — the only module that opens a SQLAlchemy
engine/Inspector against the active database (Architecture Rule 5/7/13).

Tools (`get_schema`, `execute_query`) depend on this layer and never open
their own connections. This layer resolves its target through the Database
Manager, so it is indifferent to whether the active database is the seeded
demo database or a session upload.
"""
import logging
import time
from typing import Any

from sqlalchemy import Engine, Inspector, inspect, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.config import settings
from app.db import database_manager, engine as engine_factory

logger = logging.getLogger(__name__)


class DatabaseUnavailableError(Exception):
    """The active database could not be reached/opened."""


class SchemaDiscoveryError(Exception):
    """The database opened but introspection failed."""


class QueryTimeoutError(Exception):
    """The statement exceeded the configured execution timeout."""


class QueryExecutionError(Exception):
    """The database rejected the statement (syntax, unknown column, ...).

    The message intentionally preserves the driver's text so the agent can
    self-correct (04_AGENT_TOOLS.md Tool 2 §6), sanitized of filesystem paths.
    """


def get_engine_for_session(session_id: str) -> Engine:
    db_path = database_manager.get_connection_path(session_id)
    return engine_factory.get_engine(db_path)


def get_readonly_engine_for_session(session_id: str) -> Engine:
    db_path = database_manager.get_connection_path(session_id)
    return engine_factory.get_readonly_engine(db_path)


def get_inspector_for_session(session_id: str) -> Inspector:
    return inspect(get_engine_for_session(session_id))


def list_tables_for_session(session_id: str) -> list[str]:
    return get_inspector_for_session(session_id).get_table_names()


def _sanitize_db_error(message: str) -> str:
    """Strips filesystem paths from a driver error before it leaves the
    backend, while preserving the diagnostic detail the agent needs."""
    upload_dir = str(settings.upload_dir_path)
    default_path = str(settings.default_database_path)
    cleaned = message.replace(upload_dir, "<database>").replace(default_path, "<database>")
    # Also drop SQLAlchemy's trailing connection-URL annotation if present.
    for marker in ("(Background on this error", "[SQL:"):
        index = cleaned.find(marker)
        if index != -1:
            cleaned = cleaned[:index]
    return cleaned.strip()


def discover_schema(session_id: str, table_filter: list[str] | None = None) -> list[dict[str, Any]]:
    """Inspector-driven schema discovery against the session's active
    database. Contains no knowledge of any particular schema.

    Raises DatabaseUnavailableError / SchemaDiscoveryError.
    """
    try:
        inspector = get_inspector_for_session(session_id)
        table_names = inspector.get_table_names()
    except OperationalError as exc:
        logger.exception("Active database unavailable for session %s", session_id)
        raise DatabaseUnavailableError(str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.exception("Schema discovery failed for session %s", session_id)
        raise SchemaDiscoveryError(str(exc)) from exc

    if table_filter:
        # Unknown names are silently omitted, never a fatal error (Tool 1 §9).
        requested = {name.lower() for name in table_filter}
        table_names = [name for name in table_names if name.lower() in requested]

    tables: list[dict[str, Any]] = []
    try:
        for table_name in table_names:
            pk_columns = set(inspector.get_pk_constraint(table_name).get("constrained_columns") or [])
            columns = [
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": bool(column.get("nullable", True)),
                    "primary_key": column["name"] in pk_columns,
                }
                for column in inspector.get_columns(table_name)
            ]

            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                referred_table = fk.get("referred_table")
                constrained = fk.get("constrained_columns") or []
                referred = fk.get("referred_columns") or []
                for index, column_name in enumerate(constrained):
                    foreign_keys.append(
                        {
                            "column": column_name,
                            "references_table": referred_table,
                            "references_column": referred[index] if index < len(referred) else None,
                        }
                    )

            tables.append({"name": table_name, "columns": columns, "foreign_keys": foreign_keys})
    except SQLAlchemyError as exc:
        logger.exception("Schema discovery failed for session %s", session_id)
        raise SchemaDiscoveryError(str(exc)) from exc

    return tables


def _json_safe(value: Any) -> Any:
    """Coerces driver values to JSON-serializable types (Tool 2 §6)."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def execute_read_only(
    session_id: str, sql: str, effective_limit: int
) -> tuple[list[str], list[list[Any]], bool]:
    """Executes an already-validated read-only statement against the
    session's active database.

    Returns (columns, rows, truncated). Callers must validate `sql` through
    `sql_validator` first — this function does not re-validate, but the
    connection itself is opened read-only as defense in depth.
    """
    try:
        engine = get_readonly_engine_for_session(session_id)
        connection = engine.connect()
    except (OperationalError, SQLAlchemyError) as exc:
        logger.exception("Could not connect for session %s", session_id)
        raise DatabaseUnavailableError(str(exc)) from exc

    deadline = time.monotonic() + settings.query_timeout_seconds
    timed_out = False

    def _progress_handler() -> int:
        # Returning non-zero aborts the running statement. This is SQLite's
        # supported interruption hook and works mid-query.
        nonlocal timed_out
        if time.monotonic() > deadline:
            timed_out = True
            return 1
        return 0

    raw_connection = connection.connection.driver_connection
    try:
        raw_connection.set_progress_handler(_progress_handler, 1000)
        try:
            result = connection.execute(text(sql))
            columns = list(result.keys())
            # Fetch one extra row so we can distinguish "exactly at the cap"
            # from "there is more data behind the cap".
            fetched = result.fetchmany(effective_limit + 1)
        finally:
            raw_connection.set_progress_handler(None, 1000)
    except OperationalError as exc:
        if timed_out:
            raise QueryTimeoutError(
                f"Query exceeded the {settings.query_timeout_seconds}s execution limit."
            ) from exc
        raise QueryExecutionError(_sanitize_db_error(str(exc.orig or exc))) from exc
    except SQLAlchemyError as exc:
        raise QueryExecutionError(_sanitize_db_error(str(getattr(exc, "orig", None) or exc))) from exc
    finally:
        connection.close()

    truncated = len(fetched) > effective_limit
    rows = [[_json_safe(value) for value in row] for row in fetched[:effective_limit]]
    return columns, rows, truncated
