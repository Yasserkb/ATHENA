# syntax=docker/dockerfile:1.7
# check=error=true

ARG PYTHON_VERSION=3.12.13
ARG PYTHON_IMAGE_DIGEST=sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

FROM python:${PYTHON_VERSION}-slim-trixie@${PYTHON_IMAGE_DIGEST} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml README.md MANIFEST.in constraints-production.txt ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade \
        "pip==26.2" "setuptools==83.0.0" "wheel==0.47.0" \
    && python -m pip install --constraint constraints-production.txt ".[mcp,tokenizers]" \
    && python -m pip check


FROM python:${PYTHON_VERSION}-slim-trixie@${PYTHON_IMAGE_DIGEST} AS runtime

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=0.1.0
ARG SOURCE_URL="https://github.com/OWNER/athena-codegraph"

LABEL org.opencontainers.image.title="Athena CodeGraph" \
      org.opencontainers.image.description="Local-first repository context and code graph MCP server" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ATHENA_ROOT=/workspace \
    ATHENA_STATE_DIR=/data \
    HOME=/data/home \
    XDG_CACHE_HOME=/data/cache

RUN apt-get update \
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends ca-certificates git tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 athena \
    && mkdir -p /workspace /data/home /data/cache \
    && useradd --uid 10001 --gid 10001 --no-log-init --no-create-home \
        --home-dir /data/home --shell /usr/sbin/nologin athena \
    && chown -R 10001:10001 /data /workspace

COPY --from=builder /opt/venv /opt/venv
COPY docker/healthcheck.py /opt/athena/healthcheck.py

WORKDIR /workspace
USER 10001:10001

VOLUME ["/data"]
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "/opt/athena/healthcheck.py"]

ENTRYPOINT ["/usr/bin/tini", "--", "athena"]
CMD ["mcp", "--root", "/workspace", "--mode", "economy", "--daemon"]
