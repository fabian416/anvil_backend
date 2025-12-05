"""
Agent Telemetry entity - Performance metrics for Agent Squad agents.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_id import MessageId
from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.created_at import CreatedAt


@dataclass(eq=False, kw_only=True)
class AgentTelemetryId:
    """Agent Telemetry identifier."""
    value: uuid.UUID
    
    def __init__(self, value: uuid.UUID | str):
        if isinstance(value, str):
            value = uuid.UUID(value)
        object.__setattr__(self, 'value', value)
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgentTelemetryId):
            return False
        return self.value == other.value
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(eq=False, kw_only=True)
class AgentTelemetry(Entity[AgentTelemetryId]):
    """
    Agent telemetry: performance metrics for Agent Squad agents.
    
    Tracks:
    - Intent classification accuracy
    - Response latency
    - Token usage
    - Tool usage
    - Success rate
    """
    agent_type: AgentType
    conversation_id: Optional[ConversationId]
    message_id: Optional[MessageId]
    intent_classification: Optional[str]  # User intent (e.g., "swap_tokens", "analyze_risk")
    intent_confidence: Optional[float]  # 0.0-1.0
    latency_ms: int  # Response time in milliseconds
    tokens_used: Optional[int]  # LLM tokens consumed
    tools_used: list[str]  # Tools/APIs used (e.g., ["privy_wallet", "1inch_api"])
    success: bool  # Whether agent call succeeded
    error_message: Optional[str]  # Error details if failed
    created_at: CreatedAt
    
    @classmethod
    def create(
        cls,
        agent_type: AgentType,
        latency_ms: int,
        success: bool,
        conversation_id: Optional[ConversationId] = None,
        message_id: Optional[MessageId] = None,
        intent_classification: Optional[str] = None,
        intent_confidence: Optional[float] = None,
        tokens_used: Optional[int] = None,
        tools_used: Optional[list[str]] = None,
        error_message: Optional[str] = None,
    ) -> "AgentTelemetry":
        """Create new agent telemetry entry."""
        return cls(
            id_=AgentTelemetryId(uuid.uuid4()),
            agent_type=agent_type,
            conversation_id=conversation_id,
            message_id=message_id,
            intent_classification=intent_classification,
            intent_confidence=intent_confidence,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            tools_used=tools_used or [],
            success=success,
            error_message=error_message,
            created_at=CreatedAt.now(),
        )
    
    @property
    def is_successful(self) -> bool:
        """Check if agent call succeeded."""
        return self.success
    
    @property
    def has_high_confidence(self) -> bool:
        """Check if intent classification confidence is high (>0.85)."""
        return self.intent_confidence is not None and self.intent_confidence >= 0.85
    
    @property
    def is_fast(self) -> bool:
        """Check if response was fast (<2000ms)."""
        return self.latency_ms < 2000
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id_),
            "agent_type": self.agent_type.value,
            "conversation_id": str(self.conversation_id.value) if self.conversation_id else None,
            "message_id": str(self.message_id.value) if self.message_id else None,
            "intent_classification": self.intent_classification,
            "intent_confidence": self.intent_confidence,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "tools_used": self.tools_used,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.value.isoformat(),
        }
