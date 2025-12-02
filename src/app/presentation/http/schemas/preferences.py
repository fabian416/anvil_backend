"""
User preferences request/response schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Response schemas
class UserPreferencesResponse(BaseModel):
    """User preferences response."""

    user_id: str
    risk_tolerance: str
    preferred_chains: List[str]
    preferred_categories: List[str]
    excluded_protocols: List[str]
    favorite_protocols: List[str]
    search_settings: Dict[str, Any]
    notification_settings: Dict[str, Any]
    default_currency: str
    theme: str

    @classmethod
    def from_entity(cls, entity: Any) -> "UserPreferencesResponse":
        """Create from domain entity."""
        return cls(
            user_id=str(entity.user_id),
            risk_tolerance=entity.risk_tolerance,
            preferred_chains=entity.preferred_chains,
            preferred_categories=entity.preferred_categories,
            excluded_protocols=[str(p) for p in entity.excluded_protocols],
            favorite_protocols=[str(p) for p in entity.favorite_protocols],
            search_settings={
                "default_similarity_threshold": entity.search_settings.default_similarity_threshold,
                "default_risk_filter": entity.search_settings.default_risk_filter,
                "search_history_enabled": entity.search_settings.search_history_enabled,
            },
            notification_settings={
                "risk_alerts_enabled": entity.notification_settings.risk_alerts_enabled,
                "push_enabled": entity.notification_settings.push_enabled,
                "min_severity": entity.notification_settings.min_severity,
            },
            default_currency=entity.default_currency,
            theme=entity.theme,
        )


class SavedSearchResponse(BaseModel):
    """Saved search response."""

    id: str
    name: str
    query: str
    filters: Dict[str, Any]
    created_at: str


# Request schemas
class UpdateRiskToleranceRequest(BaseModel):
    """Update risk tolerance request."""

    risk_tolerance: str = Field(..., pattern="^(conservative|moderate|aggressive)$")


class UpdateChainPreferencesRequest(BaseModel):
    """Update chain preferences request."""

    preferred_chains: List[str] = Field(..., min_items=1, max_items=10)


class UpdateNotificationPreferencesRequest(BaseModel):
    """Update notification preferences request."""

    risk_alerts_enabled: Optional[bool] = None
    protocol_updates_enabled: Optional[bool] = None
    price_alerts_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    min_severity: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")


class SaveSearchRequest(BaseModel):
    """Save search preset request."""

    name: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=500)
    filters: Dict[str, Any] = Field(default_factory=dict)
