"""Tool Registry (Architecture §9).

The single place all agent tools are constructed and registered. Adding a
later tool means adding one entry here — not touching routing or the agent
executor.

Phase 6 registers exactly two tools: `get_schema` and `execute_query`.
`generate_chart`, `explain_data`, and `generate_flowchart` belong to
Phases 8-10 and must NOT be registered yet.

Each LangChain tool is a thin wrapper that injects the current session from
the backend execution context, so `session_id` never appears in the
LLM-facing argument schema (docs review — pending correction 2).
"""
from typing import Any, Optional

from langchain_core.tools import StructuredTool

from app.agent import trace
from app.session.context import get_current_session_id
from app.tools.execute_query import ExecuteQueryInput, execute_query
from app.tools.get_schema import GetSchemaInput, get_schema

GET_SCHEMA_DESCRIPTION = (
    "Discover the active database's tables, columns, data types, primary keys, "
    "and foreign-key relationships. Call this before writing SQL so you use real "
    "table and column names. Returns structured JSON."
)

EXECUTE_QUERY_DESCRIPTION = (
    "Execute a single read-only SQL SELECT (or WITH) statement against the active "
    "database and return the rows. Write operations are rejected. Returns structured "
    "JSON with columns, rows, row_count, and truncated."
)


def _get_schema_tool(
    table_filter: Optional[list[str]] = None, refresh: bool = False
) -> dict[str, Any]:
    result = get_schema(
        session_id=get_current_session_id(),
        table_filter=table_filter,
        refresh=refresh,
    )
    trace.record("get_schema", {"table_filter": table_filter, "refresh": refresh}, result)
    return result


def _execute_query_tool(sql: str, max_rows: Optional[int] = None) -> dict[str, Any]:
    result = execute_query(
        session_id=get_current_session_id(),
        sql=sql,
        max_rows=max_rows,
    )
    trace.record("execute_query", {"sql": sql, "max_rows": max_rows}, result)
    return result


def build_tools() -> list[StructuredTool]:
    """Constructs the tools registered for the current phase."""
    return [
        StructuredTool.from_function(
            func=_get_schema_tool,
            name="get_schema",
            description=GET_SCHEMA_DESCRIPTION,
            args_schema=GetSchemaInput,
        ),
        StructuredTool.from_function(
            func=_execute_query_tool,
            name="execute_query",
            description=EXECUTE_QUERY_DESCRIPTION,
            args_schema=ExecuteQueryInput,
        ),
    ]


def registered_tool_names() -> list[str]:
    return [tool.name for tool in build_tools()]
