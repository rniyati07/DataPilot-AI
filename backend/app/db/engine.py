"""Engine factory: builds a SQLAlchemy engine for an arbitrary resolved
database path — no longer a single global engine tied to DATABASE_URL
(Phase 3 requirement, so a session's upload can become the active engine)."""
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import Engine, create_engine


@lru_cache(maxsize=32)
def _cached_engine(db_path_str: str) -> Engine:
    return create_engine(
        f"sqlite:///{db_path_str}",
        connect_args={"check_same_thread": False},
    )


@lru_cache(maxsize=32)
def _cached_readonly_engine(db_path_str: str) -> Engine:
    """Read-only engine using SQLite's `mode=ro` URI — defense in depth
    beyond `execute_query`'s statement validation (TRD §5, point 3).

    The path is percent-encoded because it is embedded in a URI and may
    contain spaces or other reserved characters.
    """
    encoded = quote(Path(db_path_str).as_posix(), safe="/:")
    return create_engine(
        f"sqlite:///file:{encoded}?mode=ro&uri=true",
        connect_args={"check_same_thread": False},
    )


def get_engine(db_path: Path) -> Engine:
    return _cached_engine(str(db_path.resolve()))


def get_readonly_engine(db_path: Path) -> Engine:
    return _cached_readonly_engine(str(db_path.resolve()))
