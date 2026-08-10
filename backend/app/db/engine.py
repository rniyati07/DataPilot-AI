"""Engine factory: builds a SQLAlchemy engine for an arbitrary resolved
database path — no longer a single global engine tied to DATABASE_URL
(Phase 3 requirement, so a session's upload can become the active engine).

Engines are cached per resolved path. The cache is a bounded dict registry
rather than functools.lru_cache so a specific path's engines can be evicted
and disposed on demand: an uploaded database's pooled connection keeps the
file open, which on Windows blocks unlink() during cleanup and leaves orphan
files behind in the upload directory.
"""
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from sqlalchemy import Engine, create_engine

MAX_CACHED_ENGINES = 32


def _make_engine(db_path_str: str) -> Engine:
    return create_engine(
        f"sqlite:///{db_path_str}",
        connect_args={"check_same_thread": False},
    )


def _make_readonly_engine(db_path_str: str) -> Engine:
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


class _EngineRegistry:
    """Bounded per-path engine cache with explicit per-path disposal."""

    def __init__(self, factory: Callable[[str], Engine], max_size: int) -> None:
        self._factory = factory
        self._max_size = max_size
        self._engines: OrderedDict[str, Engine] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, path_str: str) -> Engine:
        with self._lock:
            engine = self._engines.get(path_str)
            if engine is None:
                engine = self._factory(path_str)
                self._engines[path_str] = engine
                while len(self._engines) > self._max_size:
                    _, oldest = self._engines.popitem(last=False)
                    oldest.dispose()
            else:
                self._engines.move_to_end(path_str)
            return engine

    def dispose(self, path_str: str) -> None:
        """Evict and dispose the engine for `path_str`, closing its pooled
        connections (and, on Windows, releasing the file handle they hold)."""
        with self._lock:
            engine = self._engines.pop(path_str, None)
        if engine is not None:
            engine.dispose()


_engines = _EngineRegistry(_make_engine, MAX_CACHED_ENGINES)
_readonly_engines = _EngineRegistry(_make_readonly_engine, MAX_CACHED_ENGINES)


def get_engine(db_path: Path) -> Engine:
    return _engines.get(str(db_path.resolve()))


def get_readonly_engine(db_path: Path) -> Engine:
    return _readonly_engines.get(str(db_path.resolve()))


def dispose_engine(db_path: Path) -> None:
    """Release and evict any cached engines for `db_path`.

    Call before removing a database file so SQLAlchemy's pooled connection
    does not keep the file locked on Windows. Safe when the path was never
    cached — that case is a no-op.
    """
    resolved = str(db_path.resolve())
    _engines.dispose(resolved)
    _readonly_engines.dispose(resolved)
