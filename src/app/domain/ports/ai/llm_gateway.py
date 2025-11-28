from typing import Protocol, List, Dict, Any, Optional
from app.domain.entities.ai.llm_conversation import LLMConversation
from app.domain.enums.ai.llm_provider import LLMProvider

class LLMGateway(Protocol):
    """
    Port for interacting with LLM providers.
    This defines the contract for our multi-model gateway.
    """
    async def generate_response(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generates a text response from the LLM.
        """
        ...

    async def generate_response_with_metadata(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates response and returns metadata (tokens, cost, latency).
        """
        ...
