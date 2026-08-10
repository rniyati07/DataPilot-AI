"""Tool 2 — `execute_query` (04_AGENT_TOOLS.md).

The system's primary security boundary. Destructive SQL is stopped by the
validator in `db/sql_validator.py` *before* the statement reaches the
database — never by the LLM's system prompt alone (Architecture Rule 6).
"""
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.db import access_layer, sql_validator

logger = logging.getLogger(__name__)


class ExecuteQueryInput(BaseModel):
    """LLM-facing input. Deliberately excludes `session_id` — the session is
    resolved from the backend execution context, not from the model."""

    sql: str = Field(description="A single read-only SELECT or WITH statement to execute.")
    max_rows: Optional[int] = Field(
        default=None,
        description=(
            "Optional cap on returned rows. The server enforces its own ceiling; "
            "this can only lower the effective cap, never raise it."
        ),
    )

    @field_validator("max_rows")
    @classmethod
    def _validate_max_rows(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("max_rows must be a positive integer.")
        return value


def _error(error_type: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"type": error_type, "message": message}}


def _effective_limit(max_rows: Optional[int]) -> int:
    requested = max_rows if max_rows is not None else settings.default_max_rows
    return max(1, min(requested, settings.hard_row_ceiling))


def execute_query(
    session_id: str,
    sql: str,
    max_rows: Optional[int] = None,
) -> dict[str, Any]:
    """Core implementation. `session_id` is supplied by the backend, never
    by the LLM. Returns the structured contract from Tool 2 §6.
    """
    try:
        validated = sql_validator.validate(sql)
    except sql_validator.SqlValidationError as exc:
        # Rejected before the database is touched at all.
        logger.info("execute_query rejected a statement for session %s: %s", session_id, exc)
        return _error("validation_rejected", str(exc))

    limit = _effective_limit(max_rows)

    try:
        columns, rows, truncated = access_layer.execute_read_only(
            session_id, validated.sql, limit
        )
    except access_layer.QueryTimeoutError as exc:
        logger.warning("execute_query timed out for session %s", session_id)
        return _error("timeout", str(exc))
    except access_layer.DatabaseUnavailableError:
        logger.exception("execute_query: database unavailable for session %s", session_id)
        return _error("database_unavailable", "Could not connect to the active database.")
    except access_layer.QueryExecutionError as exc:
        # The driver's message is preserved (paths stripped) so the agent can
        # self-correct in Phase 12 — see Tool 2 §6.
        logger.info("execute_query: database error for session %s: %s", session_id, exc)
        return _error("sql_error", str(exc))
    except Exception:  # noqa: BLE001 - no exception may cross the tool boundary
        logger.exception("execute_query: unexpected failure for session %s", session_id)
        return _error("sql_error", "The query could not be executed.")

    return {
        "success": True,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
    }
