# Stage 1: Install dependencies with uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
