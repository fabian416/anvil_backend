"""
Conversation analytics domain entity.

Tracks metrics and statistics for chat conversations including:
- Message counts and timing
- Agent usage and performance
- Cost tracking
- Quality metrics
- Token usage
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Optional, Any
from uuid import UUID


@dataclass
class ConversationAnalytics:
    """
    Analytics entity for a conversation.

    Aggregates metrics and statistics for a single conversation,
    including message counts, agent usage, costs, and quality scores.
    """

    id: UUID
    conversation_id: UUID
    user_id: UUID

    # Message metrics
    message_count: int = 0
    user_message_count: int = 0
    agent_message_count: int = 0

    # Agent usage (dict mapping agent names to usage data)
    agent_usage: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Response time metrics (milliseconds)
    avg_response_time_ms: Optional[float] = None
    median_response_time_ms: Optional[float] = None
    p95_response_time_ms: Optional[float] = None
    min_response_time_ms: Optional[float] = None
    max_response_time_ms: Optional[float] = None

    # Cost metrics (USD)
    total_cost_usd: float = 0.0
    avg_cost_per_message: float = 0.0
    cost_by_agent: Dict[str, float] = field(default_factory=dict)

    # Quality metrics (0.0 to 1.0)
    sentiment_score: Optional[float] = None
    quality_score: Optional[float] = None
    user_satisfaction_score: Optional[float] = None

    # Token usage
    total_tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    # Timestamps
    first_message_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
