"""
Conversation context entity for agent memory.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4


@dataclass
class ConversationContext:
    """
    Represents conversation context for agent memory.
    
    Stores conversation state, user preferences, and historical patterns
    to enable intelligent multi-turn conversations.
    """
    
    id: UUID = field(default_factory=uuid4)
    conversation_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    
    # Context data
    current_topic: Optional[str] = None
    recent_intents: List[str] = field(default_factory=list)
    mentioned_tokens: List[str] = field(default_factory=list)
    mentioned_protocols: List[str] = field(default_factory=list)
    active_positions: List[Dict[str, Any]] = field(default_factory=list)
    
    # User preferences (learned over time)
    preferred_slippage: Optional[float] = None
    preferred_leverage: Optional[int] = None
    risk_tolerance: Optional[str] = None  # "low", "medium", "high"
    preferred_chains: List[str] = field(default_factory=list)
    
    # Historical patterns
    frequent_operations: Dict[str, int] = field(default_factory=dict)
    typical_trade_sizes: Dict[str, float] = field(default_factory=dict)
    interaction_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def add_intent(self, intent: str, max_recent: int = 10) -> None:
        """
        Add an intent to recent history.
        
        Args:
            intent: Intent type
            max_recent: Maximum number of recent intents to keep
        """
        self.recent_intents.append(intent)
        if len(self.recent_intents) > max_recent:
            self.recent_intents = self.recent_intents[-max_recent:]
        
        # Update frequent operations
        self.frequent_operations[intent] = self.frequent_operations.get(intent, 0) + 1
        self.interaction_count += 1
        self.updated_at = datetime.now(UTC)
    
    def add_mentioned_token(self, token: str) -> None:
        """Add a token to mentioned tokens (deduplicated)."""
        if token not in self.mentioned_tokens:
            self.mentioned_tokens.append(token)
        self.updated_at = datetime.now(UTC)
    
    def add_mentioned_protocol(self, protocol: str) -> None:
        """Add a protocol to mentioned protocols (deduplicated)."""
        if protocol not in self.mentioned_protocols:
            self.mentioned_protocols.append(protocol)
        self.updated_at = datetime.now(UTC)
    
    def update_preference(self, key: str, value: Any) -> None:
        """
        Update a user preference.
        
        Args:
            key: Preference key (e.g., 'preferred_slippage')
            value: New value
        """
        if hasattr(self, key):
            setattr(self, key, value)
            self.updated_at = datetime.now(UTC)
    
    def get_dominant_intent(self) -> Optional[str]:
        """
        Get the most frequent intent type.
        
        Returns:
            Most common intent or None
        """
        if not self.frequent_operations:
            return None
        
        return max(self.frequent_operations.items(), key=lambda x: x[1])[0]
    
    def is_experienced_user(self, threshold: int = 20) -> bool:
        """
        Check if user is experienced based on interaction count.
        
        Args:
            threshold: Minimum interactions to be considered experienced
        
        Returns:
            True if experienced
        """
        return self.interaction_count >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "current_topic": self.current_topic,
            "recent_intents": self.recent_intents,
            "mentioned_tokens": self.mentioned_tokens,
            "mentioned_protocols": self.mentioned_protocols,
            "active_positions": self.active_positions,
            "preferred_slippage": self.preferred_slippage,
            "preferred_leverage": self.preferred_leverage,
            "risk_tolerance": self.risk_tolerance,
            "preferred_chains": self.preferred_chains,
            "frequent_operations": self.frequent_operations,
            "typical_trade_sizes": self.typical_trade_sizes,
            "interaction_count": self.interaction_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
