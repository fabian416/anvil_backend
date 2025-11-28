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
        
        # For MVP, we hardcode the chain: DeepInfra -> None
        # In real implementation, we would look up AgentModelConfig to build the chain
        primary_strategy = self._factory.get_strategy(LLMProvider.DEEPINFRA)
        
        chain = RetryHandler(primary_strategy)
        
        return await chain.handle(
            model_name, 
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens
        )
