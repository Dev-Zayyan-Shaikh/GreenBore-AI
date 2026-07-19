import logging
import os
import re
from typing import Any

from backend.rag.vector_store import DBVectorStore

logger = logging.getLogger("greenbore.rag.ingester")


class DocumentIngester:
    """
    Ingests, parses, chunks, and indexes geological documents from files.
    """

    def __init__(
        self,
        vector_store: DBVectorStore,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> None:
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        """
        Splits a text string into overlapping chunks.
        """
        chunks: list[str] = []
        if not text:
            return chunks

        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)

            # Move start pointer forward by chunk size minus overlap
            start += self.chunk_size - self.chunk_overlap

            # Edge case to prevent infinite loops if sizing is incorrect
            if self.chunk_size <= self.chunk_overlap:
                break

        return chunks

    def parse_document(
        self, raw_content: str, filename: str
    ) -> tuple[dict[str, Any], str]:
        """
        Parses metadata header block from text files if present,
        and returns the metadata dictionary and cleaned text body.
        """
        metadata = {
            "source_file": filename,
            "category": "General",
            "author": "Unknown",
            "title": os.path.splitext(filename)[0].replace("_", " ").title(),
        }

        # Regex to match key-value headers at the top of the file
        header_lines = []
        lines = raw_content.split("\n")
        body_start_idx = 0

        for idx, line in enumerate(lines):
            # Check if line looks like a header (e.g. 'Title: ...')
            match = re.match(r"^([a-zA-Z0-9_\-]+):\s*(.*)$", line.strip())
            if match:
                key = match.group(1).lower()
                val = match.group(2).strip()
                if key in ["title", "author", "category", "status"]:
                    metadata[key] = val
                header_lines.append(line)
                body_start_idx = idx + 1
            elif not line.strip():
                # Allow empty lines in headers block
                continue
            else:
                # First line that is not a header marks the start of the body
                break

        body_content = "\n".join(lines[body_start_idx:]).strip()
        return metadata, body_content

    async def ingest_file(self, filepath: str) -> int:
        """
        Reads, parses, chunks, and indexes a single geological document file.
        """
        filename = os.path.basename(filepath)
        if not os.path.exists(filepath):
            logger.error(f"Ingestion file does not exist: {filepath}")
            return 0

        with open(filepath, encoding="utf-8") as f:
            raw_content = f.read()

        metadata, body_content = self.parse_document(raw_content, filename)
        chunks = self.chunk_text(body_content)

        logger.info(f"Ingesting {filename}: parsed into {len(chunks)} chunks.")

        for idx, chunk_text in enumerate(chunks):
            # Include chunk-specific indices in metadata
            chunk_metadata = {
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(chunks),
            }
            await self.vector_store.add_document_chunk(
                title=metadata["title"], content=chunk_text, metadata=chunk_metadata
            )

        return len(chunks)

    async def ingest_directory(self, directory_path: str) -> int:
        """
        Ingests all text and markdown documents inside a directory.
        """
        if not os.path.exists(directory_path):
            logger.error(f"Ingestion directory does not exist: {directory_path}")
            return 0

        files_ingested = 0
        total_chunks = 0

        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith((".txt", ".md")):
                    filepath = os.path.join(root, file)
                    try:
                        chunks_count = await self.ingest_file(filepath)
                        total_chunks += chunks_count
                        files_ingested += 1
                    except Exception as e:
                        logger.error(f"Failed to ingest file {file}: {e}")

        logger.info(
            f"Ingestion completed. {files_ingested} files ingested into {total_chunks} total chunks."
        )
        return total_chunks
