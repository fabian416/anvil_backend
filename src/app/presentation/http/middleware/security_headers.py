"""
Security Headers Middleware.

Implements security best practices by adding HTTP security headers to all responses.
Based on OWASP recommendations and Mozilla Observatory guidelines.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains (HTTPS only)
    - Content-Security-Policy: Restrictive CSP policy
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: Restrictive feature policy
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        enable_csp: bool = True,
        csp_policy: str = None,
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            enable_hsts: Enable HTTP Strict Transport Security (HTTPS only)
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            enable_csp: Enable Content Security Policy
            csp_policy: Custom CSP policy (default: restrictive policy)
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.enable_csp = enable_csp

        # Default CSP policy (restrictive)
        self.csp_policy = (
            csp_policy
            or (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow eval for Swagger UI
                "style-src 'self' 'unsafe-inline'; "  # Allow inline styles for Swagger UI
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # X-Content-Type-Options: Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevents clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: Legacy XSS protection (still good for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Restricts browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # HSTS: Force HTTPS (only add if request is HTTPS)
        if self.enable_hsts:
            # Check if request is HTTPS
            is_https = (
                request.url.scheme == "https"
                or request.headers.get("X-Forwarded-Proto") == "https"
            )
            if is_https:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={self.hsts_max_age}; includeSubDomains; preload"
                )

        # Content-Security-Policy: Prevents XSS and other injection attacks
        if self.enable_csp:
            response.headers["Content-Security-Policy"] = self.csp_policy

        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS.

    Only active in production environments.
    """

    def __init__(self, app: ASGIApp, enabled: bool = False):
        """
        Initialize HTTPS redirect middleware.

        Args:
            app: ASGI application
            enabled: Enable HTTPS redirect (should be True in production)
        """
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Redirect HTTP to HTTPS if enabled."""
        if not self.enabled:
            return await call_next(request)

        # Check if request is HTTP
        is_http = (
            request.url.scheme == "http"
            and request.headers.get("X-Forwarded-Proto") != "https"
        )

        if is_http:
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            from starlette.responses import RedirectResponse

            logger.info(f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}")
            return RedirectResponse(url=str(https_url), status_code=301)

        return await call_next(request)


def create_security_middleware(
    app: ASGIApp,
    environment: str = "local",
    enable_https_redirect: bool = False,
) -> ASGIApp:
    """
    Factory function to create and configure security middleware.

    Args:
        app: ASGI application
        environment: Environment name (local, dev, prod)
        enable_https_redirect: Force HTTPS redirect (production only)

    Returns:
        ASGI application with security middleware applied
    """
    # Determine settings based on environment
    is_production = environment in ("prod", "production")

    # Add HTTPS redirect (production only)
    if enable_https_redirect and is_production:
        app = HTTPSRedirectMiddleware(app, enabled=True)
        logger.info("HTTPS redirect middleware enabled (production)")

    # Add security headers
    app = SecurityHeadersMiddleware(
        app,
        enable_hsts=is_production,  # HSTS only in production
        enable_csp=True,  # CSP in all environments
    )
    logger.info(f"Security headers middleware enabled (environment: {environment})")

    return app
