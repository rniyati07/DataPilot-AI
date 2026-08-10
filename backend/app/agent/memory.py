"""Bounded, session-scoped conversation memory (Implementation Plan Phase 7,
Architecture §7, FR-8).

Each session keeps a sliding window of recent user/assistant text turns so
follow-up questions ("now show their trend", "which one grew fastest?")
resolve pronouns and entity references against what was just asked. The
window is deliberately bounded (TRD §13) — older turns are dropped rather
than retained verbatim, so prompts stay within context limits on longer
sessions.

The most recent result set itself lives in the Session Store (Phase 7's
second responsibility); this module is only the conversation-turn memory.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_MAX_TURNS = 6


class ConversationMemory:
    """A bounded list of the session's most recent text turns.

    Each turn contributes one user message and one assistant message. The
    window is capped at `max_turns` complete turns; the oldest turns are
    dropped first.
    """

    def __init__(self, max_turns: int = DEFAULT_MAX_TURNS) -> None:
        self.max_turns = max_turns
        self._turns: list[dict[str, str]] = []  # {"role": "user"|"assistant", "content": str}

    def add_user(self, message: str) -> None:
        self._turns.append({"role": "user", "content": message})
        self._trim()

    def add_assistant(self, text: str) -> None:
        self._turns.append({"role": "assistant", "content": text})
        self._trim()

    def to_messages(self) -> list[dict[str, str]]:
        """Messages ready to prepend to the agent's input messages."""
        return list(self._turns)

    def clear(self) -> None:
        self._turns = []

    def _trim(self) -> None:
        max_messages = self.max_turns * 2
        if len(self._turns) > max_messages:
            self._turns = self._turns[-max_messages:]

    @property
    def turn_count(self) -> int:
        return (len(self._turns) + 1) // 2

    @property
    def message_count(self) -> int:
        return len(self._turns)
