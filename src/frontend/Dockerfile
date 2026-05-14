# Stage 1: Builder
FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/frontend/pyproject.toml ./src/frontend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package frontend

# Stage 2: Runner
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/frontend/ /app/frontend/
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8501
RUN mkdir -p /app/frontend/static
# Point Streamlit at the config.toml we ship inside the image
ENV STREAMLIT_HOME=/app/frontend
CMD ["streamlit", "run", "frontend/app.py", \
     "--server.port", "8501", \
     "--server.address", "0.0.0.0", \
     "--server.maxUploadSize", "15000", \
     "--server.maxMessageSize", "200", \
     "--server.enableStaticServing", "true"]
