# Stage 1: Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./backend/
RUN pip install --no-cache-dir --user ./backend/

# Stage 2: Final runtime stage
FROM python:3.12-slim

WORKDIR /app

# Run as non-root user
RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser

# Copy packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

COPY backend/ ./backend/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENV ENV=production
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
