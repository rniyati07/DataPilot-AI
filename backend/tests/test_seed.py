from pathlib import Path

from sqlalchemy import create_engine, inspect

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"

EXPECTED_TABLES = {
    "customers",
    "categories",
    "products",
    "orders",
    "order_items",
    "inventory",
    "payments",
}


def test_ecommerce_db_exists():
    assert DB_PATH.exists(), "ecommerce.db must be seeded before running tests"


def test_ecommerce_db_has_expected_schema():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(tables)


def test_ecommerce_db_has_sample_rows():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        from sqlalchemy import text

        for table in EXPECTED_TABLES:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            assert count > 0, f"{table} should have seeded rows"


def test_ecommerce_db_foreign_keys_present():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    inspector = inspect(engine)
    products_fks = inspector.get_foreign_keys("products")
    assert any(fk["referred_table"] == "categories" for fk in products_fks)
    order_items_fks = inspector.get_foreign_keys("order_items")
    referred_tables = {fk["referred_table"] for fk in order_items_fks}
    assert {"orders", "products"}.issubset(referred_tables)
