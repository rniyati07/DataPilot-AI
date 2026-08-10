"""Tool 3 — `generate_chart` (04_AGENT_TOOLS.md).

A thin wrapper around the deterministic Plotly builder. The tool never
touches the database or the LLM: it only shapes the `data` it is handed into
a ready-to-render spec (Architecture Rule 9).
"""
import logging
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.viz import plotly_builder

logger = logging.getLogger(__name__)


class ChartData(BaseModel):
    columns: List[str]
    rows: List[List[Any]]

    def as_dict(self) -> dict[str, Any]:
        return {"columns": self.columns, "rows": self.rows}


class GenerateChartInput(BaseModel):
    """LLM-facing input. `session_id` is resolved from the execution context,
    never from the model (pending correction 2)."""

    data: ChartData = Field(description="The result set to visualize, normally passed through from execute_query.")
    intent: Optional[str] = Field(
        default=None,
        description=(
            "Optional free-text hint about what the user wants to see "
            "(e.g., 'trend over time', 'compare products', 'share of total'). "
            "Used only to disambiguate otherwise-tied rules, never to override "
            "a clear shape-based rule."
        ),
    )
    x_field: Optional[str] = Field(
        default=None,
        description="Optional hint for which column maps to the x axis. Ignored if it does not match a column.",
    )
    y_field: Optional[str] = Field(
        default=None,
        description="Optional hint for which column maps to the y axis. Ignored if it does not match a column.",
    )

    @field_validator("intent")
    @classmethod
    def _validate_intent(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("intent must be a non-empty string when provided.")
        return value


def generate_chart(
    session_id: str,
    data: dict[str, Any],
    intent: Optional[str] = None,
    x_field: Optional[str] = None,
    y_field: Optional[str] = None,
) -> dict[str, Any]:
    """Core implementation. `session_id` is accepted for signature parity with
    the other tools but is intentionally unused — chart building has no
    database dependency (Tool 3 §7, Rule 9).
    """
    try:
        # `data` is a plain dict when called directly, but the LangChain layer
        # may have validated it into a ChartData model first.
        data_dict = data.as_dict() if isinstance(data, ChartData) else data
        return plotly_builder.build_chart_spec(data_dict, intent, x_field, y_field)
    except Exception:  # noqa: BLE001 - no exception may cross the tool boundary
        logger.exception("generate_chart: unexpected failure")
        return {
            "success": False,
            "error": {"type": "unsupported", "message": "The chart could not be generated."},
        }
