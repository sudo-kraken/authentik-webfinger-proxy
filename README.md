# Authentik WebFinger Proxy

This is a minimal Flask application that implements a WebFinger endpoint for Tailscale SSO to integrate with an Authentik instance. It listens on port 8000 and responds to GET requests at `/.well-known/webfinger`, returning JSON data based on the provided query parameter.

## Features

- **Dynamic Issuer URL:** Uses the `DOMAIN` environment variable to build the issuer URL.
- **Dynamic Application:** Uses the `APPLICATION` environment variable to specify the application name in Authentik.
- **WebFinger Endpoint:** Responds to WebFinger queries for resources starting with `acct:`.
- **WSGI Compatible:** Runs with Gunicorn for production-ready deployments.
- **Containerised:** Easily deployable with Docker.

## File Structure

```
authentik-webfinger-proxy/
├──Dockerfile
├──app/
  ├──requirements.txt
  ├──app.py
```

## Prerequisites

- [Docker](https://www.docker.com/)
- (Alternatively) Python 3.10 for local development

## Setup and Installation

### Using Docker

1. **Set DOMAIN Environment Variable:**

  The application uses the `DOMAIN` environment variable to configure the issuer URL. For example, if you want your issuer URL to be `https://auth.example-domain.com/application/o/tailscale/`, set:

  ```bash
export DOMAIN=auth.example-domain.com
```

1. **(Optional) Set APPLICATION Environment Variable:**

  The application uses the `APPLICATION` environment variable to configure the application (slug) from Authentik. For example, if you want your application to be `tailscaleapp`, set:

  ```bash
export APPLICATION=tailscaleapp
```

By default, we use `tailscale` as the application name.

2. **Build the Docker Image:**

  Run the following command from the project root:

  ```bash
docker build -t authentik-webfinger-proxy .
```

3. **Run the Docker Container:**

  Run the container while exposing port 8000 and passing the environment variable:

  ```bash
docker run -d -p 8000:8000 -e DOMAIN=auth.example-domain.com authentik-webfinger-proxy
```

## Using Local Development

1. **Create a Virtual Environment:**

  ```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install Dependencies:**

  ```bash
pip install -r requirements.txt
```

3. **Set the Environment Variable:**

  ```bash
export DOMAIN=auth.example-domain.com
```

4. **Run the Application:**

  ```bash
python app/app.py
```

## Endpoint Usage

The application listens on the following endpoint:

```
GET /.well-known/webfinger
```

## Example Request

To query the service, you can run:

```bash
curl "http://localhost:8000/.well-known/webfinger?resource=acct:user@example.com"
```

## Running with Gunicorn

The Dockerfile is configured to run the app using Gunicorn with 4 workers:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

This provides a robust WSGI server suitable for production environments.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions or improvements.
