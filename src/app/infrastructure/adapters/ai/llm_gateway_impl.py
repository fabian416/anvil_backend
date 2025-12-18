from typing import List, Dict, Any, Optional
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.domain.enums.ai.llm_provider import LLMProvider
from app.infrastructure.factories.ai.llm_provider_factory import LLMProviderFactory
from app.infrastructure.adapters.ai.llm.retry_handler import RetryHandler

class LLMGatewayImpl(LLMGateway):
    def __init__(self, factory: LLMProviderFactory):
        self._factory = factory

    async def generate_response(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        text, _ = await self.generate_response_with_metadata(
            model_name, messages, temperature, max_tokens, tools
        )
        return text

    async def generate_response_with_metadata(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        
        # Provider Priority: Vertex AI (Primary) -> DeepInfra (Fallback)
        # Try Vertex AI first, fallback to DeepInfra if not available/implemented
        primary_strategy = None
        
        try:
            primary_strategy = self._factory.get_strategy(LLMProvider.VERTEX)
        except (NotImplementedError, KeyError, ValueError) as e:
            # Fallback to DeepInfra if Vertex AI not implemented/configured
            # This is expected until VertexStrategy adapter is implemented
            try:
                primary_strategy = self._factory.get_strategy(LLMProvider.DEEPINFRA)
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Failed to initialize LLM providers. "
                    f"Vertex AI: {str(e)}, DeepInfra: {str(fallback_error)}"
                ) from fallback_error
        
        if primary_strategy is None:
            raise RuntimeError("No LLM provider strategy available")
        
        chain = RetryHandler(primary_strategy)
        
        return await chain.handle(
            model_name, 
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens
        )
