"""Refinement tests — chart-type selection and palette.

These pin the two bugs found by inspecting the running UI:
  * a monthly series (`strftime('%Y-%m', …)` → "2025-02") was typed as a plain
    category and drawn as bars instead of a line;
  * an explicit "…as a line/pie/scatter chart" request had no effect at all,
    because only share/correlation hints existed.

Deterministic: the builder is a pure function, so no LLM or database is used.
"""
import pytest

from app.viz.plotly_builder import _looks_like_date, build_chart_spec

MONTHS = ["2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07"]
MONTHLY = {
    "columns": ["month", "total_revenue"],
    "rows": [[m, v] for m, v in zip(MONTHS, [2245.28, 788.26, 990.84, 2245.28, 788.26, 990.84])],
}
CATEGORIES = {
    "columns": ["category", "total_revenue"],
    "rows": [
        ["Electronics", 2960.72],
        ["Home & Kitchen", 1412.8],
        ["Sportswear", 1317.78],
        ["Beauty", 927.94],
        ["Toys", 852.8],
        ["Books", 576.72],
    ],
}
PRICE_UNITS = {
    "columns": ["product_name", "price", "units_sold"],
    "rows": [["a", 9.99, 6], ["b", 59.99, 6], ["c", 249.99, 8], ["d", 21.99, 8]],
}


# --- Time-bucket recognition ----------------------------------------------


@pytest.mark.parametrize("value", ["2025-02", "2025-02-11", "2025/02", "2025-02-11 10:30:00"])
def test_sql_time_buckets_are_recognized_as_dates(value):
    assert _looks_like_date(value) is True


@pytest.mark.parametrize("value", ["Electronics", "4K Monitor", "", "not-a-date", "12"])
def test_plain_categories_are_not_dates(value):
    assert _looks_like_date(value) is False


def test_month_bucket_series_becomes_a_line_without_any_hint():
    """The regression: month buckets are a trend, not a category comparison."""
    assert build_chart_spec(MONTHLY)["chart_type"] == "line"


# --- Explicit chart-type requests -----------------------------------------


@pytest.mark.parametrize(
    "intent",
    [
        "Show me the monthly revenue trend over the available order history as a line chart.",
        "Plot monthly sales as a line graph.",
        "Show how revenue changed month by month using a line chart.",
        "Show the revenue trend over time.",
    ],
)
def test_line_requests_produce_a_line(intent):
    assert build_chart_spec(MONTHLY, intent=intent)["chart_type"] == "line"


@pytest.mark.parametrize(
    "intent",
    [
        "Show me the revenue share by product category as a pie chart.",
        "Break revenue down by category as a pie chart.",
    ],
)
def test_pie_requests_produce_a_pie(intent):
    assert build_chart_spec(CATEGORIES, intent=intent)["chart_type"] == "pie"


def test_bar_remains_the_default_for_a_plain_comparison():
    assert build_chart_spec(CATEGORIES, intent="Compare revenue by category.")["chart_type"] == "bar"


@pytest.mark.parametrize(
    "intent",
    [
        "Show product price versus total units sold using a scatter chart.",
        "Show the relationship between product price and units sold.",
    ],
)
def test_scatter_requests_pair_two_numeric_columns(intent):
    result = build_chart_spec(PRICE_UNITS, intent=intent)
    assert result["chart_type"] == "scatter"
    # x must be the other measure, not the label column that happens to be first.
    assert {result["x_label"], result["y_label"]} == {"Price", "Units Sold"}


def test_an_unsupported_request_does_not_force_a_chart():
    """Asking for a pie over data with no category column must not fabricate one."""
    numeric_only = {"columns": ["price", "units"], "rows": [[1.0, 2], [3.0, 4]]}
    assert build_chart_spec(numeric_only, intent="as a pie chart")["chart_type"] != "pie"


# --- Palette / spec shape --------------------------------------------------


def test_bar_uses_a_distinct_colour_per_category():
    trace = build_chart_spec(CATEGORIES)["plotly_spec"]["data"][0]
    colors = trace["marker"]["color"]
    assert isinstance(colors, list)
    assert len(colors) == len(CATEGORIES["rows"])
    assert len(set(colors)) > 1  # not one flat block of colour


def test_pie_spec_carries_labels_values_and_a_legend():
    result = build_chart_spec(CATEGORIES, intent="revenue share as a pie chart")
    trace = result["plotly_spec"]["data"][0]
    layout = result["plotly_spec"]["layout"]

    assert trace["type"] == "pie"
    assert len(trace["labels"]) == len(trace["values"]) == 6
    assert all(isinstance(v, (int, float)) for v in trace["values"])
    assert len(trace["marker"]["colors"]) == 6
    # The slice text shows percentages, so the legend must name the categories.
    assert layout["showlegend"] is True
    # A pie has no cartesian axes; emitting them confuses the renderer.
    assert "xaxis" not in layout and "yaxis" not in layout


def test_cartesian_charts_declare_axes_and_hide_the_legend():
    layout = build_chart_spec(CATEGORIES)["plotly_spec"]["layout"]
    assert layout["xaxis"]["title"] == "Category"
    assert layout["yaxis"]["title"] == "Total Revenue"
    assert layout["showlegend"] is False


# --- Contingencies ---------------------------------------------------------


def test_single_row_result_produces_no_chart():
    assert build_chart_spec({"columns": ["total"], "rows": [[42]]})["chart_type"] == "none"


def test_empty_result_produces_no_chart():
    assert build_chart_spec({"columns": ["a", "b"], "rows": []})["chart_type"] == "none"


def test_result_without_a_numeric_column_produces_no_chart():
    data = {"columns": ["a", "b"], "rows": [["x", "y"], ["p", "q"]]}
    assert build_chart_spec(data)["chart_type"] == "none"
