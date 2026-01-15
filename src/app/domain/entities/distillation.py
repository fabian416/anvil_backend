"""
Distillation domain entities.

Represents request distillation concepts in the domain.
"""
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Optional
from uuid import UUID

from app.domain.chat.entities.message import Message


@dataclass
class DistillationRequest:
    """
    Request for distillation validation.
    
    Represents a user chat request that needs to be validated
    before being processed by the main conversation pipeline.
    """
    
    user_message: str
    conversation_history: List[Message]
    user_id: UUID
    conversation_id: UUID
    detected_language: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Set default timestamp."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


@dataclass
class DistillationResult:
    """
    Result of distillation validation.
    
    Contains the validation decision and metadata about the
    distillation process.
    """
    
    success: bool
    message: str
    reason: str
    confidence: float
    provider: str
    model: str
    detected_language: str
    latency_ms: float
    tokens_used: int
    cost_usd: float
    fallback_used: bool = False
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Set default timestamp and validate fields."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        
        # Validate confidence range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        
        # Validate cost
        if self.cost_usd < 0:
            raise ValueError(f"Cost cannot be negative, got {self.cost_usd}")
    
    def is_valid(self) -> bool:
        """Check if request should be processed."""
        return self.success and self.error is None
    
    def should_allow_fallback(self) -> bool:
        """Check if fallback to main processing is allowed."""
        # If distillation failed with error, allow fallback (fail-open)
        return self.error is not None
