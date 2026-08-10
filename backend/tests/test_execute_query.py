"""Phase 5 tests — Tool 2 contract (04_AGENT_TOOLS.md §12).

No test here relies on an LLM; the validator and execution path are
deterministic code.
"""
from pathlib import Path

import pytest

from app.config import settings
from app.tools.execute_query import ExecuteQueryInput, execute_query

SESSION = "eq-session"


# --- Valid statements -----------------------------------------------------


def test_simple_select():
    result = execute_query(SESSION, "SELECT name, price FROM products ORDER BY price DESC")
    assert result["success"] is True
    assert result["columns"] == ["name", "price"]
    assert result["row_count"] > 0
    assert isinstance(result["rows"][0], list)


def test_aggregation():
    result = execute_query(SESSION, "SELECT COUNT(*) AS total FROM orders")
    assert result["success"] is True
    assert result["rows"][0][0] > 0


def test_join_order_by_and_limit():
    result = execute_query(
        SESSION,
        "SELECT p.name AS name, SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM products p JOIN order_items oi ON oi.product_id = p.id "
        "GROUP BY p.name ORDER BY revenue DESC LIMIT 5",
    )
    assert result["success"] is True
    assert result["columns"] == ["name", "revenue"]
    assert result["row_count"] == 5
    revenues = [row[1] for row in result["rows"]]
    assert revenues == sorted(revenues, reverse=True)


def test_cte_select():
    result = execute_query(
        SESSION,
        "WITH top AS (SELECT id, name FROM products LIMIT 3) SELECT name FROM top",
    )
    assert result["success"] is True
    assert result["row_count"] == 3


def test_empty_result_is_success_not_error():
    result = execute_query(SESSION, "SELECT * FROM products WHERE price < 0")
    assert result["success"] is True
    assert result["rows"] == []
    assert result["row_count"] == 0
    assert result["truncated"] is False


def test_quoted_string_literal_query_executes():
    result = execute_query(SESSION, "SELECT 'delete' AS status")
    assert result["success"] is True
    assert result["rows"] == [["delete"]]


# --- Rejected statements --------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO customers (name, email, created_at) VALUES ('x','y','z')",
        "UPDATE customers SET name = 'x'",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN x INT",
        "TRUNCATE TABLE customers",
        "CREATE TABLE t (id INT)",
        "ATTACH DATABASE 'other.db' AS other",
        "PRAGMA table_info(customers)",
        "SELECT 1; DROP TABLE customers;",
    ],
)
def test_destructive_and_multi_statement_rejected(sql):
    result = execute_query(SESSION, sql)
    assert result["success"] is False
    assert result["error"]["type"] == "validation_rejected"


def test_rejection_happens_before_touching_database(monkeypatch):
    """A rejected statement must never reach the execution path."""
    from app.db import access_layer

    def _fail(*args, **kwargs):
        raise AssertionError("execute_read_only must not be called for rejected SQL")

    monkeypatch.setattr(access_layer, "execute_read_only", _fail)
    result = execute_query(SESSION, "DROP TABLE customers")
    assert result["error"]["type"] == "validation_rejected"


def test_destructive_sql_did_not_modify_database():
    execute_query(SESSION, "DELETE FROM customers")
    remaining = execute_query(SESSION, "SELECT COUNT(*) FROM customers")
    assert remaining["rows"][0][0] > 0


# --- Named regression tests ----------------------------------------------


def test_updated_at_identifier_not_falsely_rejected(make_db):
    make_db(
        "regress-1",
        [
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, updated_at TEXT, created_by TEXT)",
            "INSERT INTO orders (updated_at, created_by) VALUES ('2026-01-01', 'alice')",
        ],
    )
    result = execute_query("regress-1", "SELECT updated_at, created_by FROM orders")
    assert result["success"] is True
    assert result["rows"] == [["2026-01-01", "alice"]]


def test_select_delete_literal_not_falsely_rejected():
    result = execute_query(SESSION, "SELECT 'delete' AS status")
    assert result["success"] is True


def test_select_update_literal_not_falsely_rejected():
    result = execute_query(SESSION, "SELECT 'update' AS status")
    assert result["success"] is True


# --- Result handling ------------------------------------------------------


def test_hard_row_ceiling_enforced(monkeypatch):
    monkeypatch.setattr(settings, "hard_row_ceiling", 3)
    # The agent asks for far more than the ceiling permits.
    result = execute_query(SESSION, "SELECT * FROM order_items", max_rows=500)
    assert result["row_count"] == 3
    assert result["truncated"] is True


def test_agent_can_lower_but_not_raise_the_cap(monkeypatch):
    monkeypatch.setattr(settings, "hard_row_ceiling", 10)
    lowered = execute_query(SESSION, "SELECT * FROM order_items", max_rows=2)
    assert lowered["row_count"] == 2
    assert lowered["truncated"] is True


def test_truncated_false_when_result_fits():
    result = execute_query(SESSION, "SELECT * FROM categories", max_rows=100)
    assert result["truncated"] is False
    assert result["row_count"] == 6


def test_default_row_cap_applied(monkeypatch):
    monkeypatch.setattr(settings, "default_max_rows", 4)
    result = execute_query(SESSION, "SELECT * FROM order_items")
    assert result["row_count"] == 4
    assert result["truncated"] is True


def test_values_are_json_safe(make_db):
    import json

    make_db(
        "json-safe",
        [
            "CREATE TABLE mixed (i INTEGER, r REAL, t TEXT, b BLOB, n INTEGER)",
            "INSERT INTO mixed VALUES (1, 2.5, 'text', X'414243', NULL)",
        ],
    )
    result = execute_query("json-safe", "SELECT * FROM mixed")
    assert result["success"] is True
    json.dumps(result["rows"])  # must not raise


# --- Structured errors ----------------------------------------------------


def test_sql_syntax_error_returned_structurally():
    result = execute_query(SESSION, "SELECT FROM WHERE")
    assert result["success"] is False
    assert result["error"]["type"] == "sql_error"


def test_unknown_column_error_preserves_driver_detail():
    """The agent needs this detail to self-correct in Phase 12."""
    result = execute_query(SESSION, "SELECT revenues FROM products")
    assert result["error"]["type"] == "sql_error"
    assert "revenues" in result["error"]["message"]


def test_error_message_does_not_leak_filesystem_paths():
    result = execute_query(SESSION, "SELECT nope FROM products")
    message = result["error"]["message"]
    assert "Downloads" not in message
    assert ".db" not in message


def test_database_unavailable_returned_structurally(monkeypatch):
    from app.db import database_manager

    monkeypatch.setattr(
        database_manager,
        "get_active_database_path",
        lambda session_id: Path("/nonexistent/dir/missing.db"),
    )
    result = execute_query("broken", "SELECT 1")
    assert result["success"] is False
    assert result["error"]["type"] in ("database_unavailable", "sql_error")
    assert "missing.db" not in result["error"]["message"]


def test_timeout_returned_structurally(monkeypatch):
    """A zero-second budget makes the progress handler abort immediately."""
    monkeypatch.setattr(settings, "query_timeout_seconds", -1)
    result = execute_query(
        SESSION,
        "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) "
        "SELECT COUNT(*) FROM c",
    )
    assert result["success"] is False
    assert result["error"]["type"] == "timeout"


# --- Behaves identically on an uploaded database --------------------------


def test_guard_behaves_identically_on_uploaded_database(make_db):
    make_db(
        "uploaded",
        [
            "CREATE TABLE library_books (id INTEGER PRIMARY KEY, title TEXT, updated_at TEXT)",
            "INSERT INTO library_books (title, updated_at) VALUES ('Dune', '2026-01-01')",
        ],
    )
    assert execute_query("uploaded", "SELECT title FROM library_books")["success"] is True
    assert execute_query("uploaded", "SELECT updated_at FROM library_books")["success"] is True
    assert execute_query("uploaded", "SELECT 'delete' AS s")["success"] is True

    rejected = execute_query("uploaded", "DROP TABLE library_books")
    assert rejected["error"]["type"] == "validation_rejected"


# --- Input model ----------------------------------------------------------


def test_input_model_rejects_non_positive_max_rows():
    with pytest.raises(ValueError):
        ExecuteQueryInput(sql="SELECT 1", max_rows=0)


def test_input_model_has_no_session_id_field():
    """session_id must never be LLM-facing (pending correction 2)."""
    assert "session_id" not in ExecuteQueryInput.model_fields
