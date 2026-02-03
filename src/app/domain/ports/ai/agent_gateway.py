from typing import Protocol, Dict, Any, Optional
from uuid import UUID


class AgentGateway(Protocol):
    """
    Port for the Agent Orchestration Layer.
    """

    async def process_message(
        self,
        user_id: UUID,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggested_model: Optional[str] = None,
        suggested_agent: Optional[str] = None,
    ) -> str:
        """
        Routes the message to the appropriate agent and returns the response.

        Args:
            user_id: User identifier
            session_id: Session/conversation identifier
            message: User message content
            context: Optional context dictionary
            suggested_model: Optional model tier hint from distillation (e.g., "gpt-3.5-turbo", "gpt-4")
            suggested_agent: Optional agent hint from distillation (e.g., "trading", "portfolio")

        Returns:
            Agent response text
        """
        ...
