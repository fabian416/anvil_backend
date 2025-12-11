"""
Telemetry Feature Flags Configuration.

Provides granular control over telemetry components:
- Enable/disable each telemetry type independently
- Configure per-API instrumentation
- Runtime toggle support

Usage:
    from app.infrastructure.telemetry.feature_flags import (
        TelemetryFeatureFlags,
        get_feature_flags,
    )
    
    flags = get_feature_flags()
    
    # Check if API telemetry is enabled
    if flags.api_telemetry_enabled:
        # ... instrument API call
    
    # Check if specific API is enabled
    if flags.is_api_enabled("coingecko"):
        # ... instrument CoinGecko call
"""

import os
from dataclasses import dataclass, field
from typing import Any, Optional, Set


@dataclass
class TelemetryFeatureFlags:
    """
    Granular feature flags for telemetry components.
    
    Attributes:
        global_enabled: Master switch for all telemetry
        api_telemetry_enabled: Enable external API telemetry
        llm_telemetry_enabled: Enable LLM provider telemetry
        db_telemetry_enabled: Enable database query telemetry
        tracing_enabled: Enable distributed tracing
        metrics_export_enabled: Enable Prometheus metrics export
        
        # Per-API flags
        enabled_apis: Set of API names to instrument (empty = all)
        disabled_apis: Set of API names to skip instrumentation
        
        # Per-LLM provider flags
        enabled_llm_providers: Set of LLM providers to instrument (empty = all)
        disabled_llm_providers: Set of LLM providers to skip
        
        # Database telemetry flags
        db_slow_query_logging: Log slow queries
        db_query_patterns: Track query patterns
        db_connection_pool: Track connection pool stats
        
        # Per-endpoint flags (for admin routes)
        endpoint_telemetry_enabled: Enable HTTP endpoint telemetry
        disabled_endpoints: Set of endpoint paths to skip
        admin_telemetry_enabled: Enable telemetry for /admin/* routes
    """
    
    # Master switch
    global_enabled: bool = True
    
    # Component-level flags
    api_telemetry_enabled: bool = True
    llm_telemetry_enabled: bool = True
    db_telemetry_enabled: bool = True
    tracing_enabled: bool = True
    metrics_export_enabled: bool = True
    
    # Per-API granular control
    enabled_apis: Set[str] = field(default_factory=set)  # Empty = all enabled
    disabled_apis: Set[str] = field(default_factory=set)
    
    # Per-LLM provider control
    enabled_llm_providers: Set[str] = field(default_factory=set)  # Empty = all enabled
    disabled_llm_providers: Set[str] = field(default_factory=set)
    
    # Database telemetry sub-flags
    db_slow_query_logging: bool = True
    db_query_patterns: bool = True
    db_connection_pool: bool = True
    
    # Sampling rates (0.0 - 1.0)
    api_sample_rate: float = 1.0
    llm_sample_rate: float = 1.0
    db_sample_rate: float = 1.0
    trace_sample_rate: float = 1.0
    
    # Per-endpoint control (for HTTP routes)
    endpoint_telemetry_enabled: bool = True
    admin_telemetry_enabled: bool = True  # /admin/* routes
    disabled_endpoints: Set[str] = field(default_factory=set)  # Explicit endpoint paths to skip
    enabled_endpoint_prefixes: Set[str] = field(default_factory=set)  # Empty = all
    disabled_endpoint_prefixes: Set[str] = field(default_factory=set)  # Explicit prefixes to skip
    
    def is_enabled(self) -> bool:
        """Check if telemetry is globally enabled."""
        return self.global_enabled
    
    def is_api_telemetry_enabled(self) -> bool:
        """Check if API telemetry is enabled."""
        return self.global_enabled and self.api_telemetry_enabled
    
    def is_llm_telemetry_enabled(self) -> bool:
        """Check if LLM telemetry is enabled."""
        return self.global_enabled and self.llm_telemetry_enabled
    
    def is_db_telemetry_enabled(self) -> bool:
        """Check if database telemetry is enabled."""
        return self.global_enabled and self.db_telemetry_enabled
    
    def is_tracing_enabled(self) -> bool:
        """Check if distributed tracing is enabled."""
        return self.global_enabled and self.tracing_enabled
    
    def is_api_enabled(self, api_name: str) -> bool:
        """
        Check if telemetry is enabled for a specific API.
        
        Logic:
        1. If global or API telemetry disabled, return False
        2. If api_name in disabled_apis, return False
        3. If enabled_apis is empty (default), return True
        4. If api_name in enabled_apis, return True
        5. Otherwise, return False
        
        Args:
            api_name: Name of the API (e.g., "coingecko", "uniswap")
            
        Returns:
            True if telemetry should be collected for this API
        """
        if not self.is_api_telemetry_enabled():
            return False
        
        api_lower = api_name.lower()
        
        # Explicit disable takes precedence
        if api_lower in self.disabled_apis:
            return False
        
        # If no explicit whitelist, all are enabled
        if not self.enabled_apis:
            return True
        
        # Check whitelist
        return api_lower in self.enabled_apis
    
    def is_llm_provider_enabled(self, provider: str) -> bool:
        """
        Check if telemetry is enabled for a specific LLM provider.
        
        Args:
            provider: Name of the provider (e.g., "vertex_ai", "openai")
            
        Returns:
            True if telemetry should be collected for this provider
        """
        if not self.is_llm_telemetry_enabled():
            return False
        
        provider_lower = provider.lower()
        
        # Explicit disable takes precedence
        if provider_lower in self.disabled_llm_providers:
            return False
        
        # If no explicit whitelist, all are enabled
        if not self.enabled_llm_providers:
            return True
        
        # Check whitelist
        return provider_lower in self.enabled_llm_providers
    
    def is_endpoint_telemetry_enabled(self) -> bool:
        """Check if HTTP endpoint telemetry is enabled."""
        return self.global_enabled and self.endpoint_telemetry_enabled
    
    def is_endpoint_enabled(self, path: str) -> bool:
        """
        Check if telemetry is enabled for a specific HTTP endpoint.
        
        Args:
            path: HTTP endpoint path (e.g., "/api/v1/admin/users", "/api/v1/user/chat")
            
        Returns:
            True if telemetry should be collected for this endpoint
        """
        if not self.is_endpoint_telemetry_enabled():
            return False
        
        path_lower = path.lower()
        
        # Check admin routes - matches /api/v1/admin/*
        if self.is_admin_endpoint(path_lower) and not self.admin_telemetry_enabled:
            return False
        
        # Explicit disable takes precedence
        if path_lower in self.disabled_endpoints:
            return False
        
        # Check disabled prefixes
        for prefix in self.disabled_endpoint_prefixes:
            if path_lower.startswith(prefix.lower()):
                return False
        
        # If no whitelist, all enabled
        if not self.enabled_endpoint_prefixes:
            return True
        
        # Check whitelist prefixes
        for prefix in self.enabled_endpoint_prefixes:
            if path_lower.startswith(prefix.lower()):
                return True
        
        return False
    
    def is_admin_endpoint(self, path: str) -> bool:
        """Check if path is an admin endpoint (/api/v1/admin/*)."""
        path_lower = path.lower()
        return "/admin/" in path_lower
    
    def is_user_endpoint(self, path: str) -> bool:
        """Check if path is a user endpoint (/api/v1/user/*)."""
        path_lower = path.lower()
        return "/user/" in path_lower
    
    def should_sample_api(self, api_name: str) -> bool:
        """Check if an API call should be sampled based on rate."""
        if not self.is_api_enabled(api_name):
            return False
        if self.api_sample_rate >= 1.0:
            return True
        if self.api_sample_rate <= 0.0:
            return False
        import random
        return random.random() < self.api_sample_rate
    
    def should_sample_llm(self, provider: str) -> bool:
        """Check if an LLM call should be sampled based on rate."""
        if not self.is_llm_provider_enabled(provider):
            return False
        if self.llm_sample_rate >= 1.0:
            return True
        if self.llm_sample_rate <= 0.0:
            return False
        import random
        return random.random() < self.llm_sample_rate
    
    def should_sample_db(self) -> bool:
        """Check if a database query should be sampled based on rate."""
        if not self.is_db_telemetry_enabled():
            return False
        if self.db_sample_rate >= 1.0:
            return True
        if self.db_sample_rate <= 0.0:
            return False
        import random
        return random.random() < self.db_sample_rate
    
    def should_sample_trace(self) -> bool:
        """Check if a trace should be sampled based on rate."""
        if not self.is_tracing_enabled():
            return False
        if self.trace_sample_rate >= 1.0:
            return True
        if self.trace_sample_rate <= 0.0:
            return False
        import random
        return random.random() < self.trace_sample_rate
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "global_enabled": self.global_enabled,
            "components": {
                "api_telemetry": self.api_telemetry_enabled,
                "llm_telemetry": self.llm_telemetry_enabled,
                "db_telemetry": self.db_telemetry_enabled,
                "tracing": self.tracing_enabled,
                "metrics_export": self.metrics_export_enabled,
                "endpoint_telemetry": self.endpoint_telemetry_enabled,
            },
            "api_config": {
                "enabled_apis": list(self.enabled_apis),
                "disabled_apis": list(self.disabled_apis),
                "sample_rate": self.api_sample_rate,
            },
            "llm_config": {
                "enabled_providers": list(self.enabled_llm_providers),
                "disabled_providers": list(self.disabled_llm_providers),
                "sample_rate": self.llm_sample_rate,
            },
            "db_config": {
                "slow_query_logging": self.db_slow_query_logging,
                "query_patterns": self.db_query_patterns,
                "connection_pool": self.db_connection_pool,
                "sample_rate": self.db_sample_rate,
            },
            "endpoint_config": {
                "admin_telemetry_enabled": self.admin_telemetry_enabled,
                "disabled_endpoints": list(self.disabled_endpoints),
                "enabled_prefixes": list(self.enabled_endpoint_prefixes),
                "disabled_prefixes": list(self.disabled_endpoint_prefixes),
            },
            "trace_sample_rate": self.trace_sample_rate,
        }


# ============================================================================
# ENVIRONMENT-BASED CONFIGURATION
# ============================================================================


def load_feature_flags_from_env() -> TelemetryFeatureFlags:
    """
    Load feature flags from environment variables.
    
    Environment variables:
        TELEMETRY_ENABLED: Master switch (default: true)
        TELEMETRY_API_ENABLED: API telemetry (default: true)
        TELEMETRY_LLM_ENABLED: LLM telemetry (default: true)
        TELEMETRY_DB_ENABLED: Database telemetry (default: true)
        TELEMETRY_TRACING_ENABLED: Distributed tracing (default: true)
        TELEMETRY_METRICS_ENABLED: Prometheus export (default: true)
        
        TELEMETRY_ENABLED_APIS: Comma-separated list of APIs to enable
        TELEMETRY_DISABLED_APIS: Comma-separated list of APIs to disable
        TELEMETRY_ENABLED_LLM_PROVIDERS: Comma-separated providers
        TELEMETRY_DISABLED_LLM_PROVIDERS: Comma-separated providers
        
        TELEMETRY_API_SAMPLE_RATE: API sampling rate (0.0-1.0)
        TELEMETRY_LLM_SAMPLE_RATE: LLM sampling rate (0.0-1.0)
        TELEMETRY_DB_SAMPLE_RATE: Database sampling rate (0.0-1.0)
        TELEMETRY_TRACE_SAMPLE_RATE: Trace sampling rate (0.0-1.0)
        
        TELEMETRY_DB_SLOW_QUERY_LOGGING: Log slow queries (default: true)
        TELEMETRY_DB_QUERY_PATTERNS: Track query patterns (default: true)
        TELEMETRY_DB_CONNECTION_POOL: Track pool stats (default: true)
    
    Returns:
        TelemetryFeatureFlags configured from environment
    """
    def parse_bool(value: str, default: bool = True) -> bool:
        if not value:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    def parse_float(value: str, default: float = 1.0) -> float:
        if not value:
            return default
        try:
            return max(0.0, min(1.0, float(value)))
        except ValueError:
            return default
    
    def parse_set(value: str) -> Set[str]:
        if not value:
            return set()
        return {v.strip().lower() for v in value.split(",") if v.strip()}
    
    return TelemetryFeatureFlags(
        # Master switch
        global_enabled=parse_bool(os.getenv("TELEMETRY_ENABLED", "true")),
        
        # Component flags
        api_telemetry_enabled=parse_bool(os.getenv("TELEMETRY_API_ENABLED", "true")),
        llm_telemetry_enabled=parse_bool(os.getenv("TELEMETRY_LLM_ENABLED", "true")),
        db_telemetry_enabled=parse_bool(os.getenv("TELEMETRY_DB_ENABLED", "true")),
        tracing_enabled=parse_bool(os.getenv("TELEMETRY_TRACING_ENABLED", "true")),
        metrics_export_enabled=parse_bool(os.getenv("TELEMETRY_METRICS_ENABLED", "true")),
        
        # Per-API config
        enabled_apis=parse_set(os.getenv("TELEMETRY_ENABLED_APIS", "")),
        disabled_apis=parse_set(os.getenv("TELEMETRY_DISABLED_APIS", "")),
        
        # Per-LLM provider config
        enabled_llm_providers=parse_set(os.getenv("TELEMETRY_ENABLED_LLM_PROVIDERS", "")),
        disabled_llm_providers=parse_set(os.getenv("TELEMETRY_DISABLED_LLM_PROVIDERS", "")),
        
        # Database sub-flags
        db_slow_query_logging=parse_bool(os.getenv("TELEMETRY_DB_SLOW_QUERY_LOGGING", "true")),
        db_query_patterns=parse_bool(os.getenv("TELEMETRY_DB_QUERY_PATTERNS", "true")),
        db_connection_pool=parse_bool(os.getenv("TELEMETRY_DB_CONNECTION_POOL", "true")),
        
        # Sample rates
        api_sample_rate=parse_float(os.getenv("TELEMETRY_API_SAMPLE_RATE", "1.0")),
        llm_sample_rate=parse_float(os.getenv("TELEMETRY_LLM_SAMPLE_RATE", "1.0")),
        db_sample_rate=parse_float(os.getenv("TELEMETRY_DB_SAMPLE_RATE", "1.0")),
        trace_sample_rate=parse_float(os.getenv("TELEMETRY_TRACE_SAMPLE_RATE", "1.0")),
        
        # Endpoint/route config
        endpoint_telemetry_enabled=parse_bool(os.getenv("TELEMETRY_ENDPOINT_ENABLED", "true")),
        admin_telemetry_enabled=parse_bool(os.getenv("TELEMETRY_ADMIN_ENABLED", "true")),
        disabled_endpoints=parse_set(os.getenv("TELEMETRY_DISABLED_ENDPOINTS", "")),
        enabled_endpoint_prefixes=parse_set(os.getenv("TELEMETRY_ENABLED_ENDPOINT_PREFIXES", "")),
        disabled_endpoint_prefixes=parse_set(os.getenv("TELEMETRY_DISABLED_ENDPOINT_PREFIXES", "")),
    )


# ============================================================================
# PERSISTENCE
# ============================================================================

import json
import logging

logger = logging.getLogger(__name__)

REDIS_KEY = "telemetry:feature_flags"


async def save_flags_to_redis(
    flags: TelemetryFeatureFlags,
    redis_client: Any,
) -> bool:
    """
    Persist feature flags to Redis.
    
    Args:
        flags: Feature flags to save
        redis_client: Redis async client
        
    Returns:
        True if saved successfully
    """
    try:
        data = {
            "global_enabled": flags.global_enabled,
            "api_telemetry_enabled": flags.api_telemetry_enabled,
            "llm_telemetry_enabled": flags.llm_telemetry_enabled,
            "db_telemetry_enabled": flags.db_telemetry_enabled,
            "tracing_enabled": flags.tracing_enabled,
            "metrics_export_enabled": flags.metrics_export_enabled,
            "enabled_apis": list(flags.enabled_apis),
            "disabled_apis": list(flags.disabled_apis),
            "enabled_llm_providers": list(flags.enabled_llm_providers),
            "disabled_llm_providers": list(flags.disabled_llm_providers),
            "db_slow_query_logging": flags.db_slow_query_logging,
            "db_query_patterns": flags.db_query_patterns,
            "db_connection_pool": flags.db_connection_pool,
            "api_sample_rate": flags.api_sample_rate,
            "llm_sample_rate": flags.llm_sample_rate,
            "db_sample_rate": flags.db_sample_rate,
            "trace_sample_rate": flags.trace_sample_rate,
            # Endpoint flags
            "endpoint_telemetry_enabled": flags.endpoint_telemetry_enabled,
            "admin_telemetry_enabled": flags.admin_telemetry_enabled,
            "disabled_endpoints": list(flags.disabled_endpoints),
            "enabled_endpoint_prefixes": list(flags.enabled_endpoint_prefixes),
            "disabled_endpoint_prefixes": list(flags.disabled_endpoint_prefixes),
        }
        await redis_client.set(REDIS_KEY, json.dumps(data))
        logger.info("Telemetry feature flags saved to Redis")
        return True
    except Exception as e:
        logger.error(f"Failed to save feature flags to Redis: {e}")
        return False


async def load_flags_from_redis(
    redis_client: Any,
) -> Optional[TelemetryFeatureFlags]:
    """
    Load feature flags from Redis.
    
    Args:
        redis_client: Redis async client
        
    Returns:
        Feature flags if found, None otherwise
    """
    try:
        data = await redis_client.get(REDIS_KEY)
        if data is None:
            return None
        
        parsed = json.loads(data)
        
        return TelemetryFeatureFlags(
            global_enabled=parsed.get("global_enabled", True),
            api_telemetry_enabled=parsed.get("api_telemetry_enabled", True),
            llm_telemetry_enabled=parsed.get("llm_telemetry_enabled", True),
            db_telemetry_enabled=parsed.get("db_telemetry_enabled", True),
            tracing_enabled=parsed.get("tracing_enabled", True),
            metrics_export_enabled=parsed.get("metrics_export_enabled", True),
            enabled_apis=set(parsed.get("enabled_apis", [])),
            disabled_apis=set(parsed.get("disabled_apis", [])),
            enabled_llm_providers=set(parsed.get("enabled_llm_providers", [])),
            disabled_llm_providers=set(parsed.get("disabled_llm_providers", [])),
            db_slow_query_logging=parsed.get("db_slow_query_logging", True),
            db_query_patterns=parsed.get("db_query_patterns", True),
            db_connection_pool=parsed.get("db_connection_pool", True),
            api_sample_rate=parsed.get("api_sample_rate", 1.0),
            llm_sample_rate=parsed.get("llm_sample_rate", 1.0),
            db_sample_rate=parsed.get("db_sample_rate", 1.0),
            trace_sample_rate=parsed.get("trace_sample_rate", 1.0),
            # Endpoint flags
            endpoint_telemetry_enabled=parsed.get("endpoint_telemetry_enabled", True),
            admin_telemetry_enabled=parsed.get("admin_telemetry_enabled", True),
            disabled_endpoints=set(parsed.get("disabled_endpoints", [])),
            enabled_endpoint_prefixes=set(parsed.get("enabled_endpoint_prefixes", [])),
            disabled_endpoint_prefixes=set(parsed.get("disabled_endpoint_prefixes", [])),
        )
    except Exception as e:
        logger.warning(f"Failed to load feature flags from Redis: {e}")
        return None


async def delete_flags_from_redis(redis_client: Any) -> bool:
    """
    Delete persisted feature flags from Redis.
    
    This will cause the system to fall back to environment-based flags on restart.
    
    Args:
        redis_client: Redis async client
        
    Returns:
        True if deleted successfully
    """
    try:
        await redis_client.delete(REDIS_KEY)
        logger.info("Telemetry feature flags deleted from Redis")
        return True
    except Exception as e:
        logger.error(f"Failed to delete feature flags from Redis: {e}")
        return False


# ============================================================================
# SINGLETON & FACTORY
# ============================================================================


_feature_flags: Optional[TelemetryFeatureFlags] = None


def get_feature_flags() -> TelemetryFeatureFlags:
    """Get the global telemetry feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = load_feature_flags_from_env()
    return _feature_flags


def set_feature_flags(flags: TelemetryFeatureFlags) -> None:
    """Set the global telemetry feature flags instance."""
    global _feature_flags
    _feature_flags = flags


def reset_feature_flags() -> None:
    """Reset feature flags to reload from environment."""
    global _feature_flags
    _feature_flags = None


async def initialize_feature_flags(redis_client: Optional[Any] = None) -> TelemetryFeatureFlags:
    """
    Initialize feature flags, loading from Redis if available.
    
    Priority:
    1. Redis (if connected and has saved flags)
    2. Environment variables
    3. Defaults
    
    Args:
        redis_client: Optional Redis client for persistence
        
    Returns:
        Initialized feature flags
    """
    global _feature_flags
    
    # Try to load from Redis first
    if redis_client is not None:
        try:
            redis_flags = await load_flags_from_redis(redis_client)
            if redis_flags is not None:
                _feature_flags = redis_flags
                logger.info("Loaded telemetry feature flags from Redis")
                return _feature_flags
        except Exception as e:
            logger.warning(f"Could not load flags from Redis: {e}")
    
    # Fall back to environment
    _feature_flags = load_feature_flags_from_env()
    logger.info("Loaded telemetry feature flags from environment")
    return _feature_flags
