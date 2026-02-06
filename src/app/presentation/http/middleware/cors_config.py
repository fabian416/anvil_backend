"""
CORS Configuration.

Environment-specific CORS settings following security best practices.
"""

from typing import List
import logging

logger = logging.getLogger(__name__)


def get_cors_origins(environment: str = "local") -> List[str]:
    """
    Get allowed CORS origins based on environment.

    Args:
        environment: Environment name (local, dev, prod)

    Returns:
        List of allowed origins
    """
    cors_origins_map = {
        "local": [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",  # Vite dev server
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
        ],
        "dev": [
            "https://development.anvil.zk-access.xyz",  # Frontend staging
            "https://development.api.anvil.zk-access.xyz",  # API staging
            "http://localhost:3000",  # For local development
            "http://localhost:5173",  # Vite dev server
        ],
        "staging": [
            "https://staging.anvil.zk-access.xyz",  # Frontend staging
            "https://staging.api.anvil.zk-access.xyz",  # API staging
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        "prod": [
            "https://anvil.zk-access.xyz",  # Frontend production
            "https://api.anvil.zk-access.xyz",  # API production
        ],
        "production": [
            "https://anvil.zk-access.xyz",
            "https://api.anvil.zk-access.xyz",
        ],
    }

    origins = cors_origins_map.get(environment, cors_origins_map["local"])
    logger.info(f"CORS origins configured for {environment}: {origins}")
    return origins


def get_cors_config(environment: str = "local") -> dict:
    """
    Get complete CORS configuration based on environment.

    Args:
        environment: Environment name (local, dev, prod)

    Returns:
        Dictionary with CORS configuration
    """
    is_production = environment in ("prod", "production")

    config = {
        "allow_origins": get_cors_origins(environment),
        "allow_credentials": True,  # Allow cookies for authentication
        "allow_methods": [
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ]
        if not is_production
        else [
            "GET",
            "POST",
            "PUT",
            "DELETE",  # Remove PATCH in production if not needed
        ],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-CSRF-Token",
        ],
        "expose_headers": [
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        "max_age": 600 if is_production else 3600,  # Shorter max-age in production
    }

    logger.info(f"CORS configuration loaded for {environment}")
    return config
