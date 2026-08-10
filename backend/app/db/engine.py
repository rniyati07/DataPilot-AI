"""Engine factory: builds a SQLAlchemy engine for an arbitrary resolved
database path — no longer a single global engine tied to DATABASE_URL
(Phase 3 requirement, so a session's upload can become the active engine)."""
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine


@lru_cache(maxsize=32)
def _cached_engine(db_path_str: str) -> Engine:
    return create_engine(
        f"sqlite:///{db_path_str}",
        connect_args={"check_same_thread": False},
    )


def get_engine(db_path: Path) -> Engine:
    return _cached_engine(str(db_path.resolve()))
