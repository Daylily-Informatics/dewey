# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.12

FROM ghcr.io/astral-sh/uv:0.5.30-python${PYTHON_VERSION}-bookworm-slim AS builder

ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION} \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY config ./config
COPY dewey_service ./dewey_service
RUN uv sync --frozen --no-dev

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system lsmc && adduser --system --ingroup lsmc --home /app lsmc
WORKDIR /app
COPY --from=builder --chown=lsmc:lsmc /app /app
COPY --chown=lsmc:lsmc docker/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh
USER lsmc

EXPOSE 8914
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "dewey_service.container_entry"]
