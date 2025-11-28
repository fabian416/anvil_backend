from typing import Dict
from app.domain.enums.ai.llm_provider import LLMProvider
from app.infrastructure.adapters.ai.llm.strategy import LLMStrategy
from app.infrastructure.adapters.ai.llm.deepinfra import DeepInfraStrategy
# from app.infrastructure.adapters.ai.llm.vertex import VertexStrategy (Future)
# from app.infrastructure.adapters.ai.llm.bedrock import BedrockStrategy (Future)

class LLMProviderFactory:
    """
    Factory for creating LLM Strategies.
    See libs/python-patterns/patterns/creational/factory.py
    """
    def __init__(self, config: Dict[str, str]):
        self._config = config
        self._strategies: Dict[LLMProvider, LLMStrategy] = {}

    def get_strategy(self, provider: LLMProvider) -> LLMStrategy:
        if provider in self._strategies:
            return self._strategies[provider]
            
        if provider == LLMProvider.DEEPINFRA:
            strategy = DeepInfraStrategy(api_key=self._config.get("DEEPINFRA_API_KEY", ""))
            self._strategies[provider] = strategy
            return strategy
            
        # Fallback for unimplemented providers in this phase
        raise NotImplementedError(f"Provider {provider} not implemented yet")
