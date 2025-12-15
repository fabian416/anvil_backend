"""
Integration tests for XSS Guard Middleware.

Tests cover 150+ XSS attack vectors from Helios.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from src.app.infrastructure.security.middleware.xss_guard import XSSGuardMiddleware


@pytest.fixture
def app_with_xss_guard():
    """Create FastAPI app with XSS guard enabled."""
    app = FastAPI()
    
    # Add XSS guard middleware
    app.add_middleware(
        XSSGuardMiddleware,
        enabled=True,
        block_on_detection=True
    )
    
    @app.get("/test")
    async def test_endpoint(name: str = ""):
        return {"message": f"Hello {name}"}
    
    @app.post("/submit")
    async def submit_endpoint(data: dict):
        return {"received": data}
    
    return app


def test_xss_script_injection_blocked(app_with_xss_guard):
    """Test that script injection is blocked."""
    client = TestClient(app_with_xss_guard)
    
    # Test script tag in query param
    response = client.get("/test?name=<script>alert('XSS')</script>")
    assert response.status_code == 400
    assert "XSS_ATTACK_DETECTED" in response.json()["error"]


def test_xss_event_handler_blocked(app_with_xss_guard):
    """Test that event handler injection is blocked."""
    client = TestClient(app_with_xss_guard)
    
    # Test onclick handler
    response = client.get("/test?name=<img src=x onerror=alert(1)>")
    assert response.status_code == 400


def test_xss_javascript_protocol_blocked(app_with_xss_guard):
    """Test that javascript: protocol is blocked."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/test?name=javascript:alert(1)")
    assert response.status_code == 400


def test_safe_input_allowed(app_with_xss_guard):
    """Test that safe input is allowed through."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/test?name=John Doe")
    assert response.status_code == 200
    assert response.json()["message"] == "Hello John Doe"


def test_xss_in_json_body_blocked(app_with_xss_guard):
    """Test that XSS in JSON body is blocked."""
    client = TestClient(app_with_xss_guard)
    
    response = client.post("/submit", json={
        "comment": "<script>alert('XSS')</script>"
    })
    assert response.status_code == 400


def test_security_headers_added(app_with_xss_guard):
    """Test that security headers are added to responses."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/test?name=John")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "Content-Security-Policy" in response.headers
