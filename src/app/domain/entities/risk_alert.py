"""Risk alert domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class RiskAlert:
    """Domain entity for protocol risk alerts."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)
    protocol_id: UUID = field(default=None)
    protocol_name: str = ""
    alert_type: str = "risk_increase"  # risk_increase/anomaly/critical/dependency
    severity: str = "MEDIUM"  # LOW/MEDIUM/HIGH/CRITICAL
    message: str = ""
    details: Dict = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    # Risk metrics
    current_risk_score: float = 0.0
    previous_risk_score: Optional[float] = None
    risk_change: Optional[float] = None
    
    # Status
    acknowledged: bool = False
    dismissed: bool = False
    acted_upon: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def acknowledge(self) -> None:
        """Mark alert as acknowledged by user."""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()

    def dismiss(self) -> None:
        """Dismiss alert (mark as not relevant)."""
        self.dismissed = True

    def mark_acted_upon(self) -> None:
        """Mark that user took action on this alert."""
        self.acted_upon = True
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if alert has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def should_notify(self) -> bool:
        """Determine if alert should trigger notification."""
        # Don't notify if already acknowledged or dismissed
        if self.acknowledged or self.dismissed:
            return False

        # Don't notify if expired
        if self.is_expired():
            return False

        # Notify for HIGH and CRITICAL always
        if self.severity in ["HIGH", "CRITICAL"]:
            return True

        # Notify for MEDIUM if risk change is significant
        if self.severity == "MEDIUM" and self.risk_change:
            return abs(self.risk_change) >= 1.0  # >1 point change

        return False


@dataclass
class AlertSubscription:
    """User's alert subscription preferences."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)
    
    # Alert type preferences
    risk_alerts_enabled: bool = True
    anomaly_alerts_enabled: bool = True
    protocol_update_alerts_enabled: bool = True
    price_alerts_enabled: bool = True
    
    # Severity threshold
    min_severity: str = "MEDIUM"  # Only alert for this severity and above
    
    # Protocol-specific
    subscribed_protocols: List[UUID] = field(default_factory=list)
    excluded_protocols: List[UUID] = field(default_factory=list)
    
    # Notification channels
    push_notifications: bool = True
    email_notifications: bool = False
    websocket_notifications: bool = True
    
    # Throttling
    max_alerts_per_hour: int = 10
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def should_alert_for_severity(self, severity: str) -> bool:
        """Check if should alert for given severity."""
        severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        try:
            min_idx = severity_order.index(self.min_severity)
            alert_idx = severity_order.index(severity)
            return alert_idx >= min_idx
        except ValueError:
            return True  # Default to alerting if invalid severity

    def should_alert_for_protocol(self, protocol_id: UUID) -> bool:
        """Check if should alert for specific protocol."""
        # If excluded, don't alert
        if protocol_id in self.excluded_protocols:
            return False
        
        # If subscription list is empty, alert for all
        if not self.subscribed_protocols:
            return True
        
        # Only alert for subscribed protocols
        return protocol_id in self.subscribed_protocols
