import sqlite3


def make_sqlite_bytes(table_name: str = "items") -> bytes:
    """Builds a tiny genuine SQLite database in memory and returns its raw bytes."""
    conn = sqlite3.connect(":memory:")
    conn.execute(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute(f"INSERT INTO {table_name} (name) VALUES ('sample')")
    conn.commit()
    data = conn.serialize()
    conn.close()
    return bytes(data)
