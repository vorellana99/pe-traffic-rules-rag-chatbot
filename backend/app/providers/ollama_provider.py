"""Implementación de los providers vía `langchain-ollama` (100% local)."""
from collections.abc import AsyncIterator

from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.providers.base import EmbeddingProvider, LLMProvider


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, base_url: str, model: str, dimension: int) -> None:
        self._dimension = dimension
        self._client = OllamaEmbeddings(base_url=base_url, model=model)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._client.aembed_documents(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self._client.aembed_query(text)


class OllamaLLMProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, temperature: float = 0.0) -> None:
        self._client = ChatOllama(
            base_url=base_url, model=model, temperature=temperature
        )

    @staticmethod
    def _build_messages(prompt: str, system: str | None) -> list[tuple[str, str]]:
        messages: list[tuple[str, str]] = []
        if system:
            messages.append(("system", system))
        messages.append(("human", prompt))
        return messages

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        result = await self._client.ainvoke(self._build_messages(prompt, system))
        return result.content

    async def stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        async for chunk in self._client.astream(self._build_messages(prompt, system)):
            if chunk.content:
                yield chunk.content
