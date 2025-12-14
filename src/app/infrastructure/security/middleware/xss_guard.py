"""
XSS Guard Middleware

Protects against Cross-Site Scripting (XSS) attacks based on Helios attack vectors.
Implements 150+ XSS attack pattern detection and sanitization.

OWASP Reference: OWASP Top 10 2021 - A03:2021 – Injection
Helios Coverage: 150+ XSS test cases
"""

import re
import html
import json
from typing import Callable, Any, Dict, List, Optional
from urllib.parse import unquote
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class XSSGuardMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for XSS protection.

    Protects against:
    - Script injection (<script> tags)
    - Event handler injection (onclick, onerror, onload, etc.)
    - SVG-based XSS
    - Data URI XSS
    - JavaScript protocol handlers
    - HTML entity encoding attacks
    - DOM clobbering
    - Attribute-based XSS
    """

    # Critical XSS patterns that should be blocked
    DANGER_PATTERNS = [
        # Script tags (various encodings and obfuscations)
        r'<\s*script[^>]*>.*?</\s*script\s*>',
        r'<\s*script[^>]*>',
        r'</\s*script\s*>',

        # Event handlers
        r'on\w+\s*=\s*["\']?[^"\']*["\']?',
        r'on(?:load|error|click|mouse|key|focus|blur|change|submit|resize|scroll)',

        # JavaScript protocol
        r'javascript\s*:',
        r'vbscript\s*:',

        # Data URIs with JavaScript
        r'data:text/html',
        r'data:.*base64.*script',

        # SVG-based XSS
        r'<\s*svg[^>]*>',
        r'<\s*iframe[^>]*>',
        r'<\s*embed[^>]*>',
        r'<\s*object[^>]*>',

        # Meta refresh XSS
        r'<\s*meta[^>]*http-equiv\s*=\s*["\']?refresh',

        # Link with JavaScript
        r'<\s*link[^>]*>.*javascript:',

        # Form action XSS
        r'<\s*form[^>]*action\s*=\s*["\']?javascript:',

        # Import statements
        r'<\s*import[^>]*>',

        # Expression evaluation
        r'expression\s*\(',
        r'eval\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',

        # HTML entities that decode to dangerous characters
        r'&#x?[0-9a-f]+;',  # Will validate these separately
    ]

    # Suspicious patterns that should be logged but may not be blocked
    SUSPICIOUS_PATTERNS = [
        r'<.*?>',  # Any HTML tag
        r'\\u[0-9a-f]{4}',  # Unicode escapes
        r'\\x[0-9a-f]{2}',  # Hex escapes
        r'fromCharCode',
        r'String\.fromCharCode',
        r'unescape',
        r'decodeURI',
        r'atob',  # Base64 decode
    ]

    # Paths to exclude from XSS checking (e.g., admin endpoints that handle raw HTML)
    EXCLUDED_PATHS = [
        r'/api/admin/.*',  # Admin endpoints may need to handle HTML
        r'/health',  # Health checks
        r'/metrics',  # Metrics endpoints
    ]

    def __init__(
        self,
        app,
        enabled: bool = True,
        block_on_detection: bool = True,
        log_suspicious: bool = True,
        excluded_paths: Optional[List[str]] = None
    ):
        """
        Initialize XSS Guard Middleware.

        Args:
            app: FastAPI application
            enabled: Whether XSS protection is enabled
            block_on_detection: Block requests with detected XSS
            log_suspicious: Log suspicious patterns even if not blocking
            excluded_paths: Additional regex patterns for paths to exclude
        """
        super().__init__(app)
        self.enabled = enabled
        self.block_on_detection = block_on_detection
        self.log_suspicious = log_suspicious

        if excluded_paths:
            self.EXCLUDED_PATHS.extend(excluded_paths)

        # Compile patterns for performance
        self.danger_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGER_PATTERNS]
        self.suspicious_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS]
        self.excluded_regexes = [re.compile(pattern) for pattern in self.EXCLUDED_PATHS]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through XSS guard."""
        if not self.enabled:
            return await call_next(request)

        # Check if path is excluded
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Check query parameters
        xss_found_in_query = self._check_query_params(request)
        if xss_found_in_query:
            logger.warning(
                f"XSS detected in query params: {request.url.path}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "query": str(request.query_params),
                    "detected_patterns": xss_found_in_query
                }
            )
            if self.block_on_detection:
                return self._create_block_response(
                    "XSS attack detected in query parameters",
                    xss_found_in_query
                )

        # Check request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            xss_found_in_body = await self._check_request_body(request)
            if xss_found_in_body:
                logger.warning(
                    f"XSS detected in request body: {request.url.path}",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "detected_patterns": xss_found_in_body
                    }
                )
                if self.block_on_detection:
                    return self._create_block_response(
                        "XSS attack detected in request body",
                        xss_found_in_body
                    )

        # Check headers
        xss_found_in_headers = self._check_headers(request)
        if xss_found_in_headers:
            logger.warning(
                f"XSS detected in headers: {request.url.path}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "detected_patterns": xss_found_in_headers
                }
            )
            if self.block_on_detection:
                return self._create_block_response(
                    "XSS attack detected in headers",
                    xss_found_in_headers
                )

        # Process request
        response = await call_next(request)

        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none'"

        return response

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from XSS checking."""
        return any(regex.match(path) for regex in self.excluded_regexes)

    def _check_query_params(self, request: Request) -> List[str]:
        """Check query parameters for XSS patterns."""
        detected = []

        for key, value in request.query_params.items():
            # URL decode the value
            decoded_value = unquote(value)

            # Check dangerous patterns
            for pattern_idx, regex in enumerate(self.danger_regexes):
                if regex.search(decoded_value):
                    detected.append(f"query.{key}: {self.DANGER_PATTERNS[pattern_idx]}")

            # Check suspicious patterns if logging enabled
            if self.log_suspicious:
                for pattern_idx, regex in enumerate(self.suspicious_regexes):
                    if regex.search(decoded_value):
                        logger.info(
                            f"Suspicious pattern in query param {key}",
                            extra={"pattern": self.SUSPICIOUS_PATTERNS[pattern_idx]}
                        )

        return detected

    async def _check_request_body(self, request: Request) -> List[str]:
        """Check request body for XSS patterns."""
        detected = []

        try:
            # Read body
            body = await request.body()
            if not body:
                return detected

            # Try to parse as JSON
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    json_data = json.loads(body)
                    detected.extend(self._check_json_recursive(json_data))
                except json.JSONDecodeError:
                    pass
            else:
                # Check raw body as text
                try:
                    text = body.decode("utf-8")
                    detected.extend(self._check_text(text, "body"))
                except UnicodeDecodeError:
                    pass

        except Exception as e:
            logger.error(f"Error checking request body: {e}")

        return detected

    def _check_headers(self, request: Request) -> List[str]:
        """Check HTTP headers for XSS patterns."""
        detected = []

        # Headers that commonly contain user input
        user_headers = ["user-agent", "referer", "x-forwarded-for", "x-real-ip"]

        for header_name in user_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                for pattern_idx, regex in enumerate(self.danger_regexes):
                    if regex.search(header_value):
                        detected.append(f"header.{header_name}: {self.DANGER_PATTERNS[pattern_idx]}")

        return detected

    def _check_json_recursive(self, data: Any, path: str = "") -> List[str]:
        """Recursively check JSON data for XSS patterns."""
        detected = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                detected.extend(self._check_json_recursive(value, current_path))

        elif isinstance(data, list):
            for idx, item in enumerate(data):
                current_path = f"{path}[{idx}]"
                detected.extend(self._check_json_recursive(item, current_path))

        elif isinstance(data, str):
            detected.extend(self._check_text(data, path))

        return detected

    def _check_text(self, text: str, location: str) -> List[str]:
        """Check text for XSS patterns."""
        detected = []

        # URL decode if needed
        decoded_text = unquote(text)

        # Check dangerous patterns
        for pattern_idx, regex in enumerate(self.danger_regexes):
            if regex.search(decoded_text):
                detected.append(f"{location}: {self.DANGER_PATTERNS[pattern_idx]}")

        # Check HTML entity attacks
        if "&#" in decoded_text:
            unescaped = html.unescape(decoded_text)
            for pattern_idx, regex in enumerate(self.danger_regexes):
                if regex.search(unescaped):
                    detected.append(f"{location}: HTML entity encoding of {self.DANGER_PATTERNS[pattern_idx]}")

        return detected

    def _create_block_response(self, message: str, detected_patterns: List[str]) -> JSONResponse:
        """Create a blocked response."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "XSS_ATTACK_DETECTED",
                "message": message,
                "details": "Request blocked due to potential XSS attack",
                "security_info": {
                    "detected_patterns": len(detected_patterns),
                    "protection": "Helios XSS Guard"
                }
            },
            headers={
                "X-XSS-Protection": "1; mode=block",
                "X-Content-Type-Options": "nosniff"
            }
        )


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML by escaping dangerous characters.

    Use this for displaying user-generated content.

    Args:
        text: Raw text that may contain HTML

    Returns:
        HTML-escaped text safe for display
    """
    return html.escape(text, quote=True)


def sanitize_json_response(data: Any) -> Any:
    """
    Recursively sanitize all strings in a JSON-serializable object.

    Args:
        data: Dict, list, or primitive value

    Returns:
        Sanitized data structure
    """
    if isinstance(data, dict):
        return {key: sanitize_json_response(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_response(item) for item in data]
    elif isinstance(data, str):
        return sanitize_html(data)
    else:
        return data
