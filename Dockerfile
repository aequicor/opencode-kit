# syntax=docker/dockerfile:1

FROM python:3.11-slim

LABEL org.opencontainers.image.title="opencode-kit"
LABEL org.opencontainers.image.description="Reusable OpenCode AI agent configuration kit"
LABEL org.opencontainers.image.source="https://github.com/aequicor/opencode-kit"

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV CI=true
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /kit

COPY pyproject.toml ./

RUN pip install --no-cache-dir -e .[dev]

COPY scripts/ scripts/
COPY kit/ kit/
COPY manifest.example.yaml profiles/ ./

RUN mkdir -p /workspace

VOLUME ["/workspace"]

ENTRYPOINT ["python", "-m", "scripts.apply"]
CMD ["--help"]
