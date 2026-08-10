"""Deterministic Mermaid diagram builder (Implementation Plan Phase 10,
04_AGENT_TOOLS.md Tool 4 §8, Architecture Rule 10).

A pure formatting module: no database access and no LLM calls. ER diagrams
are template-driven from a `get_schema`-shaped schema; process diagrams are
driven entirely by an agent-supplied step graph. No table, relationship, or
process name is hardcoded for any dataset — including the seeded e-commerce
one — so the output always matches the database actually active.
"""
import re
from typing import Any, Optional

_ER_KEYWORDS = ("erDiagram",)
_FLOW_KEYWORDS = ("flowchart", "graph")


def _clean_id(value: str) -> str:
    """Turns an arbitrary name into a Mermaid-safe node/entity id."""
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(value))
    if not cleaned:
        cleaned = "node"
    if cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned


def _clean_label(value: Any) -> str:
    """Strips characters that would break Mermaid's node/edge syntax."""
    text = str(value).strip()
    for char in ('"', "[", "]", "{", "}", "|", "`", "\n", "\r"):
        text = text.replace(char, " ")
    text = re.sub(r"\s+", " ", text)
    return text[:200]


def _mermaid_type(sql_type: Any) -> str:
    t = str(sql_type).upper()
    if "INT" in t:
        return "int"
    if "BOOL" in t:
        return "bool"
    if "CHAR" in t or "TEXT" in t or "CLOB" in t or "STRING" in t:
        return "string"
    if "REAL" in t or "FLOA" in t or "DOUB" in t or "DEC" in t or "NUM" in t:
        return "float"
    if "BLOB" in t:
        return "blob"
    if "DATE" in t:
        return "date"
    return "string"


def _er_label(label: str) -> str:
    label = _clean_label(label)
    return f'"{label}"' if " " in label else (label or "references")


def build_er_diagram(schema: list[dict[str, Any]]) -> str:
    """Renders a live schema into Mermaid `erDiagram` syntax. The schema is
    expected in `get_schema`'s output shape: list of {name, columns, foreign_keys}.
    Relationship labels are derived from the foreign-key column names — never
    hardcoded per-dataset semantics.
    """
    lines = ["erDiagram"]
    for table in schema:
        entity = _clean_id(table["name"]).upper()
        fk_columns = {fk["column"] for fk in table.get("foreign_keys", [])}
        lines.append(f"    {entity} {{")
        for column in table.get("columns", []):
            column_name = _clean_id(column["name"])
            if column.get("primary_key"):
                key = " PK"
            elif column_name in fk_columns:
                key = " FK"
            else:
                key = ""
            lines.append(f"        {_mermaid_type(column.get('type'))} {column_name}{key}")
        lines.append("    }")
    for table in schema:
        entity = _clean_id(table["name"]).upper()
        for fk in table.get("foreign_keys", []):
            referenced = fk.get("references_table") or table["name"]
            parent = _clean_id(referenced).upper()
            lines.append(f"    {parent} ||--o{{ {entity} : {_er_label(fk['column'])}")
    return "\n".join(lines)


def build_process_diagram(steps: list[dict[str, Any]]) -> str:
    """Renders an agent-supplied step graph as a Mermaid `flowchart TD`.
    Every node carries its label; edges come only from each step's `next`.
    """
    lines = ["flowchart TD"]
    for step in steps:
        node = _clean_id(step["id"])
        label = _clean_label(step.get("label")) or node
        lines.append(f'    {node}["{label}"]')
    for step in steps:
        node = _clean_id(step["id"])
        for target in step.get("next") or []:
            lines.append(f"    {node} --> {_clean_id(target)}")
    return "\n".join(lines)


def build_decision_diagram(entities: list[str], description: str) -> str:
    """Bonus: renders a small decision flowchart from the supplied entities
    and description. Deterministic; never half-built."""
    title = _clean_label(description) or "Decision"
    lines = ["flowchart TD", f'    start["{title}"] --> decision{{"{title}?"}}']
    for index, entity in enumerate(entities):
        label = _clean_label(entity) or f"Option {index + 1}"
        lines.append(f'    decision -->|"{label}"| branch_{index}["{label}"]')
    return "\n".join(lines)


def _strip_quoted(text: str) -> str:
    return re.sub(r'"[^"]*"', "", text)


def _is_balanced(text: str, opening: str, closing: str) -> bool:
    depth = 0
    for char in text:
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
        if depth < 0:
            return False
    return depth == 0


def validate_mermaid(syntax: str) -> bool:
    """Structural pre-return validation: recognized top-level keyword and,
    for flowcharts, balanced brackets (04_AGENT_TOOLS.md Tool 4 §9)."""
    lines = [line.strip() for line in syntax.strip().splitlines() if line.strip()]
    if not lines:
        return False
    first = lines[0]
    if any(first.startswith(keyword) for keyword in _ER_KEYWORDS):
        return first == "erDiagram"
    if any(first.startswith(keyword) for keyword in _FLOW_KEYWORDS):
        stripped = _strip_quoted(syntax)
        return (
            _is_balanced(stripped, "[", "]")
            and _is_balanced(stripped, "{", "}")
            and _is_balanced(stripped, "(", ")")
        )
    return False
