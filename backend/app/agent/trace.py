"""Per-invocation tool trace.

The API layer needs the SQL the agent ran and the rows it got back in order
to fill the response envelope (`sql`, `columns`, `rows`). Rather than
re-parsing serialized ToolMessage content — whose exact string form is a
LangChain implementation detail — the registry's tool wrappers record what
they actually returned here.

Scoped with a ContextVar so concurrent requests never share a trace.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator, Optional

_current_trace: ContextVar[Optional[list[dict[str, Any]]]] = ContextVar(
    "current_tool_trace", default=None
)


@contextmanager
def trace_scope() -> Iterator[list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    token = _current_trace.set(records)
    try:
        yield records
    finally:
        _current_trace.reset(token)


def record(tool_name: str, args: dict[str, Any], result: dict[str, Any]) -> None:
    records = _current_trace.get()
    if records is not None:
        records.append({"tool": tool_name, "args": args, "result": result})


def last_successful_query(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The most recent successful `execute_query` call, if any."""
    for entry in reversed(records):
        if entry["tool"] == "execute_query" and entry["result"].get("success"):
            return entry
    return None


def last_query_error(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The most recent failed `execute_query` call, if any."""
    for entry in reversed(records):
        if entry["tool"] == "execute_query" and not entry["result"].get("success"):
            return entry
    return None


def last_chart(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The most recent successful `generate_chart` result that produced a
    real chart (not `chart_type: "none"`), if any."""
    for entry in reversed(records):
        if entry["tool"] != "generate_chart" or not entry["result"].get("success"):
            continue
        if entry["result"].get("chart_type") == "none":
            continue
        return entry["result"]
    return None


def last_diagram(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The most recent successful `generate_flowchart` result, if any."""
    for entry in reversed(records):
        if entry["tool"] == "generate_flowchart" and entry["result"].get("success"):
            return entry["result"]
    return None


def last_explanation(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The most recent successful `explain_data` result, if any."""
    for entry in reversed(records):
        if entry["tool"] == "explain_data" and entry["result"].get("success"):
            return entry["result"]
    return None


def last_explanation_entry(records: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The full trace entry (args + result) for the most recent successful
    `explain_data` call, if any. Unlike `last_explanation`, this exposes the
    `data` the tool was actually given, so a caller can verify which query
    result the explanation is grounded in (Phase 11 consistency check)."""
    for entry in reversed(records):
        if entry["tool"] == "explain_data" and entry["result"].get("success"):
            return entry
    return None


def successful_query_count(records: list[dict[str, Any]]) -> int:
    """How many `execute_query` calls in this turn succeeded."""
    return sum(
        1
        for entry in records
        if entry["tool"] == "execute_query" and entry["result"].get("success")
    )
