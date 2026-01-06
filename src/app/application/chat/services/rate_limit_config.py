"""
Rate Limit Configuration.

Defines rate limits by user type (guest, authenticated, premium).
"""

from typing import TypedDict


class RateLimitConfig(TypedDict):
    """Rate limit configuration for a user type."""
    
    messages_per_hour: int | None
    messages_per_day: int | None
    max_conversations: int | None
    features: list[str]


# Rate limits by user type
RATE_LIMITS: dict[str, RateLimitConfig] = {
    "guest": {
        "messages_per_hour": 20,
        "messages_per_day": 50,
        "max_conversations": 1,
        "features": [
            "sentiment",
            "prediction", 
            "signals",
            "protocol_search",
            "swap_quote",
            "risk_assessment",
            "similar_protocols",
            "general_conversation",
        ],
    },
    "authenticated": {
        "messages_per_hour": 200,
        "messages_per_day": 1000,
        "max_conversations": 50,
        "features": ["*"],  # All features
    },
    "premium": {
        "messages_per_hour": None,  # No limit
        "messages_per_day": None,
        "max_conversations": None,
        "features": ["*"],
    },
}


def get_rate_limit_config(user_type: str) -> RateLimitConfig:
    """Get rate limit configuration for user type."""
    return RATE_LIMITS.get(user_type, RATE_LIMITS["guest"])


def has_unlimited_access(user_type: str) -> bool:
    """Check if user type has unlimited access."""
    config = get_rate_limit_config(user_type)
    return config["messages_per_hour"] is None and config["messages_per_day"] is None


def get_feature_list(user_type: str) -> list[str]:
    """Get list of allowed features for user type."""
    config = get_rate_limit_config(user_type)
    return config["features"]


def can_access_feature(user_type: str, feature: str) -> bool:
    """Check if user type can access a specific feature."""
    features = get_feature_list(user_type)
    return "*" in features or feature in features

