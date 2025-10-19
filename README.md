<div align="center">
<img src="https://raw.githubusercontent.com/sudo-kraken/authentik-webfinger-proxy/main/docs/assets/logo.png" align="center" width="144px" height="144px"/>

### Authentik Webfinger Proxy

_A minimal Flask service that implements `/.well-known/webfinger` to help Tailscale discover your Authentik OpenID Connect provider. Built with uv and designed for local or containerised runs._

</div>

<div align="center">

[![Docker](https://img.shields.io/github/v/tag/sudo-kraken/authentik-webfinger-proxy?label=docker&logo=docker&style=for-the-badge)](https://github.com/sudo-kraken/authentik-webfinger-proxy/pkgs/container/authentik-webfinger-proxy) [![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fsudo-kraken%2Fauthentik-webfinger-proxy%2Fmain%2Fpyproject.toml&logo=python&logoColor=yellow&color=3776AB&style=for-the-badge)](https://github.com/sudo-kraken/authentik-webfinger-proxy/blob/main/pyproject.toml)
</div>

<div align="center">

[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/sudo-kraken/authentik-webfinger-proxy?label=openssf%20scorecard&style=for-the-badge)](https://scorecard.dev/viewer/?uri=github.com/sudo-kraken/authentik-webfinger-proxy)

</div>

## Overview

The service responds to WebFinger queries by constructing an issuer URL from your `DOMAIN` and proxying relevant metadata. It exposes a health endpoint for orchestration systems and runs under Flask or Gunicorn.

## Architecture at a glance

- Flask app factory with `app:app` WSGI target
- WebFinger endpoint at `/.well-known/webfinger`
- Health endpoint `GET /health`

## Features

- WebFinger responder at `/.well-known/webfinger`
- Issuer URL built dynamically from `DOMAIN`
- Optional `APPLICATION` slug support for Authentik
- Response caching with `CACHE_TTL`
- Configurable upstream timeouts
- `/health` endpoint for liveness checks
- Prebuilt container image on GHCR

## Prerequisites

- [Docker](https://www.docker.com/)
- (Alternatively) [uv](https://docs.astral.sh/uv/) and Python 3.13 for local development

## Quick start

Local development with uv

```bash
uv sync --all-extras
export DOMAIN=auth.example-domain.com
uv run flask --app app:app run --host 0.0.0.0 --port ${PORT:-8000}
```

## Docker

Pull and run

```bash
docker pull ghcr.io/sudo-kraken/authentik-webfinger-proxy:latest
docker run --rm -p 8000:8000 \
  -e DOMAIN=auth.example-domain.com \
  ghcr.io/sudo-kraken/authentik-webfinger-proxy:latest
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PORT | no | 8000 | Port to bind |
| WEB_CONCURRENCY | no | 2 | Gunicorn worker processes |
| DOMAIN | yes |  | Domain of your Authentik issuer host |
| APPLICATION | no | tailscale | Authentik application slug |
| CACHE_TTL | no | 300 | Cache IDP endpoints seconds |
| REQUEST_TIMEOUT | no | 10 | HTTP timeout seconds for outbound calls |

`.env` example

```dotenv
PORT=8000
WEB_CONCURRENCY=2
DOMAIN=auth.example-domain.com
APPLICATION=tailscale
CACHE_TTL=300
REQUEST_TIMEOUT=10
```

## Health

- `GET /health` returns `{ "ok": true }`

## Endpoint

- `GET /.well-known/webfinger?resource=acct:user@example.com`

Example

```bash
curl "http://localhost:8000/.well-known/webfinger?resource=acct:user@example.com"
```

## Production notes

- Expose the service on the network domain referenced by `DOMAIN`. Your reverse proxy should terminate TLS.
- Keep `REQUEST_TIMEOUT` conservative and cache metadata with `CACHE_TTL` to reduce upstream calls.

## Development

```bash
uv run ruff check --fix .
uv run ruff format .
uv run pytest --cov
```

## Troubleshooting

- If the issuer cannot be resolved, check `DOMAIN` and ensure the upstream IDP endpoints are reachable from the container.
- If you receive 404 responses, confirm the `resource` query is present and correctly formatted.

## Licence
See [LICENSE](LICENSE)

## Security
See [SECURITY.md](SECURITY.md)

## Contributing
Feel free to open issues or submit pull requests if you have suggestions or improvements.
See [CONTRIBUTING.md](CONTRIBUTING.md)

## Support
Open an [issue](/../../issues)
