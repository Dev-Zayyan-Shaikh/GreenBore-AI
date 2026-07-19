import logging
from typing import Any, Protocol, cast

import httpx
from sklearn.feature_extraction.text import (
    HashingVectorizer,  # type: ignore[import-untyped]
)

from backend.core.config import settings

logger = logging.getLogger("greenbore.rag.embeddings")


class EmbeddingProvider(Protocol):
    """
    Interface for text embedding generation.
    """

    def get_embedding(self, text: str) -> list[float]: ...

    def get_embeddings(self, texts: list[str]) -> list[list[float]]: ...


class LocalEmbeddingProvider:
    """
    Offline embedding generator using scikit-learn's HashingVectorizer.
    Generates a deterministic 768-dimensional dense vector.
    """

    def __init__(self, dimension: int = 768) -> None:
        self.dimension = dimension
        # Alternate sign set to False to keep values positive/comparable
        self.vectorizer = HashingVectorizer(
            n_features=dimension, norm="l2", alternate_sign=False
        )

    def get_embedding(self, text: str) -> list[float]:
        sparse_vec = self.vectorizer.transform([text])
        return cast(Any, sparse_vec).toarray()[0].tolist()

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        sparse_vecs = self.vectorizer.transform(texts)
        return cast(Any, sparse_vecs).toarray().tolist()


class GeminiEmbeddingProvider:
    """
    Remote embedding generator using Google Generative AI text-embedding-004 API.
    """

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"

    def get_embedding(self, text: str) -> list[float]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }
        params = {"key": self.api_key}

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                self.url, json=payload, headers=headers, params=params
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]["values"]

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self.get_embedding(t) for t in texts]


class DualModeEmbeddingProvider:
    """
    Tries GeminiEmbeddingProvider if API key is present.
    If the API call fails or the key is absent, falls back to LocalEmbeddingProvider.
    """

    def __init__(self, api_key: str | None = None, dimension: int = 768) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.dimension = dimension
        self.local_provider = LocalEmbeddingProvider(dimension=dimension)

        if self.api_key and self.api_key.strip():
            logger.info("Initializing Gemini embedding provider (key present).")
            self.gemini_provider: GeminiEmbeddingProvider | None = GeminiEmbeddingProvider(api_key=self.api_key)
        else:
            logger.info(
                "No Gemini API key found. Falling back to local offline embeddings."
            )
            self.gemini_provider = None

    def get_embedding(self, text: str) -> list[float]:
        if self.gemini_provider:
            try:
                return self.gemini_provider.get_embedding(text)
            except Exception as e:
                logger.warning(
                    f"Gemini embedding API call failed: {e}. Falling back to local offline provider."
                )
        return self.local_provider.get_embedding(text)

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if self.gemini_provider:
            try:
                return self.gemini_provider.get_embeddings(texts)
            except Exception as e:
                logger.warning(
                    f"Gemini embeddings batch API call failed: {e}. Falling back to local offline provider."
                )
        return self.local_provider.get_embeddings(texts)
