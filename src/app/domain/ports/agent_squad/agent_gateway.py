"""
Agent Gateway port - Base interface for all agents.
"""

from typing import Protocol
from dataclasses import dataclass, field

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.value_objects.chat.source_info import SourceInfo


@dataclass
class AgentResponse:
    """
    Response from agent execution.
    
    Contains:
    - content: Agent response text
    - agent_type: Which agent generated the response
    - tools_used: List of tools/APIs used (legacy, for backward compatibility)
    - sources: List of detailed source information (NEW)
    - metadata: Additional metadata (tokens, latency, etc.)
    """
    content: str
    agent_type: AgentType
    tools_used: list[str]
    sources: list[SourceInfo] = field(default_factory=list)  # NEW: Detailed sources
    metadata: dict = field(default_factory=dict)
    
    @property
    def tokens_used(self) -> int | None:
        """Get tokens used (if available)."""
        return self.metadata.get("tokens_used")
    
    @property
    def latency_ms(self) -> int | None:
        """Get latency in milliseconds (if available)."""
        return self.metadata.get("latency_ms")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "content": self.content,
            "agent_type": self.agent_type.value,
            "tools_used": self.tools_used,
            "sources": [s.to_dict() for s in self.sources],
            "metadata": self.metadata,
        }


class AgentGateway(Protocol):
    """
    Agent Gateway port - Base interface for all agents.
    
    All 18 agents must implement this interface.
    
    Responsibilities:
    - Execute agent with message and context
    - Return structured response
    - Handle errors gracefully
    
    Implementing adapters:
    - ChatAgentOpenAI
    - HunterAIAgentOpenAI
    - ResearchAgentPerplexity
    - ExecutionAgentPrivy
    - ... (all 18 agents)
    """
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        ...
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute agent with message and context.
        
        Args:
            conversation_id: Conversation identifier
            message: User message
            conversation_context: Conversation history and metadata
            
        Returns:
            AgentResponse with content, tools used, and metadata
            
        Raises:
            AgentExecutionError: If agent execution fails
        """
        ...
    
    async def is_available(self) -> bool:
        """
        Check if agent is available (e.g., API accessible).
        
        Returns:
            True if agent can execute, False otherwise
        """
        ...
