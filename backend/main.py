import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.api import api_router
from backend.core.config import settings
from backend.core.logging_config import setup_logging

# Configure structured JSON log outputs
setup_logging()
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown hook logic.
    """
    logger.info("Application starting up...")
    
    # Auto-create database tables
    try:
        from backend.core.database import engine, Base
        from backend.rag.models import DocumentChunkModel
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}", exc_info=True)
        
    # Auto-seed document chunks if database is empty
    try:
        from backend.core.database import AsyncSessionLocal
        from sqlalchemy.future import select
        from backend.rag.models import DocumentChunkModel
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DocumentChunkModel))
            exists = result.scalars().first() is not None
            if not exists:
                logger.info("Database vector store is empty. Auto-seeding knowledge base...")
                import sys
                import os
                import re
                sys.path.append(os.path.abspath("."))
                from scripts.seed_knowledge_base import SEED_DOCUMENTS
                from backend.rag.embeddings import DualModeEmbeddingProvider
                from backend.rag.vector_store import DBVectorStore
                
                embedding_provider = DualModeEmbeddingProvider(dimension=768)
                vector_store = DBVectorStore(session=session, embedding_provider=embedding_provider)
                
                for filename, text in SEED_DOCUMENTS.items():
                    title_match = re.search(r"Title:\s*(.*)", text)
                    cat_match = re.search(r"Category:\s*(.*)", text)
                    
                    title = title_match.group(1).strip() if title_match else filename
                    category = cat_match.group(1).strip() if cat_match else "General"
                    
                    # Clean headers from document content
                    content_lines = []
                    for line in text.split("\n"):
                        if not any(line.startswith(h) for h in ["Title:", "Author:", "Category:", "Status:"]):
                            content_lines.append(line)
                    content = "\n".join(content_lines).strip()
                    
                    await vector_store.add_document_chunk(
                        title=title,
                        content=content,
                        metadata={"category": category, "source": filename}
                    )
                logger.info("Knowledge base database seeding complete.")
    except Exception as e:
        logger.error(f"Failed to auto-seed database knowledge base: {e}", exc_info=True)
        
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url="/redoc" if settings.ENV == "development" else None,
    openapi_url=(
        f"{settings.API_V1_STR}/openapi.json" if settings.ENV == "development" else None
    ),
)

# CORS Setup
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def log_requests_middleware(
    request: Request, call_next: Callable[[Request], Any]
) -> Response:
    """
    Middleware that tracks request lifecycles, measuring execution times
    and printing logs in structured format.
    """
    start_time = time.perf_counter()
    logger.info(f"Start request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info(
            f"Success request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {process_time:.4f}s",
            extra={
                "extra_attrs": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration": process_time,
                }
            },
        )
        return response
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error(
            f"Failure request: {request.method} {request.url.path} - "
            f"Error: {str(e)} - Duration: {process_time:.4f}s",
            exc_info=True,
            extra={
                "extra_attrs": {
                    "method": request.method,
                    "path": request.url.path,
                    "duration": process_time,
                }
            },
        )
        raise


app.include_router(api_router, prefix=settings.API_V1_STR)
