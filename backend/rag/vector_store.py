import json
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.rag.embeddings import EmbeddingProvider
from backend.rag.models import DocumentChunkModel


class DBVectorStore:
    """
    Database-backed vector store that integrates with SQLAlchemy.
    Compatible with both SQLite (tests/local) and PostgreSQL (production).
    """

    def __init__(
        self, session: AsyncSession, embedding_provider: EmbeddingProvider
    ) -> None:
        self.session = session
        self.embedding_provider = embedding_provider

    async def add_document_chunk(
        self, title: str, content: str, metadata: dict[str, Any] | None = None
    ) -> DocumentChunkModel:
        """
        Generates embedding for a text chunk and saves it to the database.
        """
        embedding_vector = self.embedding_provider.get_embedding(content)

        # Serialize list of floats to JSON string for database storage
        embedding_str = json.dumps(embedding_vector)

        chunk = DocumentChunkModel(
            title=title,
            content=content,
            embedding=embedding_str,
            metadata_json=metadata or {},
        )

        self.session.add(chunk)
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk

    async def similarity_search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """
        Performs semantic search by computing cosine similarity.
        """
        query_vector = np.array(self.embedding_provider.get_embedding(query))

        # Retrieve all chunks from database
        result = await self.session.execute(select(DocumentChunkModel))
        chunks = result.scalars().all()

        if not chunks:
            return []

        scored_chunks = []
        for chunk in chunks:
            # Deserialize embedding from database
            try:
                embedding_data = str(chunk.embedding)
                chunk_vector = np.array(json.loads(embedding_data))
            except (TypeError, json.JSONDecodeError):
                continue

            # Compute cosine similarity: (A . B) / (||A|| * ||B||)
            dot_product = np.dot(query_vector, chunk_vector)
            norm_q = np.linalg.norm(query_vector)
            norm_c = np.linalg.norm(chunk_vector)

            if norm_q > 0 and norm_c > 0:
                similarity = float(dot_product / (norm_q * norm_c))
            else:
                similarity = 0.0

            scored_chunks.append((similarity, chunk))

        # Sort by similarity score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_k = scored_chunks[:k]

        # Format results as dictionary records
        results: list[dict[str, Any]] = []
        for score, chunk in top_k:
            results.append(
                {
                    "id": chunk.id,
                    "title": chunk.title,
                    "content": chunk.content,
                    "score": score,
                    "category": chunk.metadata_json.get("category", "General")
                    if chunk.metadata_json
                    else "General",
                    "metadata": chunk.metadata_json or {},
                }
            )

        return results
