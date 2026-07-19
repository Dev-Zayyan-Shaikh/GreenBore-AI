from sqlalchemy import JSON, Column, Integer, String, Text

from backend.core.database import Base


class DocumentChunkModel(Base):
    """
    SQLAlchemy model representing a chunked document segment, its vector embedding,
    and associated metadata. Highly portable across SQLite and PostgreSQL.
    """

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    # Stored as a JSON-serialized string of floats (e.g. '[0.12, -0.43, ...]')
    # This guarantees out-of-the-box compatibility with SQLite for tests
    # and standard PostgreSQL tables.
    embedding = Column(Text, nullable=False)
    # Stores structural metadata: author, category, chunk_index, source
    metadata_json = Column(JSON, nullable=True)
