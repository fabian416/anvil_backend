"""
WebSocket message schemas.

Defines structured message types for real-time chat communication
following the presentation layer's responsibility for request/response
serialization.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """
    WebSocket message type enumeration.

    Defines all possible message types for client-server communication.
    """

    # Client → Server
    MESSAGE = "message"
    PING = "ping"

    # Server → Client
    STREAM = "stream"
    TYPING = "typing"
    VOTING_UPDATE = "voting_update"
    DEBATE_PHASE = "debate_phase"
    MESSAGE_COMPLETE = "message_complete"
    PROGRESS = "progress"
    ERROR = "error"
    PONG = "pong"
    SYSTEM = "system"
    INTENT_SUGGESTION = "intent_suggestion"


class DebatePhase(str, Enum):
    """
    Multi-agent debate phase enumeration.

    Represents different stages of the multi-agent consensus process.
    """

    INITIAL_ANALYSIS = "initial_analysis"
    VOTING = "voting"
    DEBATE = "debate"
    CONSENSUS = "consensus"
    FINAL_RESPONSE = "final_response"


class TypingIndicatorAction(str, Enum):
    """Typing indicator actions."""

    STARTED = "started"
    STOPPED = "stopped"


# =============================================================================
# CLIENT → SERVER MESSAGES
# =============================================================================


class ClientMessage(BaseModel):
    """
    Base client message schema.

    All messages from client must have a type field.
    """

    type: WebSocketMessageType


class ChatMessageRequest(ClientMessage):
    """
    Client chat message request.

    Sent when user sends a message in the conversation.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.MESSAGE,
        description="Message type",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content",
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Conversation ID (creates new if not provided)",
    )


class PingMessage(ClientMessage):
    """
    Client heartbeat ping.

    Used for connection health monitoring.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.PING,
        description="Message type",
    )


# =============================================================================
# SERVER → CLIENT MESSAGES
# =============================================================================


class ServerMessage(BaseModel):
    """
    Base server message schema.

    All messages from server include type and timestamp.
    """

    type: WebSocketMessageType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StreamTokenMessage(ServerMessage):
    """
    Streaming token message.

    Sent during agent response streaming (token-by-token).
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.STREAM,
        description="Message type",
    )
    content: str = Field(..., description="Token or content chunk")
    message_id: Optional[UUID] = Field(
        default=None,
        description="Associated message ID",
    )


class TypingIndicatorMessage(ServerMessage):
    """
    Agent typing indicator.

    Notifies client that an agent is typing/processing.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.TYPING,
        description="Message type",
    )
    action: TypingIndicatorAction = Field(
        ...,
        description="Typing action (started/stopped)",
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Name of typing agent",
    )


class VotingUpdateMessage(ServerMessage):
    """
    Multi-agent voting progress update.

    Sent during multi-agent voting to show vote counts and progress.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.VOTING_UPDATE,
        description="Message type",
    )
    total_agents: int = Field(..., description="Total agents participating")
    votes_received: int = Field(..., description="Number of votes received")
    vote_summary: Optional[Dict[str, int]] = Field(
        default=None,
        description="Vote breakdown by option",
    )
    leading_option: Optional[str] = Field(
        default=None,
        description="Current leading vote option",
    )


class DebatePhaseMessage(ServerMessage):
    """
    Debate phase transition notification.

    Sent when multi-agent debate moves to a new phase.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.DEBATE_PHASE,
        description="Message type",
    )
    phase: DebatePhase = Field(..., description="Current debate phase")
    description: str = Field(..., description="Human-readable phase description")
    participating_agents: Optional[list[str]] = Field(
        default=None,
        description="Agents participating in this phase",
    )
    round_number: Optional[int] = Field(
        default=None,
        description="Current debate round number",
    )


class MessageCompleteMessage(ServerMessage):
    """
    Complete message notification.

    Sent when agent finishes streaming a message.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.MESSAGE_COMPLETE,
        description="Message type",
    )
    message_id: UUID = Field(..., description="Completed message ID")
    content: str = Field(..., description="Full message content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Message metadata (agent, tools used, etc.)",
    )


class ProgressMessage(ServerMessage):
    """
    Agent progress update.

    Sent during agent execution to show progress (tool calls, thinking, etc.).
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.PROGRESS,
        description="Message type",
    )
    status: str = Field(..., description="Progress status (thinking, tool_call, etc.)")
    message: str = Field(..., description="Human-readable progress message")
    tool: Optional[str] = Field(default=None, description="Tool being used")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional progress data",
    )


class ErrorMessage(ServerMessage):
    """
    Error notification.

    Sent when an error occurs during processing.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.ERROR,
        description="Message type",
    )
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
    )


class PongMessage(ServerMessage):
    """
    Server heartbeat response.

    Response to client ping for connection health monitoring.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.PONG,
        description="Message type",
    )


class SystemMessage(ServerMessage):
    """
    System notification.

    General system messages (connection status, etc.).
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.SYSTEM,
        description="Message type",
    )
    message: str = Field(..., description="System message")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional system data",
    )


class IntentSuggestionMessage(ServerMessage):
    """
    Intent detection suggestion.

    Sent when user is typing to provide real-time intent detection,
    agent suggestions, and autocomplete recommendations.
    """

    type: WebSocketMessageType = Field(
        default=WebSocketMessageType.INTENT_SUGGESTION,
        description="Message type",
    )
    intent_type: str = Field(..., description="Detected intent type")
    confidence: float = Field(..., description="Intent confidence score (0-1)")
    confidence_level: str = Field(..., description="Confidence level (high/medium/low)")
    suggested_agent: Optional[str] = Field(
        default=None,
        description="Suggested agent name for this intent",
    )
    agent_reasoning: Optional[str] = Field(
        default=None,
        description="Why this agent was suggested",
    )
    extracted_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities (protocols, tokens, amounts, etc.)",
    )
    autocomplete_suggestions: list[str] = Field(
        default_factory=list,
        description="Autocomplete suggestions for current input",
    )
    is_high_confidence: bool = Field(
        default=False,
        description="Whether confidence is high enough to auto-suggest",
    )
