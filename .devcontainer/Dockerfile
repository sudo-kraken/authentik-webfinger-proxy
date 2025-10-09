FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_INSTALL_DIR=/usr/local/bin

ARG UV_VERSION=0.9.1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git jq \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh
