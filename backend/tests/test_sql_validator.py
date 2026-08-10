"""Phase 5 tests — the read-only SQL guard, in isolation from database I/O.

These tests are pure and deterministic: no LLM, no database (Tool 2 §12).
"""
import pytest

from app.db.sql_validator import SqlValidationError, mask_quoted_spans, split_statements, validate


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM products",
        "SELECT COUNT(*) FROM orders",
        "SELECT c.name, SUM(oi.quantity) FROM order_items oi JOIN customers c ON c.id = oi.id "
        "GROUP BY c.name ORDER BY 2 DESC LIMIT 5",
        "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent",
        "  select 1  ",
        "SELECT * FROM products;",
        "-- a leading comment\nSELECT 1",
        "/* block comment */ SELECT 1",
        "SELECT 'a;b' AS contains_semicolon",
    ],
)
def test_valid_statements_accepted(sql):
    assert validate(sql).sql


@pytest.mark.parametrize(
    "sql,keyword",
    [
        ("INSERT INTO customers (name) VALUES ('x')", "INSERT"),
        ("UPDATE customers SET name = 'x'", "UPDATE"),
        ("DELETE FROM customers", "DELETE"),
        ("DROP TABLE customers", "DROP"),
        ("ALTER TABLE customers ADD COLUMN x INT", "ALTER"),
        ("TRUNCATE TABLE customers", "TRUNCATE"),
        ("CREATE TABLE t (id INT)", "CREATE"),
        ("ATTACH DATABASE 'other.db' AS other", "ATTACH"),
        ("PRAGMA table_info(customers)", "PRAGMA"),
        ("REPLACE INTO customers VALUES (1)", "REPLACE"),
        ("VACUUM", "VACUUM"),
    ],
)
def test_destructive_statements_rejected(sql, keyword):
    with pytest.raises(SqlValidationError):
        validate(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE customers;",
        "SELECT * FROM customers; DELETE FROM customers",
        "SELECT 1; SELECT 2",
    ],
)
def test_multi_statement_rejected(sql):
    with pytest.raises(SqlValidationError, match="single statement"):
        validate(sql)


def test_destructive_keyword_hidden_in_cte_rejected():
    with pytest.raises(SqlValidationError):
        validate("WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x")


@pytest.mark.parametrize("sql", ["", "   ", "\n\t ", "-- only a comment", "/* only */"])
def test_empty_input_rejected(sql):
    with pytest.raises(SqlValidationError):
        validate(sql)


# --- Named regression tests from Tool 2 §12 -------------------------------


def test_word_boundary_regression_updated_at_not_rejected():
    """A column named `updated_at` must not trip the UPDATE rule."""
    assert validate("SELECT updated_at FROM orders").sql


def test_word_boundary_regression_created_by_not_rejected():
    assert validate("SELECT created_by, updated_at FROM audit_log").sql


def test_quoted_literal_regression_delete_not_rejected():
    """`SELECT 'delete' AS status` must not trip the DELETE rule."""
    assert validate("SELECT 'delete' AS status").sql


def test_quoted_literal_regression_update_not_rejected():
    assert validate("SELECT 'update' AS status").sql


def test_quoted_literal_with_multiple_keywords_not_rejected():
    assert validate("SELECT 'drop table customers' AS note FROM products").sql


def test_double_quoted_identifier_not_rejected():
    assert validate('SELECT "updated_at" FROM orders').sql


def test_escaped_quote_inside_literal_handled():
    assert validate("SELECT 'it''s a delete' AS x").sql


# --- Helper behavior ------------------------------------------------------


def test_mask_preserves_length_and_delimiters():
    original = "SELECT 'delete' AS s"
    masked = mask_quoted_spans(original)
    assert len(masked) == len(original)
    assert "delete" not in masked
    assert masked.count("'") == 2


def test_semicolon_inside_quotes_does_not_split():
    assert len(split_statements("SELECT 'a;b' AS x")) == 1


def test_has_limit_detection():
    assert validate("SELECT * FROM t LIMIT 10").has_limit is True
    assert validate("SELECT * FROM t").has_limit is False
    assert validate("SELECT 'limit' AS x").has_limit is False


def test_trailing_semicolon_stripped():
    assert validate("SELECT 1;").sql == "SELECT 1"
