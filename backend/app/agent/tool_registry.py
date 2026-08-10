"""Tool Registry (Architecture §9).

The single place all agent tools are constructed and registered. Adding a
later tool means adding one entry here — not touching routing or the agent
executor.

All five mandatory tools are now registered: `get_schema` (Phase 4),
`execute_query` (Phase 5), `generate_chart` (Phase 8), `explain_data`
(Phase 9), and `generate_flowchart` (Phase 10).

Each LangChain tool is a thin wrapper that injects the current session from
the backend execution context, so `session_id` never appears in the
LLM-facing argument schema (docs review — pending correction 2).
"""
from typing import Any, Optional

from langchain_core.tools import StructuredTool

from app.agent import error_recovery, trace
from app.session.context import get_current_session_id
from app.tools.execute_query import ExecuteQueryInput, execute_query
from app.tools.explain_data import ExplainDataInput, explain_data
from app.tools.generate_chart import GenerateChartInput, generate_chart
from app.tools.generate_flowchart import GenerateFlowchartInput, generate_flowchart
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

GENERATE_CHART_DESCRIPTION = (
    "Turn a bounded tabular result into a ready-to-render Plotly chart. Pass the "
    "columns/rows straight through from execute_query. Returns a chart spec and "
    "chart_type (bar, line, pie, scatter, or none) — 'none' means a chart would not "
    "add clarity, so show the table and explain_data instead."
)

EXPLAIN_DATA_DESCRIPTION = (
    "Produce a natural-language explanation of a bounded query result, grounded "
    "only in the data passed in. Call this as the final step of a data turn, "
    "passing the same columns/rows the user's result returned, plus the user's "
    "question. Never call it for diagram requests."
)

GENERATE_FLOWCHART_DESCRIPTION = (
    "Generate Mermaid syntax for a structure/process question. For an entity-"
    "relationship diagram pass diagram_type='er' (the active database's schema "
    "is auto-discovered). For a process flow, first reason out the step sequence "
    "yourself and pass diagram_type='process' with context.steps as a list of "
    "{id, label, next: [...]} — the tool has no default process. Never call it "
    "for plain data questions."
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
    # Phase 12 (Architecture §6): cap automatic corrections at exactly one, in
    # code. The agent sees the failed result (its raw sql_error message) and
    # self-corrects; only database-level errors are retryable — write rejections
    # and connection failures never consume budget or allow another attempt.
    error_type = result.get("error", {}).get("type") if not result.get("success") else None
    if error_type in error_recovery.RETRYABLE_ERROR_TYPES:
        budget = error_recovery.current_budget()
        if budget is not None and budget.use():
            result = {
                **result,
                "error": {
                    "type": "retry_limit_reached",
                    "message": (
                        "The query failed again after one automatic correction. "
                        "Stop retrying and explain the limitation to the user in plain language."
                    ),
                },
            }
    trace.record("execute_query", {"sql": sql, "max_rows": max_rows}, result)
    return result


def _generate_chart_tool(
    data: dict[str, Any],
    intent: Optional[str] = None,
    x_field: Optional[str] = None,
    y_field: Optional[str] = None,
) -> dict[str, Any]:
    result = generate_chart(
        session_id=get_current_session_id(),
        data=data,
        intent=intent,
        x_field=x_field,
        y_field=y_field,
    )
    trace.record(
        "generate_chart",
        {"intent": intent, "x_field": x_field, "y_field": y_field},
        result,
    )
    return result


def _explain_data_tool(
    data: dict[str, Any],
    question: str,
    chart: Optional[dict[str, Any]] = None,
    correction_note: Optional[str] = None,
) -> dict[str, Any]:
    result = explain_data(
        session_id=get_current_session_id(),
        data=data,
        question=question,
        chart=chart,
        correction_note=correction_note,
    )
    trace.record(
        "explain_data",
        {"question": question, "chart": chart, "correction_note": correction_note},
        result,
    )
    return result


def _generate_flowchart_tool(
    diagram_type: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    result = generate_flowchart(
        session_id=get_current_session_id(),
        diagram_type=diagram_type,
        context=context,
    )
    trace.record("generate_flowchart", {"diagram_type": diagram_type}, result)
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
        StructuredTool.from_function(
            func=_generate_chart_tool,
            name="generate_chart",
            description=GENERATE_CHART_DESCRIPTION,
            args_schema=GenerateChartInput,
        ),
        StructuredTool.from_function(
            func=_explain_data_tool,
            name="explain_data",
            description=EXPLAIN_DATA_DESCRIPTION,
            args_schema=ExplainDataInput,
        ),
        StructuredTool.from_function(
            func=_generate_flowchart_tool,
            name="generate_flowchart",
            description=GENERATE_FLOWCHART_DESCRIPTION,
            args_schema=GenerateFlowchartInput,
        ),
    ]


def registered_tool_names() -> list[str]:
    return [tool.name for tool in build_tools()]
