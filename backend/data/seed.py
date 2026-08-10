"""Seeds the sample/demo e-commerce SQLite database (PRD §12, Architecture §10).

Idempotent and re-runnable: creates tables if missing, and only inserts rows
if the database is empty. This is the ONLY place the e-commerce schema is
defined — it must never be hardcoded into the Database Manager, tools, or
frontend (CLAUDE.md §10).

Usage: python data/seed.py   (run from backend/)
"""
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)

DB_PATH = Path(__file__).resolve().parent / "ecommerce.db"

metadata = MetaData()

customers = Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("email", String(150), nullable=False, unique=True),
    Column("created_at", DateTime, nullable=False),
)

categories = Table(
    "categories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False, unique=True),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(150), nullable=False),
    Column("category_id", Integer, ForeignKey("categories.id"), nullable=False),
    Column("price", Float, nullable=False),
    Column("sku", String(50), nullable=False, unique=True),
)

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("customer_id", Integer, ForeignKey("customers.id"), nullable=False),
    Column("order_date", Date, nullable=False),
    Column("status", String(30), nullable=False),
)

order_items = Table(
    "order_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Float, nullable=False),
)

inventory = Table(
    "inventory",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False, unique=True),
    Column("quantity_on_hand", Integer, nullable=False),
    Column("warehouse_location", String(50), nullable=False),
)

payments = Table(
    "payments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False, unique=True),
    Column("amount", Float, nullable=False),
    Column("payment_method", String(30), nullable=False),
    Column("paid_at", DateTime, nullable=False),
)

CATEGORY_NAMES = ["Electronics", "Home & Kitchen", "Sportswear", "Books", "Toys", "Beauty"]

PRODUCT_TEMPLATES = [
    ("Wireless Headphones", 0, 59.99),
    ("Smartphone Stand", 0, 15.49),
    ("USB-C Hub", 0, 34.99),
    ("Bluetooth Speaker", 0, 44.50),
    ("4K Monitor", 0, 249.99),
    ("Non-Stick Frying Pan", 1, 22.99),
    ("Ceramic Mug Set", 1, 18.50),
    ("Electric Kettle", 1, 29.99),
    ("Knife Block Set", 1, 64.00),
    ("Air Fryer", 1, 89.99),
    ("Running Shoes", 2, 74.99),
    ("Yoga Mat", 2, 25.00),
    ("Dumbbell Set", 2, 55.00),
    ("Cycling Gloves", 2, 19.99),
    ("Sports Water Bottle", 2, 12.99),
    ("Mystery Novel", 3, 14.99),
    ("Cookbook: World Cuisine", 3, 21.99),
    ("Children's Picture Book", 3, 9.99),
    ("Self-Help Guide", 3, 16.50),
    ("Science Fiction Anthology", 3, 18.99),
    ("Building Blocks Set", 4, 32.99),
    ("Remote Control Car", 4, 45.00),
    ("Puzzle 1000 Pieces", 4, 13.99),
    ("Plush Teddy Bear", 4, 17.50),
    ("Board Game Classic", 4, 27.99),
    ("Moisturizing Cream", 5, 23.50),
    ("Shampoo & Conditioner Set", 5, 19.99),
    ("Lipstick Set", 5, 26.00),
    ("Facial Cleanser", 5, 14.50),
    ("Perfume 50ml", 5, 58.00),
]

ORDER_STATUSES = ["completed", "shipped", "processing", "cancelled"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "upi"]
WAREHOUSES = ["WH-NORTH", "WH-SOUTH", "WH-EAST", "WH-WEST"]


def build_engine():
    return create_engine(f"sqlite:///{DB_PATH}")


def seed() -> None:
    engine = build_engine()
    metadata.create_all(engine)

    with engine.begin() as conn:
        existing = conn.execute(select(func.count()).select_from(customers)).scalar_one()
        if existing:
            print(f"ecommerce.db already seeded ({existing} customers) — skipping.")
            return

        conn.execute(
            categories.insert(),
            [{"id": i + 1, "name": name} for i, name in enumerate(CATEGORY_NAMES)],
        )

        conn.execute(
            customers.insert(),
            [
                {
                    "id": i + 1,
                    "name": f"Customer {i + 1}",
                    "email": f"customer{i + 1}@example.com",
                    "created_at": date(2025, 1, 1) + timedelta(days=i * 5),
                }
                for i in range(20)
            ],
        )

        conn.execute(
            products.insert(),
            [
                {
                    "id": i + 1,
                    "name": name,
                    "category_id": category_idx + 1,
                    "price": price,
                    "sku": f"SKU-{i + 1:04d}",
                }
                for i, (name, category_idx, price) in enumerate(PRODUCT_TEMPLATES)
            ],
        )

        conn.execute(
            inventory.insert(),
            [
                {
                    "id": i + 1,
                    "product_id": i + 1,
                    "quantity_on_hand": 20 + (i * 7) % 180,
                    "warehouse_location": WAREHOUSES[i % len(WAREHOUSES)],
                }
                for i in range(len(PRODUCT_TEMPLATES))
            ],
        )

        order_rows = []
        order_item_rows = []
        payment_rows = []
        item_id = 1
        num_orders = 60
        for i in range(num_orders):
            order_id = i + 1
            customer_id = (i % 20) + 1
            order_date = date(2025, 2, 1) + timedelta(days=i * 3)
            status = ORDER_STATUSES[i % len(ORDER_STATUSES)]
            order_rows.append(
                {
                    "id": order_id,
                    "customer_id": customer_id,
                    "order_date": order_date,
                    "status": status,
                }
            )

            num_items = 1 + (i % 3)
            order_total = 0.0
            for j in range(num_items):
                product_id = ((i + j) % len(PRODUCT_TEMPLATES)) + 1
                quantity = 1 + (j % 3)
                unit_price = PRODUCT_TEMPLATES[product_id - 1][2]
                order_total += quantity * unit_price
                order_item_rows.append(
                    {
                        "id": item_id,
                        "order_id": order_id,
                        "product_id": product_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )
                item_id += 1

            if status != "cancelled":
                payment_rows.append(
                    {
                        "id": order_id,
                        "order_id": order_id,
                        "amount": round(order_total, 2),
                        "payment_method": PAYMENT_METHODS[i % len(PAYMENT_METHODS)],
                        "paid_at": order_date,
                    }
                )

        conn.execute(orders.insert(), order_rows)
        conn.execute(order_items.insert(), order_item_rows)
        conn.execute(payments.insert(), payment_rows)

        print(
            f"Seeded ecommerce.db: {len(CATEGORY_NAMES)} categories, "
            f"20 customers, {len(PRODUCT_TEMPLATES)} products, {num_orders} orders, "
            f"{len(order_item_rows)} order_items, {len(PRODUCT_TEMPLATES)} inventory rows, "
            f"{len(payment_rows)} payments."
        )


if __name__ == "__main__":
    seed()
