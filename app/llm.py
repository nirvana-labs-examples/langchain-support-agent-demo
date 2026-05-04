"""
LLM provider factory.

Returns a LangChain `BaseChatModel` for the configured backend so the rest of
the answer chain stays provider-agnostic.

Supported providers (chosen via `LLM_PROVIDER` env var):
  - "ollama" (default) — local LLM served by Ollama on the same VM
  - "openai"           — hosted, requires OPENAI_API_KEY
"""

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    if settings.llm_provider == "ollama":
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set. Set it in .env or switch LLM_PROVIDER back to 'ollama'.")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=SecretStr(settings.openai_api_key),
            temperature=0,
        )
    raise RuntimeError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")


def llm_label() -> str:
    """Human-readable label for the active provider+model, used in responses."""
    if settings.llm_provider == "ollama":
        return f"ollama:{settings.ollama_model}"
    return f"openai:{settings.openai_model}"
