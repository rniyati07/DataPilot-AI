"""A scripted chat model for agent tests.

Lets the suite drive exact tool-call sequences deterministically, so agent
behavior is testable without contacting a real LLM provider (TRD §11).
"""
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedChatModel(BaseChatModel):
    """Replays a fixed list of AIMessages, one per model turn."""

    responses: list[AIMessage] = []
    calls: int = 0
    bound_tools: list[str] = []

    @property
    def _llm_type(self) -> str:
        return "scripted-test-model"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedChatModel":
        self.bound_tools = [getattr(tool, "name", str(tool)) for tool in tools]
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.calls >= len(self.responses):
            raise AssertionError(
                f"ScriptedChatModel ran out of scripted responses after {self.calls} calls"
            )
        message = self.responses[self.calls]
        self.calls += 1
        return ChatResult(generations=[ChatGeneration(message=message)])


class FailingChatModel(BaseChatModel):
    """Raises on invocation, simulating a provider outage/rate limit."""

    @property
    def _llm_type(self) -> str:
        return "failing-test-model"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "FailingChatModel":
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise RuntimeError("simulated provider outage")


def tool_call(name: str, args: dict[str, Any], call_id: str = "call-1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def final_answer(text: str) -> AIMessage:
    return AIMessage(content=text)
