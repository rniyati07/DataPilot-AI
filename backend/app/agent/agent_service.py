"""Agent Service (Architecture §9, Implementation Plan Phase 6).

A LangChain **tool-calling** agent over the project's own five-tool
architecture — explicitly not `create_sql_agent` or any generic black-box
SQL toolkit (TRD §4). At this phase it is given exactly two tools:
`get_schema` and `execute_query`.

Charts, explanations, and diagrams belong to Phases 8-10 and are not
requested from the agent here.
"""
import logging
from typing import Any

from app.agent import error_recovery, trace
from app.agent.llm_provider import LlmConfigurationError, get_chat_model
from app.agent.tool_registry import build_tools
from app.models.schemas import ChatResponse, ErrorDetail
from app.session import store as session_store
from app.session.context import session_scope

logger = logging.getLogger(__name__)

# Bounds tool-calling loops in code, not by prompt instruction alone. The
# single-retry self-correction loop is Phase 12 — this is only a safety stop.
MAX_AGENT_STEPS = 12

# Rows of the prior result set re-presented to the model on follow-up turns,
# so "these products" resolves without re-querying while prompts stay bounded.
PRIOR_RESULT_MAX_ROWS = 10

SYSTEM_PROMPT = """You are DataPilot AI, a careful database analyst.

You answer questions about the user's currently active SQL database.

Rules:
- Call `get_schema` before writing SQL, so you use real table and column
  names. Never invent or guess a table or column name.
- Use `execute_query` for every database read. It accepts a single
  read-only SELECT or WITH statement.
- The system is read-only. If the user asks you to insert, update, delete,
  or otherwise modify data, explain that you can only read data — do not
  attempt it.
- Base your answer only on rows actually returned by `execute_query`.
  Never invent, estimate, or extrapolate data that was not returned.
- If a query returns no rows, say so plainly rather than inventing results.
- If execute_query fails with a database error (its result has error.type
  'sql_error'), fix the SQL (re-check get_schema if needed) and retry exactly
  once. If it succeeds after that, briefly tell the user you corrected the
  query. If it fails again (error.type 'retry_limit_reached'), stop and explain
  the limitation in plain language.
- Keep tool usage focused: do not re-run a query whose result you already have.
- After a data query, if the result is a comparison, trend, or share the user
  asked to see, call `generate_chart` with the result's columns/rows. If the
  tool returns chart_type 'none', present the table and skip the chart.
- End a data turn with `explain_data` (pass the result's columns/rows and the
  user's question) so the user gets a plain-language read on the result. Do
  not call it for scalar facts the reply already covers.
- For structure questions use `generate_flowchart`: diagram_type 'er' for the
  database schema; diagram_type 'process' only after you derive the step
  sequence yourself and supply context.steps. Never call it for plain data
  questions.
- Answer in clear, brief prose. Do not paste the full result table into your
  reply — the interface displays it separately. Summarize the finding instead.
"""


def _build_agent(model: Any = None) -> Any:
    """Constructs the tool-calling agent. `model` is injectable so tests can
    supply a fake chat model instead of calling a real provider."""
    from langchain.agents import create_agent

    chat_model = model if model is not None else get_chat_model()
    return create_agent(
        model=chat_model,
        tools=build_tools(),
        system_prompt=SYSTEM_PROMPT,
    )


def _final_message_text(result: Any) -> str:
    """Extracts the agent's closing natural-language answer."""
    messages = result.get("messages") if isinstance(result, dict) else None
    if not messages:
        return ""
    content = getattr(messages[-1], "content", "")
    if isinstance(content, str):
        return content.strip()
    # Some providers return content as a list of typed blocks.
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(parts).strip()
    return str(content).strip()


def _error_response(error_type: str, message: str) -> ChatResponse:
    return ChatResponse(
        message=message,
        error=ErrorDetail(type=error_type, message=message),
    )


def run_agent(session_id: str, message: str, model: Any = None) -> ChatResponse:
    """Runs one agent turn for `session_id` and composes the response
    envelope established in Batch 1 (Architecture §5/§8).

    Never raises: every failure path becomes a structured envelope.
    """
    try:
        agent = _build_agent(model=model)
    except LlmConfigurationError as exc:
        logger.warning("Agent unavailable: %s", exc)
        return _error_response("llm_unavailable", str(exc))
    except Exception:  # noqa: BLE001
        logger.exception("Could not construct the agent")
        return _error_response(
            "agent_error", "The AI analyst could not be started. Please try again."
        )

    # The session travels through the execution context so the tools resolve
    # the right active database without `session_id` being LLM-facing.
    try:
        memory = session_store.get_memory(session_id)
        # Recent turns plus, when present, the previous result set — so
        # follow-ups ("now show their trend") resolve against prior context.
        history = _conversation_messages(session_id, memory)
        with (
            session_scope(session_id),
            trace.trace_scope() as records,
            error_recovery.retry_budget_scope(),
        ):
            result = agent.invoke(
                {"messages": history + [{"role": "user", "content": message}]},
                config={"recursion_limit": MAX_AGENT_STEPS},
            )
            response = _compose_response(result, records)
            memory.add_user(message)
            reply = _final_message_text(result)
            if reply:
                memory.add_assistant(reply)
            last_query = trace.last_successful_query(records)
            session_store.set_last_results(
                session_id, last_query["result"] if last_query else None
            )
            return response
    except Exception:  # noqa: BLE001 - never leak provider/agent internals
        logger.exception("Agent invocation failed for session %s", session_id)
        return _error_response(
            "agent_error",
            "The AI analyst could not complete that request. Please try rephrasing it.",
        )


def _conversation_messages(session_id: str, memory: Any) -> list[dict[str, str]]:
    """Prior text turns, plus the previous result set rendered compactly so
    entity references resolve without forcing a re-query (Architecture §7)."""
    messages = memory.to_messages()
    prior = session_store.get_last_results(session_id)
    if prior and prior.get("rows"):
        lines = ["[Result set from your previous question]"]
        columns = prior.get("columns") or []
        if columns:
            lines.append(", ".join(str(column) for column in columns))
        for row in (prior.get("rows") or [])[:PRIOR_RESULT_MAX_ROWS]:
            lines.append(", ".join(str(value) for value in row))
        messages = messages + [{"role": "user", "content": "\n".join(lines)}]
    return messages


def _compose_response(result: Any, records: list[dict[str, Any]]) -> ChatResponse:
    """Maps the agent run onto the response envelope.

    Charts/diagrams/explanations are taken from the trace regardless of which
    branch the message lands in, so a pure diagram turn ("draw the ER diagram",
    with no execute_query) still returns its Mermaid syntax.
    """
    text = _final_message_text(result)
    chart = trace.last_chart(records)
    diagram = trace.last_diagram(records)
    explanation = trace.last_explanation(records)
    diagram_text = diagram["mermaid_syntax"] if diagram else None
    explanation_text = explanation["explanation"] if explanation else None

    successful = trace.last_successful_query(records)
    if successful:
        payload = successful["result"]
        note = ""
        if payload.get("truncated"):
            note = " (results were truncated to the first {} rows)".format(payload["row_count"])
        return ChatResponse(
            message=(text or "Here are the results.") + note,
            sql=successful["args"].get("sql"),
            columns=payload.get("columns", []),
            rows=payload.get("rows", []),
            chart=chart,
            diagram=diagram_text,
            explanation=explanation_text,
        )

    # No successful query — surface a failed one gracefully, if there was one.
    failed = trace.last_query_error(records)
    if failed:
        error = failed["result"].get("error", {})
        error_type = error.get("type", "sql_error")
        user_message = text or _friendly_query_error(error_type)
        return ChatResponse(
            message=user_message,
            sql=failed["args"].get("sql"),
            chart=chart,
            diagram=diagram_text,
            explanation=explanation_text,
            error=ErrorDetail(type=error_type, message=user_message),
        )

    # A schema-only or conversational turn (e.g. "what tables exist?").
    if not text:
        return _error_response(
            "agent_error", "The AI analyst did not return an answer. Please try again."
        )
    return ChatResponse(message=text, chart=chart, diagram=diagram_text, explanation=explanation_text)


def _friendly_query_error(error_type: str) -> str:
    return {
        "validation_rejected": (
            "That request would require modifying the database, but DataPilot AI "
            "is read-only."
        ),
        "timeout": "That query took too long to run. Try narrowing it down.",
        "database_unavailable": "The database could not be reached. Please try again.",
        "retry_limit_reached": (
            "I tried that query once more after an automatic correction, but it "
            "still could not be completed against the current database."
        ),
    }.get(error_type, "That query could not be completed against the current database.")


def get_registered_tool_names() -> list[str]:
    """Exposed for tests/diagnostics — which tools this phase registers."""
    from app.agent.tool_registry import registered_tool_names

    return registered_tool_names()
