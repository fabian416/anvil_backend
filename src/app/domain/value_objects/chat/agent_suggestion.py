"""
Agent suggestion value object for suggesting appropriate agents.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgentSuggestion:
    """
    Suggestion for which agent to use for a query.

    Provides agent recommendation with reasoning and confidence.
    """

    agent_name: str
    confidence: float
    reasoning: str
    agent_description: Optional[str] = None
    estimated_response_time_seconds: Optional[int] = None

    @classmethod
    def create(
        cls,
        agent_name: str,
        confidence: float,
        reasoning: str,
        agent_description: Optional[str] = None,
        estimated_response_time_seconds: Optional[int] = None,
    ) -> "AgentSuggestion":
        """
        Create agent suggestion.

        Args:
            agent_name: Name of suggested agent
            confidence: Confidence score (0.0 - 1.0)
            reasoning: Why this agent is recommended
            agent_description: Brief description of what the agent does
            estimated_response_time_seconds: Expected response time

        Returns:
            AgentSuggestion instance
        """
        return cls(
            agent_name=agent_name,
            confidence=confidence,
            reasoning=reasoning,
            agent_description=agent_description,
            estimated_response_time_seconds=estimated_response_time_seconds,
        )

    @property
    def is_high_confidence(self) -> bool:
        """Check if suggestion has high confidence (>= 0.8)."""
        return self.confidence >= 0.8

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "agent_description": self.agent_description,
            "estimated_response_time_seconds": self.estimated_response_time_seconds,
            "is_high_confidence": self.is_high_confidence,
        }


@dataclass(frozen=True)
class AutocompleteSuggestion:
    """
    Autocomplete suggestion for partial user input.

    Provides intelligent completion suggestions as user types.
    """

    completion_text: str
    display_text: str
    confidence: float
    suggestion_type: str  # "protocol", "wallet", "action", "generic"
    icon: Optional[str] = None
    metadata: Optional[dict] = None

    @classmethod
    def create(
        cls,
        completion_text: str,
        display_text: str,
        confidence: float,
        suggestion_type: str,
        icon: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "AutocompleteSuggestion":
        """
        Create autocomplete suggestion.

        Args:
            completion_text: Full text to insert
            display_text: Text to show in suggestion dropdown
            confidence: Relevance score (0.0 - 1.0)
            suggestion_type: Type of suggestion
            icon: Optional icon identifier
            metadata: Additional suggestion metadata

        Returns:
            AutocompleteSuggestion instance
        """
        return cls(
            completion_text=completion_text,
            display_text=display_text,
            confidence=confidence,
            suggestion_type=suggestion_type,
            icon=icon,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "completion_text": self.completion_text,
            "display_text": self.display_text,
            "confidence": self.confidence,
            "suggestion_type": self.suggestion_type,
            "icon": self.icon,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ConversationMatch:
    """
    Matching conversation from history.

    Represents a similar past conversation that might help the user.
    """

    conversation_id: str
    title: str
    similarity_score: float
    snippet: str
    created_at: str
    message_count: int
    was_helpful: Optional[bool] = None

    @classmethod
    def create(
        cls,
        conversation_id: str,
        title: str,
        similarity_score: float,
        snippet: str,
        created_at: str,
        message_count: int,
        was_helpful: Optional[bool] = None,
    ) -> "ConversationMatch":
        """
        Create conversation match.

        Args:
            conversation_id: ID of matching conversation
            title: Conversation title
            similarity_score: Similarity score (0.0 - 1.0)
            snippet: Preview of conversation content
            created_at: When conversation was created
            message_count: Number of messages in conversation
            was_helpful: Whether user found it helpful (if known)

        Returns:
            ConversationMatch instance
        """
        return cls(
            conversation_id=conversation_id,
            title=title,
            similarity_score=similarity_score,
            snippet=snippet,
            created_at=created_at,
            message_count=message_count,
            was_helpful=was_helpful,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "similarity_score": self.similarity_score,
            "snippet": self.snippet,
            "created_at": self.created_at,
            "message_count": self.message_count,
            "was_helpful": self.was_helpful,
        }
