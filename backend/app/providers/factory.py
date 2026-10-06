"""Factories que construyen los providers desde la configuración."""
from app.core.config import Settings, get_settings
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.ollama_provider import (
    OllamaEmbeddingProvider,
    OllamaLLMProvider,
)


def build_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.embedding_model,
        dimension=settings.embedding_dim,
    )


def build_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    return OllamaLLMProvider(
        base_url=settings.ollama_base_url,
        model=settings.llm_model,
    )
