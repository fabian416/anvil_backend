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
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Routes the message to the appropriate agent and returns the response.
        """
        ...
