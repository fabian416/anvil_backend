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
    
    Provider Priority:
    1. Vertex AI (Primary) - Google Gemini models
    2. DeepInfra (Fallback) - Open-source models
    """
    def __init__(self, config: Dict[str, str]):
        self._config = config
        self._strategies: Dict[LLMProvider, LLMStrategy] = {}

    def get_strategy(self, provider: LLMProvider) -> LLMStrategy:
        if provider in self._strategies:
            return self._strategies[provider]
        
        # Primary: Vertex AI
        if provider == LLMProvider.VERTEX:
            # TODO: Implement VertexStrategy adapter
            # For now, Vertex AI is used via the new orchestrator system
            # This factory is for the legacy LLM Gateway system
            # When VertexStrategy is implemented, uncomment:
            # strategy = VertexStrategy(
            #     project_id=self._config.get("VERTEX_AI_PROJECT_ID", ""),
            #     credentials_path=self._config.get("VERTEX_AI_CREDENTIALS_PATH", ""),
            # )
            # self._strategies[provider] = strategy
            # return strategy
            raise NotImplementedError(
                "Vertex AI strategy not yet implemented for legacy LLM Gateway. "
                "Use the new LLM Orchestrator system or DeepInfra as fallback."
            )
        
        # Fallback: DeepInfra
        if provider == LLMProvider.DEEPINFRA:
            strategy = DeepInfraStrategy(api_key=self._config.get("DEEPINFRA_API_KEY", ""))
            self._strategies[provider] = strategy
            return strategy
            
        # Fallback for unimplemented providers in this phase
        raise NotImplementedError(f"Provider {provider} not implemented yet")
