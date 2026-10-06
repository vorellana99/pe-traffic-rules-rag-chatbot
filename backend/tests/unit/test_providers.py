"""Tests unitarios de los providers (con mocks, sin Ollama real)."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.providers import factory
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.ollama_provider import (
    OllamaEmbeddingProvider,
    OllamaLLMProvider,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ollama_base_url="http://ollama:11434",
        embedding_model="bge-m3",
        embedding_dim=1024,
        llm_model="qwen2.5:7b",
    )


# ---------------------------- EmbeddingProvider ----------------------------

def test_dimension_from_config(settings: Settings) -> None:
    provider = OllamaEmbeddingProvider("http://x", "bge-m3", settings.embedding_dim)
    assert provider.dimension == 1024


async def test_embed_texts_calls_client(settings: Settings) -> None:
    provider = OllamaEmbeddingProvider("http://x", "bge-m3", 1024)
    provider._client = MagicMock()
    provider._client.aembed_documents = AsyncMock(
        return_value=[[0.1, 0.2], [0.3, 0.4]]
    )

    result = await provider.embed_texts(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    provider._client.aembed_documents.assert_awaited_once_with(["a", "b"])


async def test_embed_query_calls_client(settings: Settings) -> None:
    provider = OllamaEmbeddingProvider("http://x", "bge-m3", 1024)
    provider._client = MagicMock()
    provider._client.aembed_query = AsyncMock(return_value=[0.5, 0.6])

    result = await provider.embed_query("hola")

    assert result == [0.5, 0.6]
    provider._client.aembed_query.assert_awaited_once_with("hola")


# ------------------------------- LLMProvider -------------------------------

async def test_generate_returns_content() -> None:
    provider = OllamaLLMProvider("http://x", "qwen2.5:7b")
    provider._client = MagicMock()
    provider._client.ainvoke = AsyncMock(
        return_value=SimpleNamespace(content="respuesta")
    )

    out = await provider.generate("pregunta", system="eres un asistente")

    assert out == "respuesta"
    provider._client.ainvoke.assert_awaited_once()
    # El system prompt debe ir como primer mensaje.
    sent_messages = provider._client.ainvoke.call_args.args[0]
    assert sent_messages[0] == ("system", "eres un asistente")
    assert sent_messages[-1] == ("human", "pregunta")


async def test_stream_yields_chunks() -> None:
    provider = OllamaLLMProvider("http://x", "qwen2.5:7b")

    async def fake_astream(_messages):
        for text in ["Hola", " ", "mundo", ""]:
            yield SimpleNamespace(content=text)

    provider._client = MagicMock()
    provider._client.astream = fake_astream

    chunks = [chunk async for chunk in provider.stream("hola")]

    # Los fragmentos vacíos se filtran.
    assert chunks == ["Hola", " ", "mundo"]


# --------------------------------- Factory ---------------------------------

def test_factory_builds_embedding_provider(settings: Settings) -> None:
    provider = factory.build_embedding_provider(settings)
    assert isinstance(provider, EmbeddingProvider)
    assert provider.dimension == settings.embedding_dim


def test_factory_builds_llm_provider(settings: Settings) -> None:
    provider = factory.build_llm_provider(settings)
    assert isinstance(provider, LLMProvider)
