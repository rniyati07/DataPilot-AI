"""Phase 4 tests — Tool 1 contract (04_AGENT_TOOLS.md §12)."""
from pathlib import Path

import pytest

from app.tools.get_schema import GetSchemaInput, get_schema

SEED_TABLES = {
    "customers",
    "categories",
    "products",
    "orders",
    "order_items",
    "inventory",
    "payments",
}


def _table(result, name):
    return next(t for t in result["tables"] if t["name"] == name)


def _column(table, name):
    return next(c for c in table["columns"] if c["name"] == name)


def test_returns_seeded_tables_for_default_database():
    result = get_schema("s1")
    assert result["success"] is True
    assert SEED_TABLES.issubset({t["name"] for t in result["tables"]})
    assert result["table_count"] == len(result["tables"])
    assert result["cached"] is False


def test_columns_types_and_primary_keys_are_correct():
    products = _table(get_schema("s1"), "products")
    id_column = _column(products, "id")
    assert id_column["primary_key"] is True
    assert "INT" in id_column["type"].upper()

    name_column = _column(products, "name")
    assert name_column["primary_key"] is False
    assert name_column["nullable"] is False


def test_foreign_keys_are_correct():
    products = _table(get_schema("s1"), "products")
    assert {
        "column": "category_id",
        "references_table": "categories",
        "references_column": "id",
    } in products["foreign_keys"]


def test_empty_database_is_success_not_error(make_db):
    make_db("empty-session", [])
    result = get_schema("empty-session")
    assert result["success"] is True
    assert result["tables"] == []
    assert result["table_count"] == 0


def test_unavailable_database_returns_structured_error(monkeypatch):
    from app.db import database_manager

    monkeypatch.setattr(
        database_manager,
        "get_active_database_path",
        lambda session_id: Path("/nonexistent/dir/missing.db"),
    )
    result = get_schema("broken-session")
    assert result["success"] is False
    assert result["error"]["type"] in ("database_unavailable", "schema_discovery_failed")
    # Must not leak the path.
    assert "missing.db" not in result["error"]["message"]


def test_differently_shaped_database_returns_its_own_schema(make_db):
    make_db(
        "hospital",
        [
            "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL)",
            "CREATE TABLE doctors (id INTEGER PRIMARY KEY, name TEXT, "
            "department_id INTEGER REFERENCES departments(id))",
            "CREATE TABLE patients (id INTEGER PRIMARY KEY, full_name TEXT)",
        ],
    )
    result = get_schema("hospital")
    names = {t["name"] for t in result["tables"]}
    assert names == {"departments", "doctors", "patients"}
    # None of the e-commerce schema leaks in.
    assert not (names & SEED_TABLES)

    doctors = _table(result, "doctors")
    assert doctors["foreign_keys"] == [
        {"column": "department_id", "references_table": "departments", "references_column": "id"}
    ]


def test_no_seed_schema_names_hardcoded_in_tool_source():
    """FR-3: the tool must not contain any seed table/column literal."""
    source = Path(__file__).resolve().parent.parent / "app" / "tools" / "get_schema.py"
    text = source.read_text(encoding="utf-8").lower()
    for table_name in SEED_TABLES:
        assert table_name not in text, f"{table_name} must not appear in get_schema source"


def test_cache_hit_on_second_call():
    assert get_schema("s1")["cached"] is False
    assert get_schema("s1")["cached"] is True


def test_refresh_forces_fresh_inspection():
    get_schema("s1")
    assert get_schema("s1", refresh=True)["cached"] is False


def test_filtered_call_can_hit_cache_and_filters_correctly():
    get_schema("s1")  # populates the full-schema cache
    result = get_schema("s1", table_filter=["products"])
    assert result["cached"] is True
    assert [t["name"] for t in result["tables"]] == ["products"]
    assert result["table_count"] == 1


def test_unknown_table_filter_names_are_omitted_not_fatal():
    result = get_schema("s1", table_filter=["products", "no_such_table"])
    assert result["success"] is True
    assert [t["name"] for t in result["tables"]] == ["products"]


def test_sessions_do_not_share_schema(make_db):
    make_db("session-lib", ["CREATE TABLE library_books (id INTEGER PRIMARY KEY, title TEXT)"])

    lib = {t["name"] for t in get_schema("session-lib")["tables"]}
    default = {t["name"] for t in get_schema("session-default")["tables"]}

    assert lib == {"library_books"}
    assert SEED_TABLES.issubset(default)
    assert "library_books" not in default


def test_switching_database_invalidates_stale_schema_cache(make_db):
    # Prime the cache against the default database.
    assert SEED_TABLES.issubset({t["name"] for t in get_schema("switcher")["tables"]})
    assert get_schema("switcher")["cached"] is True

    # Switch this session's active database; the cache must not be reused.
    make_db("switcher", ["CREATE TABLE only_new_table (id INTEGER PRIMARY KEY)"])

    result = get_schema("switcher")
    assert result["cached"] is False
    assert [t["name"] for t in result["tables"]] == ["only_new_table"]


def test_input_model_rejects_empty_table_filter():
    with pytest.raises(ValueError):
        GetSchemaInput(table_filter=[])
    with pytest.raises(ValueError):
        GetSchemaInput(table_filter=["   "])


def test_input_model_defaults():
    parsed = GetSchemaInput()
    assert parsed.table_filter is None
    assert parsed.refresh is False


def test_input_model_has_no_session_id_field():
    """session_id must never be LLM-facing (pending correction 2)."""
    assert "session_id" not in GetSchemaInput.model_fields
