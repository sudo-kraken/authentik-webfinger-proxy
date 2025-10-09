"""Tests for the Authentik WebFinger Proxy"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests
from flask import Flask


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    with patch.dict(
        os.environ,
        {
            "DOMAIN": "test.example.com",
            "APPLICATION": "testapp",
            "CACHE_TTL": "300",
            "REQUEST_TIMEOUT": "10",
        },
    ):
        from app import app as app_module

        app_module._cache = {}
        app_module._cache_timestamp = 0

        app_module.DOMAIN = "test.example.com"
        app_module.APPLICATION = "testapp"
        app_module.issuer_url = "https://test.example.com/application/o/testapp/"

        flask_app = app_module.app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            yield client


@pytest.fixture
def mock_idp_response():
    """Mock IDP response data."""
    return {
        "issuer": "https://test.example.com/application/o/testapp/",
        "authorization_endpoint": "https://test.example.com/application/o/testapp/authorize/",
        "token_endpoint": "https://test.example.com/application/o/testapp/token/",
        "userinfo_endpoint": "https://test.example.com/application/o/testapp/userinfo/",
        "jwks_uri": "https://test.example.com/application/o/testapp/jwks/",
    }


class TestWebFingerEndpoint:
    """Tests for the /.well-known/webfinger endpoint."""

    def test_webfinger_success(self, client, mock_idp_response):
        """Test successful WebFinger request."""
        with patch("app.app.session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_idp_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            response = client.get("/.well-known/webfinger?resource=acct:user@example.com")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["subject"] == "acct:user@example.com"
            assert len(data["links"]) == 5
            assert data["links"][0]["rel"] == "http://openid.net/specs/connect/1.0/issuer"
            assert data["links"][0]["href"] == mock_idp_response["issuer"]

    def test_webfinger_missing_resource(self, client):
        """Test WebFinger request without resource parameter."""
        response = client.get("/.well-known/webfinger")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Missing resource parameter"

    def test_webfinger_invalid_resource(self, client):
        """Test WebFinger request with invalid resource format."""
        response = client.get("/.well-known/webfinger?resource=invalid:user@example.com")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Resource must start with 'acct:'"

    def test_webfinger_idp_timeout(self, client):
        """Test WebFinger when IDP times out."""
        with patch("app.app.session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            response = client.get("/.well-known/webfinger?resource=acct:user@example.com")

            assert response.status_code == 503
            data = json.loads(response.data)
            assert "error" in data
            assert data["error"] == "Service temporarily unavailable"

    def test_webfinger_idp_connection_error(self, client):
        """Test WebFinger when IDP connection fails."""
        with patch("app.app.session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            response = client.get("/.well-known/webfinger?resource=acct:user@example.com")

            assert response.status_code == 503
            data = json.loads(response.data)
            assert "error" in data
            assert data["error"] == "Service temporarily unavailable"

    def test_webfinger_idp_http_error(self, client):
        """Test WebFinger when IDP returns HTTP error."""
        with patch("app.app.session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            http_error = requests.exceptions.HTTPError()
            http_error.response = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_get.return_value = mock_response

            response = client.get("/.well-known/webfinger?resource=acct:user@example.com")

            assert response.status_code == 503
            data = json.loads(response.data)
            assert "error" in data


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_success(self, client, mock_idp_response):
        """Test successful health check."""
        with patch("app.app.session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_idp_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            response = client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "healthy"
            assert data["domain"] == "test.example.com"
            assert data["application"] == "testapp"

    def test_health_check_failure(self, client):
        """Test health check when IDP is unavailable."""
        with patch("app.app.session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            response = client.get("/health")

            assert response.status_code == 503
            data = json.loads(response.data)
            assert data["status"] == "unhealthy"
            assert "error" in data


class TestCaching:
    """Tests for IDP endpoint caching."""

    def test_cache_works(self, client, mock_idp_response):
        """Test that IDP endpoints are cached."""
        with patch("app.app.session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_idp_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # First request should fetch from IDP
            response1 = client.get("/.well-known/webfinger?resource=acct:user1@example.com")
            assert response1.status_code == 200
            assert mock_get.call_count == 1

            # Second request should use cache
            response2 = client.get("/.well-known/webfinger?resource=acct:user2@example.com")
            assert response2.status_code == 200
            # Should still be 1 because it used the cache
            assert mock_get.call_count == 1


class TestInputValidation:
    """Tests for input validation."""

    def test_validate_application_name_valid(self):
        """Test application name validation with valid input."""
        from app.app import validate_application_name

        assert validate_application_name("valid-app_123") == "valid-app_123"
        assert validate_application_name("app") == "app"
        assert validate_application_name("my-app-123") == "my-app-123"

    def test_validate_application_name_invalid(self):
        """Test application name validation with invalid input."""
        from app.app import validate_application_name

        with pytest.raises(ValueError, match="Invalid application name"):
            validate_application_name("app with spaces")

        with pytest.raises(ValueError, match="Invalid application name"):
            validate_application_name("app/with/slashes")

        with pytest.raises(ValueError, match="Invalid application name"):
            validate_application_name("app;with;semicolons")


class TestIDPEndpoints:
    """Tests for IDP endpoint fetching."""

    def test_missing_required_endpoint(self, client):
        """Test handling of IDP response missing required endpoints."""
        incomplete_response = {
            "issuer": "https://test.example.com/application/o/testapp/",
            "authorization_endpoint": "https://test.example.com/application/o/testapp/authorize/",
        }

        with patch("app.app.session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = incomplete_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            response = client.get("/.well-known/webfinger?resource=acct:user@example.com")

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
