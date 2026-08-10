"""Phase 12 — bounded self-correction (Architecture §6, FR-10).

Caps `execute_query` automatic retries at exactly one per turn. The budget is
tracked in code via a ContextVar (the same mechanism `session`/`trace` use),
never by prompt instruction alone — a stray LLM behavior cannot turn this into
an unbounded loop.

Only database-level `sql_error` failures are retryable. Write-request
rejections (`validation_rejected`) and connection failures
(`database_unavailable`) are never retried: retrying them would either
attempt to modify data or be pointless.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

MAX_EXECUTE_QUERY_RETRIES = 1

# Error types the agent is allowed to self-correct by revising the SQL.
RETRYABLE_ERROR_TYPES = ("sql_error",)


class ExecuteRetryBudget:
    def __init__(self, max_retries: int = MAX_EXECUTE_QUERY_RETRIES) -> None:
        self.max_retries = max_retries
        self.retries = 0

    def use(self) -> bool:
        """Records one attempted correction. Returns True when the budget is
        now exhausted and no further retry may be made."""
        self.retries += 1
        return self.retries > self.max_retries

    @property
    def exhausted(self) -> bool:
        return self.retries > self.max_retries


_current_budget: ContextVar[Optional[ExecuteRetryBudget]] = ContextVar(
    "execute_retry_budget", default=None
)


@contextmanager
def retry_budget_scope() -> Iterator[ExecuteRetryBudget]:
    """Fresh, per-invocation budget. Concurrent requests never share it."""
    budget = ExecuteRetryBudget()
    token = _current_budget.set(budget)
    try:
        yield budget
    finally:
        _current_budget.reset(token)


def current_budget() -> Optional[ExecuteRetryBudget]:
    return _current_budget.get()
