"""
Alerts-related request/response schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# Response schemas
class RiskAlertResponse(BaseModel):
    """Risk alert response."""

    id: str
    user_id: str
    protocol_id: str
    protocol_name: str
    alert_type: str
    severity: str
    message: str
    details: dict
    recommendations: List[str]
    current_risk_score: float
    previous_risk_score: Optional[float]
    risk_change: Optional[float]
    acknowledged: bool
    dismissed: bool
    acted_upon: bool
    created_at: str
    acknowledged_at: Optional[str]
    expires_at: Optional[str]


class RiskAlertListResponse(BaseModel):
    """List of risk alerts response."""

    alerts: List[RiskAlertResponse]
    total: int
    unacknowledged: int


# Request schemas
class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""

    acted_upon: bool = Field(
        False, description="Whether user took action on this alert"
    )


class UpdateSubscriptionRequest(BaseModel):
    """Request to update alert subscription."""

    risk_alerts_enabled: Optional[bool] = None
    anomaly_alerts_enabled: Optional[bool] = None
    protocol_update_alerts_enabled: Optional[bool] = None
    price_alerts_enabled: Optional[bool] = None
    min_severity: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    subscribed_protocols: Optional[List[str]] = None
    excluded_protocols: Optional[List[str]] = None
    push_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    websocket_notifications: Optional[bool] = None
    max_alerts_per_hour: Optional[int] = Field(None, ge=1, le=100)


class AlertSubscriptionResponse(BaseModel):
    """Alert subscription preferences response."""

    risk_alerts_enabled: bool
    anomaly_alerts_enabled: bool
    protocol_update_alerts_enabled: bool
    price_alerts_enabled: bool
    min_severity: str
    subscribed_protocols: List[str]
    excluded_protocols: List[str]
    push_notifications: bool
    email_notifications: bool
    websocket_notifications: bool
    max_alerts_per_hour: int
