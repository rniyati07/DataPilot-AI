"""Provider-agnostic chat-model factory (TRD §4, Architecture §13).

The agent and tools depend only on LangChain's `BaseChatModel` interface —
never on a specific provider's SDK types — so swapping providers is an
environment change, not a code change.

Instantiation is lazy: the backend must still boot and serve
`/api/database/*` and `/api/health` with no LLM API key configured.
"""
import logging
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)

# Sensible per-provider defaults, overridable via LLM_MODEL.
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5",
    "gemini": "gemini-2.0-flash",
}

SUPPORTED_PROVIDERS = tuple(DEFAULT_MODELS)


class LlmConfigurationError(Exception):
    """The LLM provider is missing, misconfigured, or its package is absent.

    Carries a user-safe message — never a raw key or stack trace.
    """


def _resolve_model_name(provider: str) -> str:
    return settings.llm_model.strip() or DEFAULT_MODELS[provider]


def get_chat_model() -> "BaseChatModel":
    """Builds the configured chat model, or raises LlmConfigurationError.

    Callers are expected to catch LlmConfigurationError and convert it into
    a structured response envelope rather than letting it reach the client.
    """
    provider = (settings.llm_provider or "").strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise LlmConfigurationError(
            f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. "
            f"Supported values: {', '.join(SUPPORTED_PROVIDERS)}."
        )

    api_key = settings.llm_api_key.strip()
    if not api_key:
        raise LlmConfigurationError(
            "No LLM API key is configured. Set LLM_API_KEY in your .env file "
            "to enable the AI analyst."
        )

    model_name = _resolve_model_name(provider)

    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=model_name, api_key=api_key, temperature=0)

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(model=model_name, api_key=api_key, temperature=0)

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0)

    except ImportError as exc:
        logger.exception("LLM provider package missing for %s", provider)
        raise LlmConfigurationError(
            f"The '{provider}' provider package is not installed on the server."
        ) from exc
    except LlmConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001 - never surface provider internals
        logger.exception("Could not initialize LLM provider %s", provider)
        raise LlmConfigurationError(
            f"Could not initialize the '{provider}' language model."
        ) from exc
