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
