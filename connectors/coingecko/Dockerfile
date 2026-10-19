# Build from the repository root:
#   docker build -f connectors/coingecko/Dockerfile -t connector-coingecko .
FROM ghcr.io/astral-sh/uv:0.11.19 AS uv

FROM python:3.13-slim AS builder
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY connectors ./connectors
RUN uv sync --frozen --no-dev --no-editable --package connector-coingecko

FROM python:3.13-slim
RUN useradd --create-home --uid 1000 app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
USER app
ENTRYPOINT ["connector-coingecko"]
