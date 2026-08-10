"""Tool 4 — `generate_flowchart` (04_AGENT_TOOLS.md).

Deterministic Mermaid syntax generation. ER diagrams render the live schema
(forwarded in `context.schema` or discovered from the session's active
database); process diagrams render only the step graph the agent supplies —
the tool has no default process of its own; decision trees are the bonus.
The tool never calls the LLM internally.
"""
import logging
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db import access_layer
from app.diagrams import mermaid_builder

logger = logging.getLogger(__name__)


class FlowchartStep(BaseModel):
    id: str
    label: str = ""
    next: List[str] = Field(default_factory=list)


class FlowchartContext(BaseModel):
    """`schema` is the wire/LLM-facing key; the Python attribute is `schema_`
    because `schema` shadows BaseModel's deprecated classmethod (the contract
    in 04_AGENT_TOOLS.md Tool 4 §5 fixes the key name)."""

    model_config = ConfigDict(populate_by_name=True)
    schema_: Optional[List[dict[str, Any]]] = Field(default=None, alias="schema")
    description: Optional[str] = None
    steps: Optional[List[FlowchartStep]] = None
    entities: Optional[List[str]] = None


class GenerateFlowchartInput(BaseModel):
    """LLM-facing input. `session_id` is resolved from the execution context,
    never from the model (pending correction 2)."""

    diagram_type: Literal["er", "process", "decision"]
    context: FlowchartContext = Field(
        description=(
            "For 'er': schema (auto-discovered if omitted). For 'process': a "
            "non-empty steps list you derived, each step {id, label, next}. "
            "For 'decision': entities and/or a description."
        )
    )


def _generation_failed(message: str) -> dict[str, Any]:
    return {"success": False, "error": {"type": "generation_failed", "message": message}}


def _humanize_title(description: Optional[str]) -> str:
    if not description:
        return "Process Flow"
    return " ".join(word.capitalize() for word in description.split())


def _validate_steps(steps: Optional[List[dict[str, Any]]]) -> Optional[str]:
    """Returns an error message when the step graph is unusable, else None."""
    if not steps:
        return "process steps are required."
    ids = [step.get("id") for step in steps]
    if any(not step_id for step_id in ids):
        return "every step must have a non-empty id."
    if len(ids) != len(set(ids)):
        return "step ids must be unique."
    known = set(ids)
    for step in steps:
        for target in step.get("next") or []:
            if target not in known:
                return f"step '{step.get('id')}' references unknown step '{target}'."
    return None


def generate_flowchart(
    session_id: str,
    diagram_type: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Core implementation. `session_id` resolves the active database only for
    the ER fallback (schema omitted from `context`); everything else is
    derived deterministically from the supplied context."""
    context_dict = (
        context.model_dump(by_alias=True) if isinstance(context, FlowchartContext) else context
    )

    try:
        if diagram_type == "er":
            schema = context_dict.get("schema")
            if not schema:
                schema = access_layer.discover_schema(session_id)
            syntax = mermaid_builder.build_er_diagram(schema)
            title = "Database Entity-Relationship Diagram"
        elif diagram_type == "process":
            steps = context_dict.get("steps")
            steps_dicts = (
                [step.model_dump() for step in steps] if steps and isinstance(steps[0], FlowchartStep) else steps
            )
            error = _validate_steps(steps_dicts)
            if error:
                return _generation_failed(error)
            syntax = mermaid_builder.build_process_diagram(steps_dicts)
            title = _humanize_title(context_dict.get("description"))
        elif diagram_type == "decision":
            entities = context_dict.get("entities") or []
            description = context_dict.get("description")
            if not entities and not description:
                return _generation_failed("Insufficient context for a decision diagram.")
            syntax = mermaid_builder.build_decision_diagram(entities, description or "Decision")
            title = " ".join(description.split()).title() if description else "Decision Tree"
        else:  # unreachable: diagram_type is a Literal
            return _generation_failed("Unsupported diagram type.")
    except access_layer.DatabaseUnavailableError as exc:
        return {"success": False, "error": {"type": "schema_unavailable", "message": str(exc)}}
    except Exception:  # noqa: BLE001 - no exception may cross the tool boundary
        logger.exception("generate_flowchart: unexpected failure")
        return _generation_failed("The diagram could not be generated.")

    if not mermaid_builder.validate_mermaid(syntax):
        return _generation_failed("The diagram could not be assembled into valid Mermaid syntax.")

    return {
        "success": True,
        "diagram_type": diagram_type,
        "title": title,
        "mermaid_syntax": syntax,
    }
