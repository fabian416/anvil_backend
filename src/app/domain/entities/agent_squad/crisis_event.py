"""
Crisis Event entity - Emergency response logs.
"""

from dataclasses import dataclass
from typing import Any
from decimal import Decimal
from datetime import datetime, UTC
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.created_at import CreatedAt


@dataclass(eq=False, kw_only=True)
class CrisisEventId:
    """Crisis Event identifier."""
    value: uuid.UUID
    
    def __init__(self, value: uuid.UUID | str):
        if isinstance(value, str):
            value = uuid.UUID(value)
        object.__setattr__(self, 'value', value)
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CrisisEventId):
            return False
        return self.value == other.value
    
    def __str__(self) -> str:
        return str(self.value)


class CrisisEventType:
    """Crisis event type enum."""
    EXPLOIT = "exploit"
    DEPEG = "depeg"
    FLASH_CRASH = "flash_crash"
    LIQUIDATION_RISK = "liquidation_risk"
    BRIDGE_EXPLOIT = "bridge_exploit"
    ORACLE_MANIPULATION = "oracle_manipulation"


class CrisisSeverity:
    """Crisis severity enum."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CrisisAction:
    """Single crisis response action."""
    action: str  # Action taken (e.g., "emergency_withdrawal", "circuit_breaker")
    timestamp: datetime
    result: str  # "success" or "failed"
    details: dict[str, Any] | None = None
    
    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "result": self.result,
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CrisisAction":
        return cls(
            action=data["action"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            result=data["result"],
            details=data.get("details"),
        )


@dataclass
class PositionSaved:
    """Position saved during crisis."""
    protocol: str
    amount_usd: Decimal
    action: str  # "withdrawn", "migrated", "collateral_added"
    
    def to_dict(self) -> dict:
        return {
            "protocol": self.protocol,
            "amount_usd": float(self.amount_usd),
            "action": self.action,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PositionSaved":
        return cls(
            protocol=data["protocol"],
            amount_usd=Decimal(str(data["amount_usd"])),
            action=data["action"],
        )


@dataclass(eq=False, kw_only=True)
class CrisisEvent(Entity[CrisisEventId]):
    """
    Crisis event: emergency response log.
    
    Enterprise feature for crisis management:
    - Real-time exploit detection (Forta, OpenZeppelin Defender)
    - Circuit breaker (auto-pause trading)
    - Emergency withdrawal (30-second response)
    - Multi-sig fast-track
    - Fund migration (to safe protocols)
    - Post-crisis analysis
    """
    user_id: UserId
    event_type: str  # "exploit", "depeg", "flash_crash", etc.
    protocol_name: str  # Affected protocol (e.g., "Aave V2")
    severity: str  # "critical", "high", "medium", "low"
    user_exposure_usd: Decimal  # User's exposure in USD
    response_time_ms: int  # Crisis Manager response time (milliseconds)
    actions_taken: list[CrisisAction]  # Automated actions
    positions_saved: list[PositionSaved]  # Positions secured
    losses_prevented_usd: Decimal  # Estimated losses prevented
    crisis_resolved: bool  # Whether crisis was fully resolved
    resolved_at: datetime | None
    created_at: CreatedAt
    
    @classmethod
    def create(
        cls,
        user_id: UserId,
        event_type: str,
        protocol_name: str,
        severity: str,
        user_exposure_usd: Decimal,
        response_time_ms: int,
    ) -> "CrisisEvent":
        """Create new crisis event."""
        return cls(
            id_=CrisisEventId(uuid.uuid4()),
            user_id=user_id,
            event_type=event_type,
            protocol_name=protocol_name,
            severity=severity,
            user_exposure_usd=user_exposure_usd,
            response_time_ms=response_time_ms,
            actions_taken=[],
            positions_saved=[],
            losses_prevented_usd=Decimal("0"),
            crisis_resolved=False,
            resolved_at=None,
            created_at=CreatedAt.now(),
        )
    
    def add_action(
        self,
        action: str,
        result: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add crisis response action."""
        crisis_action = CrisisAction(
            action=action,
            timestamp=datetime.now(UTC),
            result=result,
            details=details,
        )
        self.actions_taken.append(crisis_action)
    
    def add_position_saved(
        self,
        protocol: str,
        amount_usd: Decimal,
        action: str,
    ) -> None:
        """Add saved position."""
        position = PositionSaved(
            protocol=protocol,
            amount_usd=amount_usd,
            action=action,
        )
        self.positions_saved.append(position)
        
        # Add to losses prevented
        self.losses_prevented_usd += amount_usd
    
    def resolve(self) -> None:
        """Mark crisis as resolved."""
        self.crisis_resolved = True
        self.resolved_at = datetime.now(UTC)
    
    @property
    def is_critical(self) -> bool:
        """Check if crisis is critical severity."""
        return self.severity == CrisisSeverity.CRITICAL
    
    @property
    def is_high_severity(self) -> bool:
        """Check if crisis is high severity."""
        return self.severity in [CrisisSeverity.CRITICAL, CrisisSeverity.HIGH]
    
    @property
    def total_actions(self) -> int:
        """Get total number of actions taken."""
        return len(self.actions_taken)
    
    @property
    def successful_actions(self) -> int:
        """Get number of successful actions."""
        return sum(1 for action in self.actions_taken if action.result == "success")
    
    @property
    def total_positions_saved(self) -> int:
        """Get number of positions saved."""
        return len(self.positions_saved)
    
    @property
    def was_fast_response(self) -> bool:
        """Check if response was fast (<5000ms)."""
        return self.response_time_ms < 5000
    
    @property
    def was_ultra_fast_response(self) -> bool:
        """Check if response was ultra-fast (<1000ms)."""
        return self.response_time_ms < 1000
    
    @property
    def prevention_rate(self) -> float:
        """Calculate loss prevention rate (0.0-1.0)."""
        if self.user_exposure_usd == 0:
            return 1.0
        return min(1.0, float(self.losses_prevented_usd / self.user_exposure_usd))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id_),
            "user_id": str(self.user_id.value),
            "event_type": self.event_type,
            "protocol_name": self.protocol_name,
            "severity": self.severity,
            "user_exposure_usd": float(self.user_exposure_usd),
            "response_time_ms": self.response_time_ms,
            "actions_taken": [action.to_dict() for action in self.actions_taken],
            "positions_saved": [pos.to_dict() for pos in self.positions_saved],
            "losses_prevented_usd": float(self.losses_prevented_usd),
            "crisis_resolved": self.crisis_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.value.isoformat(),
        }
