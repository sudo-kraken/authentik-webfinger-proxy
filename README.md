# Authentik WebFinger Proxy

This is a minimal Flask application that implements a WebFinger endpoint for Tailscale SSO to integrate with an Authentik instance. It listens on port 8000 and responds to GET requests at `/.well-known/webfinger`, returning JSON data based on the provided query parameter.

## Features

- **Dynamic Issuer URL:** Uses the `DOMAIN` environment variable to build the issuer URL.
- **Dynamic Application:** Uses the `APPLICATION` environment variable to specify the application name in Authentik.
- **WebFinger Endpoint:** Responds to WebFinger queries for resources starting with `acct:`.
- **WSGI Compatible:** Runs with Gunicorn for production-ready deployments.
- **Containerised:** Easily deployable with Docker.

## Requirements
- Python 3.13 with [uv](https://docs.astral.sh/uv/)
- Docker optional

## Quick start with uv
```bash
uv sync --all-extras
export DOMAIN=auth.example-domain.com
uv run flask --app app:app run --host 0.0.0.0 --port ${PORT:-8000}
# or Gunicorn
uv run --no-dev gunicorn -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-8000} app:app
```

## Docker
```bash
docker run --rm -e DOMAIN=auth.example-domain.com -p 8000:8000 ghcr.io/sudo-kraken/authentik-webfinger-proxy:latest

# For compose use see the repo example
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PORT | no | 8000 | Port to bind |
| WEB_CONCURRENCY | no | 2 | Gunicorn workers |
| DOMAIN | yes |  | Domain of your Authentik issuer host |
| APPLICATION | no | tailscale | Authentik application slug |
| CACHE_TTL | no | 300 | Cache IDP endpoints seconds |
| REQUEST_TIMEOUT | no | 10 | HTTP timeout seconds |

## Health and readiness
- `GET /health` returns `{ "ok": true }`.

## Endpoint
- `GET /.well-known/webfinger?resource=acct:user@example.com`

## Project layout
```
authentik-webfinger-proxy/
  app/
  Dockerfile
  pyproject.toml
  tests/
```

## Development
```bash
uv run ruff check --fix .
uv run ruff format .
uv run pytest --cov
```

## Licence
See [LICENSE](LICENSE)

## Security
See [SECURITY.md](SECURITY.md)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## Support
Open an [issue](/../../issues)
