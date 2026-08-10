"""Tool 5 — `explain_data` (04_AGENT_TOOLS.md).

Produces a plain-language explanation of a bounded query result, grounded
strictly in the data it is handed. This is the only one of the five tools
that makes an LLM call internally; it never touches the database.

Design (Tool 5 §8):
- Empty result → deterministic friendly message, no LLM call.
- More than `explain_summarize_after_rows` rows → compute lightweight
  aggregates in code and pass only those to the LLM.
- LLM failure → deterministic fallback assembled from the aggregates/top row,
  so the user still gets a useful answer.
"""
import logging
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.agent.llm_provider import get_chat_model
from app.config import settings
from app.tools.generate_chart import ChartData

logger = logging.getLogger(__name__)

TOP_N_ROWS = 3

EMPTY_RESULT_MESSAGE = (
    "I didn't find any matching data for that question — it's possible the "
    "filters were too narrow or there's nothing in that range yet."
)


class ChartHint(BaseModel):
    chart_type: Literal["bar", "line", "pie", "scatter", "none"]
    title: str


class ExplainDataInput(BaseModel):
    """LLM-facing input. `session_id` is resolved from the execution context,
    never from the model (pending correction 2)."""

    data: ChartData = Field(description="The bounded result set to explain, normally from execute_query.")
    question: str = Field(description="The user's original question, for framing the explanation.")
    chart: Optional[ChartHint] = Field(
        default=None,
        description="Lightweight chart context if a chart was generated this turn.",
    )
    correction_note: Optional[str] = Field(
        default=None,
        description="Brief note if a prior query attempt failed and was auto-corrected.",
    )

    @field_validator("question")
    @classmethod
    def _validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must be a non-empty string.")
        return value.strip()


# Injectable seam so tests can substitute a fake model without touching the
# agent's provider wiring.
_llm_factory = get_chat_model


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _aggregate(columns: List[str], rows: List[List[Any]]) -> dict[str, Any]:
    """Deterministic in-code aggregates over the bounded result set."""
    numeric: dict[str, dict[str, Any]] = {}
    for index, column in enumerate(columns):
        values = [row[index] for row in rows if index < len(row) and _is_number(row[index])]
        if values:
            numeric[column] = {
                "min": min(values),
                "max": max(values),
                "mean": round(sum(values) / len(values), 2),
            }
    return {"row_count": len(rows), "numeric": numeric}


def _top_rows(columns: List[str], rows: List[List[Any]]) -> List[List[Any]]:
    """Rows ordered by the first numeric column descending (deterministic)."""
    numeric_index = next(
        (index for index, column in enumerate(columns) if _is_number(rows[0][index])),
        0,
    )
    ordered = sorted(rows, key=lambda row: (row[numeric_index] if _is_number(row[numeric_index]) else 0), reverse=True)
    return ordered[:TOP_N_ROWS]


def _row_text(columns: List[str], row: List[Any]) -> str:
    return "; ".join(f"{column}: {value}" for column, value in zip(columns, row))


def _prompt(data_text: str, question: str, chart: Optional[ChartHint], correction_note: Optional[str]) -> str:
    parts = [
        "You are a careful data analyst. Explain the following query result to the user in clear, "
        "brief plain language (2-4 sentences).",
        f"User's question: {question}",
        f"Result:\n{data_text}",
    ]
    if chart is not None:
        parts.append(f"A chart was also generated: a {chart.chart_type} chart titled '{chart.title}'.")
    if correction_note:
        parts.append(f"Note: {correction_note}")
    parts.append(
        "State only what the data above supports. Do not invent values, entities, dates, or figures "
        "that are not present. If the data is inconclusive, say so."
    )
    return "\n".join(parts)


def _call_llm(prompt: str) -> str:
    from langchain_core.messages import HumanMessage

    model = _llm_factory()
    response = model.invoke([HumanMessage(content=prompt)])
    content = getattr(response, "content", "")
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return str(content).strip()


def _fallback_explanation(columns: List[str], rows: List[List[Any]], aggregates: dict[str, Any]) -> str:
    top = _top_rows(columns, rows)[0]
    return f"Here's the top result based on {aggregates['row_count']} rows: {_row_text(columns, top)}."


def explain_data(
    session_id: str,
    data: dict[str, Any],
    question: str,
    chart: Optional[dict[str, Any]] = None,
    correction_note: Optional[str] = None,
) -> dict[str, Any]:
    """Core implementation. `session_id` is accepted for signature parity with
    the other tools but is intentionally unused — the explanation only reasons
    over the `data` it is handed (Tool 5 §7, Rule 9).
    """
    data_dict = data.as_dict() if isinstance(data, ChartData) else data
    if isinstance(chart, dict) and chart:
        chart = ChartHint(**chart)
    columns = data_dict.get("columns") or []
    rows = data_dict.get("rows") or []

    if not columns:
        return {
            "success": False,
            "error": {"type": "generation_failed", "message": "The explanation service could not read the result set."},
        }
    if any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
        return {
            "success": False,
            "error": {"type": "generation_failed", "message": "The explanation service could not read the result set."},
        }

    if not rows:
        return {"success": True, "explanation": EMPTY_RESULT_MESSAGE}

    aggregates = _aggregate(columns, rows)
    if aggregates["row_count"] > settings.explain_summarize_after_rows:
        top = _top_rows(columns, rows)
        summary_lines = [f"Total rows: {aggregates['row_count']}"]
        for column, stats in aggregates["numeric"].items():
            summary_lines.append(
                f"{column}: min {stats['min']}, max {stats['max']}, mean {stats['mean']}"
            )
        summary_lines.append("Top rows:")
        summary_lines.extend(_row_text(columns, row) for row in top)
        data_text = "\n".join(summary_lines)
    else:
        # At most SUMMARIZE_THRESHOLD_ROWS rows reach this branch, so the
        # prompt stays bounded without truncating the user's actual result.
        data_text = "\n".join(_row_text(columns, row) for row in rows)

    prompt = _prompt(data_text, question, chart, correction_note)

    try:
        explanation = _call_llm(prompt)
        if explanation:
            return {"success": True, "explanation": explanation}
    except Exception:  # noqa: BLE001 - LLM failure falls back deterministically
        logger.exception("explain_data LLM call failed; using deterministic fallback")

    return {"success": True, "explanation": _fallback_explanation(columns, rows, aggregates)}
