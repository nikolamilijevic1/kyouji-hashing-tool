# Stage 1: Builder
FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/backend/pyproject.toml ./src/backend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package backend

# Stage 2: Tester
FROM builder AS tester
COPY tests/ ./tests
COPY src/backend/*.py ./src/backend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run pytest tests/

# Stage 3: Runner
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/backend/*.py /app/backend/
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
