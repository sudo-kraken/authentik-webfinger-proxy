import os
import re
import time

import requests
from flask import Flask, jsonify, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

# Configuration
DOMAIN = os.environ.get("DOMAIN", "idp.example.com")
APPLICATION = os.environ.get("APPLICATION", "tailscale")
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))  # 5 minutes default
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "10"))  # 10 seconds default


# Input validation
def validate_application_name(app_name):
    """Validate application name contains only safe characters"""
    if not re.match(r"^[a-zA-Z0-9_-]+$", app_name):
        raise ValueError(f"Invalid application name: {app_name}")
    return app_name


# Validate inputs
try:
    APPLICATION = validate_application_name(APPLICATION)
except ValueError as e:
    app.logger.error(f"Configuration error: {e}")
    raise

issuer_url = f"https://{DOMAIN}/application/o/{APPLICATION}/"

# Simple in-memory cache
_cache = {}
_cache_timestamp = 0

# Configure requests session with retries
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_idp_endpoints():
    """Fetch IDP endpoints with caching and error handling"""
    global _cache, _cache_timestamp

    current_time = time.time()

    # Check if cache is valid
    if _cache and (current_time - _cache_timestamp) < CACHE_TTL:
        app.logger.debug("Using cached IDP endpoints")
        return _cache

    try:
        app.logger.info(f"Fetching IDP endpoints from {issuer_url}")
        response = session.get(issuer_url, timeout=REQUEST_TIMEOUT, headers={"Accept": "application/json"})
        response.raise_for_status()

        idp_data = response.json()

        # Validate required endpoints exist
        required_endpoints = ["issuer", "authorization_endpoint", "token_endpoint", "userinfo_endpoint", "jwks_uri"]

        for endpoint in required_endpoints:
            if endpoint not in idp_data:
                raise ValueError(f"Missing required endpoint: {endpoint}")

        # Update cache
        _cache = idp_data
        _cache_timestamp = current_time
        app.logger.info("Successfully cached IDP endpoints")

        return idp_data

    except requests.exceptions.Timeout:
        app.logger.error(f"Timeout connecting to IDP at {issuer_url}")
        raise
    except requests.exceptions.ConnectionError:
        app.logger.error(f"Connection error to IDP at {issuer_url}")
        raise
    except requests.exceptions.HTTPError as e:
        app.logger.error(f"HTTP error from IDP: {e.response.status_code}")
        raise
    except ValueError as e:
        app.logger.error(f"Invalid response from IDP: {e}")
        raise
    except Exception as e:
        app.logger.error(f"Unexpected error fetching IDP endpoints: {e}")
        raise


@app.route("/.well-known/webfinger", methods=["GET"])
def webfinger():
    resource = request.args.get("resource")

    if not resource:
        app.logger.warning("WebFinger request missing resource parameter")
        return jsonify({"error": "Missing resource parameter"}), 400

    if not resource.startswith("acct:"):
        app.logger.warning(f"WebFinger request with invalid resource: {resource}")
        return jsonify({"error": "Resource must start with 'acct:'"}), 400

    try:
        # Get IDP endpoints (cached)
        idp_data = get_idp_endpoints()

        response_data = {
            "subject": resource,
            "links": [
                {"rel": "http://openid.net/specs/connect/1.0/issuer", "href": idp_data["issuer"]},
                {"rel": "authorization_endpoint", "href": idp_data["authorization_endpoint"]},
                {"rel": "token_endpoint", "href": idp_data["token_endpoint"]},
                {"rel": "userinfo_endpoint", "href": idp_data["userinfo_endpoint"]},
                {"rel": "jwks_uri", "href": idp_data["jwks_uri"]},
            ],
        }

        app.logger.info(f"Successfully processed WebFinger request for {resource}")
        return jsonify(response_data), 200

    except requests.exceptions.Timeout:
        app.logger.error("IDP request timed out")
        return jsonify({"error": "Service temporarily unavailable"}), 503
    except requests.exceptions.ConnectionError:
        app.logger.error("Could not connect to IDP")
        return jsonify({"error": "Service temporarily unavailable"}), 503
    except requests.exceptions.HTTPError:
        app.logger.error("IDP returned an error")
        return jsonify({"error": "Service temporarily unavailable"}), 503
    except Exception as e:
        app.logger.error(f"Unexpected error in webfinger: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Quick validation that we can reach IDP
        get_idp_endpoints()
        return jsonify(
            {
                "status": "healthy",
                "domain": DOMAIN,
                "application": APPLICATION,
                "cache_age": time.time() - _cache_timestamp if _cache else None,
            }
        ), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
