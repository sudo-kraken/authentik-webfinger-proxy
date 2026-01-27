FROM ghcr.io/astral-sh/uv:0.9-python3.13-bookworm-slim@sha256:fb12b20e86027dac1b4c78a359ba091b639df39b85d9e9f5d93a91bd08e01666

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
 
RUN adduser --disabled-password --gecos "" --home /nonroot --uid 10001 appuser

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:8000/health" || exit 1
  
CMD ["uv", "run", "--no-dev", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app.app:app"]
