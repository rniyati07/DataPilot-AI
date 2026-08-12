"""Deterministic Plotly spec builder (Implementation Plan Phase 8,
04_AGENT_TOOLS.md Tool 3 §8, Architecture Rule 9).

A pure-function module: it has no database or LLM access and consumes only
the `data`/`intent`/`x_field`/`y_field` it is handed. Column types are
inferred from the values actually passed in, never from database metadata.
"""
from datetime import datetime
from typing import Any, Optional

MAX_CATEGORY_CARDINALITY = 15

SHARE_HINTS = ("share", "proportion", "percentage", "percent", "%", "distribution of", "breakdown")
CORRELATION_HINTS = ("correlat", "relationship between", "vs", "versus", "relation")
# An explicit request for a particular chart type. These are generic phrasings,
# never tied to one question, and they only take effect when the data actually
# supports the requested shape (see build_chart_spec).
LINE_HINTS = ("line chart", "line graph", "as a line", "trend over", "over time", "trend line")
BAR_HINTS = ("bar chart", "bar graph", "as a bar", "column chart")
PIE_HINTS = ("pie chart", "as a pie", "donut", "doughnut")
SCATTER_HINTS = ("scatter chart", "scatter plot", "scatterplot", "as a scatter")

# Shared palette so every chart type reads as part of the DataPilot theme
# (NFR-6): cyan → indigo → violet with complementary accents.
_PRIMARY_COLOR = "#6366f1"
_SERIES_COLORS = [
    "#22d3ee",  # cyan
    "#6366f1",  # indigo
    "#8b5cf6",  # violet
    "#38bdf8",  # sky
    "#a78bfa",  # light violet
    "#2dd4bf",  # teal
    "#818cf8",  # periwinkle
    "#c084fc",  # orchid
    "#0ea5e9",  # blue
    "#f472b6",  # pink accent
    "#34d399",  # emerald accent
    "#fbbf24",  # amber accent
]


def _series_colors(count: int) -> list[str]:
    """Cycles the shared palette so any number of categories stays on-theme."""
    return [_SERIES_COLORS[index % len(_SERIES_COLORS)] for index in range(count)]


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# Time buckets SQL commonly produces. `%Y-%m` matters in particular:
# `strftime('%Y-%m', ...)` is the standard way to group by month, and without
# it a monthly series is mistaken for a plain category list and drawn as bars.
_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y-%m",
    "%Y/%m",
)


def _looks_like_date(value: Any) -> bool:
    if isinstance(value, datetime):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            continue
    return False


def _infer_column_type(values: list[Any]) -> str:
    non_none = [value for value in values if value is not None]
    if not non_none:
        return "categorical"
    if all(_is_numeric(value) for value in non_none):
        return "numeric"
    if all(_looks_like_date(value) for value in non_none):
        return "date"
    return "categorical"


def _humanize(name: str) -> str:
    words = str(name).replace("_", " ").split()
    return " ".join(word.capitalize() for word in words) if words else str(name)


def _error(error_type: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"type": error_type, "message": message}}


def _no_chart(reason: str) -> dict[str, Any]:
    return {"success": True, "chart_type": "none", "reason": reason}


def _matches(intent: Optional[str], hints: tuple[str, ...]) -> bool:
    return bool(intent) and any(hint in intent.lower() for hint in hints)


def _suggests_share(intent: Optional[str]) -> bool:
    return _matches(intent, SHARE_HINTS)


def _suggests_correlation(intent: Optional[str]) -> bool:
    return _matches(intent, CORRELATION_HINTS)


def _requested_chart_type(intent: Optional[str]) -> Optional[str]:
    """The chart type the user explicitly asked for, if any.

    Checked before the shape heuristics so "…as a line chart" is honored even
    when the x column is an ordered category (e.g. month buckets) rather than a
    parsed date. The request is still only granted when the data supports it.
    """
    for hints, chart_type in (
        (PIE_HINTS, "pie"),
        (SCATTER_HINTS, "scatter"),
        (LINE_HINTS, "line"),
        (BAR_HINTS, "bar"),
    ):
        if _matches(intent, hints):
            return chart_type
    return None


def build_chart_spec(
    data: dict[str, Any],
    intent: Optional[str] = None,
    x_field: Optional[str] = None,
    y_field: Optional[str] = None,
) -> dict[str, Any]:
    """Returns the Tool 3 contract payload: a chart spec, `chart_type: "none"`,
    or a structured `invalid_data_shape` error. Never raises."""
    columns = data.get("columns") or []
    rows = data.get("rows") or []

    if not columns or not isinstance(columns[0], str):
        return _error("invalid_data_shape", "data.columns must be a non-empty list of column names.")
    if not isinstance(rows, list):
        return _error("invalid_data_shape", "data.rows must be a list of rows.")
    for row in rows:
        if not isinstance(row, list) or len(row) != len(columns):
            return _error("invalid_data_shape", "Row length does not match column count.")

    if len(rows) < 2:
        return _no_chart("Result is a single scalar value; a table is clearer than a chart.")

    types = [_infer_column_type([row[index] for row in rows]) for index in range(len(columns))]
    numeric_indexes = [index for index, column_type in enumerate(types) if column_type == "numeric"]

    if not numeric_indexes:
        return _no_chart("The result has no numeric column to plot; a table is clearer than a chart.")

    # Resolve the numeric Y column, honoring the agent's hint when it names one.
    if y_field is not None and y_field in columns:
        y_index = columns.index(y_field)
        if types[y_index] != "numeric":
            y_index = numeric_indexes[0]
    else:
        y_index = numeric_indexes[0]

    # Resolve the X column: prefer the agent's hint, else a date column, else
    # the first non-Y column.
    if x_field is not None and x_field in columns and columns.index(x_field) != y_index:
        x_index = columns.index(x_field)
    else:
        candidates = [index for index in range(len(columns)) if index != y_index]
        date_candidates = [index for index in candidates if types[index] == "date"]
        numeric_candidates = [index for index in candidates if types[index] == "numeric"]
        wants_scatter = _matches(intent, SCATTER_HINTS) or _suggests_correlation(intent)
        if wants_scatter and numeric_candidates:
            # A correlation is between two measures, so pair the numeric column
            # rather than defaulting to a label column that happens to be first.
            x_index = numeric_candidates[0]
        elif date_candidates:
            x_index = date_candidates[0]
        else:
            x_index = candidates[0] if candidates else y_index

    x_type = types[x_index]
    x_label = _humanize(columns[x_index])
    y_label = _humanize(columns[y_index])
    x_values = [row[x_index] for row in rows]
    y_values = [row[y_index] for row in rows]

    requested = _requested_chart_type(intent)
    plottable = x_index != y_index and all(_is_numeric(value) for value in y_values)

    # An explicit request wins over the shape heuristics, but only when the
    # data genuinely supports it — the tool never fakes an unsuitable chart.
    if requested and plottable:
        if requested == "scatter" and x_type == "numeric":
            return _chart_result(
                "scatter",
                _scatter_trace(x_values, y_values),
                _layout(f"{y_label} vs {x_label}", x_label, y_label, axes=True),
                f"{y_label} vs {x_label}",
                x_label,
                y_label,
            )
        if requested == "line" and x_type in ("date", "categorical"):
            return _chart_result(
                "line",
                _line_trace(x_values, y_values),
                _layout(f"{y_label} over {x_label}", x_label, y_label, axes=True),
                f"{y_label} over {x_label}",
                x_label,
                y_label,
            )
        if (
            requested == "pie"
            and x_type == "categorical"
            and len({str(value) for value in x_values}) <= MAX_CATEGORY_CARDINALITY
        ):
            return _chart_result(
                "pie",
                _pie_trace(x_values, y_values),
                _layout(f"{y_label} by {x_label}", None, None, axes=False),
                f"{y_label} by {x_label}",
                x_label,
                y_label,
            )
        if (
            requested == "bar"
            and x_type in ("categorical", "date")
            and len({str(value) for value in x_values}) <= MAX_CATEGORY_CARDINALITY
        ):
            return _chart_result(
                "bar",
                _bar_trace(x_values, y_values),
                _layout(f"{y_label} by {x_label}", x_label, y_label, axes=True),
                f"{y_label} by {x_label}",
                x_label,
                y_label,
            )

    # Rule: two numeric columns, no time/category axis, and a correlation
    # intent → scatter (bonus).
    if x_type == "numeric" and x_index != y_index and _suggests_correlation(intent):
        return _chart_result(
            "scatter",
            _scatter_trace(x_values, y_values),
            _layout(f"{y_label} vs {x_label}", x_label, y_label, axes=True),
            f"{y_label} vs {x_label}",
            x_label,
            y_label,
        )

    # Rule: a date/time column plus a numeric column → line.
    if x_type == "date":
        return _chart_result(
            "line",
            _line_trace(x_values, y_values),
            _layout(f"{y_label} over {x_label}", x_label, y_label, axes=True),
            f"{y_label} over {x_label}",
            x_label,
            y_label,
        )

    # Remaining chartable shape is categorical + numeric.
    if x_type != "categorical" or x_index == y_index:
        return _no_chart("The result's shape is not a comparison, trend, or distribution.")
    if not all(_is_numeric(value) for value in y_values):
        return _no_chart("The numeric column contains non-numeric values.")

    cardinality = len({str(value) for value in x_values})
    if cardinality > MAX_CATEGORY_CARDINALITY:
        # Too many bars to read — but if the row carries a second measure, the
        # useful view is one measure against the other (e.g. price vs units for
        # every product), so plot that instead of giving up on a chart.
        if len(numeric_indexes) >= 2:
            alt_x = next(index for index in numeric_indexes if index != y_index)
            alt_x_label = _humanize(columns[alt_x])
            return _chart_result(
                "scatter",
                _scatter_trace([row[alt_x] for row in rows], y_values),
                _layout(f"{y_label} vs {alt_x_label}", alt_x_label, y_label, axes=True),
                f"{y_label} vs {alt_x_label}",
                alt_x_label,
                y_label,
            )
        return _no_chart(
            f"The category column has {cardinality} distinct values, too many for a readable chart."
        )

    if _suggests_share(intent):
        return _chart_result(
            "pie",
            _pie_trace(x_values, y_values),
            _layout(f"{y_label} by {x_label}", None, None, axes=False),
            f"{y_label} by {x_label}",
            x_label,
            y_label,
        )

    return _chart_result(
        "bar",
        _bar_trace(x_values, y_values),
        _layout(f"{y_label} by {x_label}", x_label, y_label, axes=True),
        f"{y_label} by {x_label}",
        x_label,
        y_label,
    )


def _chart_result(
    chart_type: str,
    trace: dict[str, Any],
    layout: dict[str, Any],
    title: str,
    x_label: str,
    y_label: str,
) -> dict[str, Any]:
    return {
        "success": True,
        "chart_type": chart_type,
        "plotly_spec": {"data": [trace], "layout": layout},
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
    }


def _layout(title: str, x_label: Optional[str], y_label: Optional[str], axes: bool) -> dict[str, Any]:
    layout: dict[str, Any] = {
        "autosize": True,
        "margin": {"l": 50, "r": 20, "t": 50, "b": 40},
        "title": {"text": title},
    }
    if axes:
        layout["xaxis"] = {"title": x_label}
        layout["yaxis"] = {"title": y_label}
        layout["showlegend"] = False
    else:
        # Pie: the slice text carries the percentage, so the legend is what
        # names each category.
        layout["showlegend"] = True
        layout["legend"] = {"orientation": "v", "x": 1, "xanchor": "right", "y": 0.5}
    return layout


def _bar_trace(x_values: list[Any], y_values: list[Any]) -> dict[str, Any]:
    # Per-bar colors from the shared palette so a comparison reads at a glance
    # instead of being one flat block of color.
    return {
        "type": "bar",
        "x": x_values,
        "y": y_values,
        "marker": {
            "color": _series_colors(len(x_values)),
            "line": {"color": "rgba(255,255,255,0.10)", "width": 1},
        },
    }


def _line_trace(x_values: list[Any], y_values: list[Any]) -> dict[str, Any]:
    return {
        "type": "scatter",
        "mode": "lines+markers",
        "x": x_values,
        "y": y_values,
        "line": {"color": "#22d3ee", "width": 2.5, "shape": "spline", "smoothing": 0.4},
        "marker": {"color": "#22d3ee", "size": 7, "line": {"color": "#0b1224", "width": 1.5}},
    }


def _pie_trace(x_values: list[Any], y_values: list[Any]) -> dict[str, Any]:
    return {
        "type": "pie",
        "labels": x_values,
        "values": y_values,
        "hole": 0.45,
        "sort": False,
        "textinfo": "percent",
        "textposition": "inside",
        "marker": {
            "colors": _series_colors(len(x_values)),
            "line": {"color": "#0b1224", "width": 2},
        },
    }


def _scatter_trace(x_values: list[Any], y_values: list[Any]) -> dict[str, Any]:
    return {
        "type": "scatter",
        "mode": "markers",
        "x": x_values,
        "y": y_values,
        "marker": {
            "color": "#8b5cf6",
            "size": 9,
            "opacity": 0.85,
            "line": {"color": "#22d3ee", "width": 1},
        },
    }
