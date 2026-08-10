"""Tool 1 — `get_schema` (04_AGENT_TOOLS.md).

Dynamically discovers the currently active database's tables, columns,
types, primary keys, and foreign keys. This module contains no knowledge of
any particular schema: every table/column name it returns comes from the
SQLAlchemy Inspector at request time (Architecture Rule 5).
"""
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.db import access_layer, database_manager
from app.session import store as session_store

logger = logging.getLogger(__name__)


class GetSchemaInput(BaseModel):
    """LLM-facing input. Deliberately excludes `session_id` — the session is
    resolved from the backend execution context, not from the model."""

    table_filter: Optional[list[str]] = Field(
        default=None,
        description=(
            "Optional list of table names to restrict discovery to. "
            "Unknown names are ignored. Omit to discover the whole database."
        ),
    )
    refresh: bool = Field(
        default=False,
        description="Set true to bypass the cached schema and re-inspect the database.",
    )

    @field_validator("table_filter")
    @classmethod
    def _validate_table_filter(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        cleaned = [name.strip() for name in value if isinstance(name, str) and name.strip()]
        if not cleaned:
            raise ValueError("table_filter must be a non-empty list of non-empty table names.")
        return cleaned


def _error(error_type: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"type": error_type, "message": message}}


def _apply_filter(
    tables: list[dict[str, Any]], table_filter: Optional[list[str]]
) -> list[dict[str, Any]]:
    if not table_filter:
        return tables
    requested = {name.lower() for name in table_filter}
    return [table for table in tables if table["name"].lower() in requested]


def get_schema(
    session_id: str,
    table_filter: Optional[list[str]] = None,
    refresh: bool = False,
) -> dict[str, Any]:
    """Core implementation. `session_id` is supplied by the backend, never
    by the LLM. Returns the structured contract from Tool 1 §6.
    """
    try:
        db_identity = database_manager.get_active_database_identity(session_id)

        if not refresh:
            cached = session_store.get_cached_schema(session_id, db_identity)
            if cached is not None:
                tables = _apply_filter(cached, table_filter)
                return {
                    "success": True,
                    "tables": tables,
                    "table_count": len(tables),
                    "cached": True,
                }

        # Always discover and cache the *full* schema so a later filtered
        # call can still hit the cache (Tool 1 §8, step 6).
        full_schema = access_layer.discover_schema(session_id)
        session_store.set_cached_schema(session_id, db_identity, full_schema)

        tables = _apply_filter(full_schema, table_filter)
        return {
            "success": True,
            "tables": tables,
            "table_count": len(tables),
            "cached": False,
        }

    except access_layer.DatabaseUnavailableError:
        logger.exception("get_schema: database unavailable for session %s", session_id)
        return _error("database_unavailable", "Could not connect to the active database.")
    except access_layer.SchemaDiscoveryError:
        logger.exception("get_schema: discovery failed for session %s", session_id)
        return _error("schema_discovery_failed", "Could not read the database schema.")
    except Exception:  # noqa: BLE001 - no exception may cross the tool boundary
        logger.exception("get_schema: unexpected failure for session %s", session_id)
        return _error("schema_discovery_failed", "Could not read the database schema.")
