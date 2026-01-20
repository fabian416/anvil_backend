from typing import Dict
from app.domain.enums.ai.llm_provider import LLMProvider
from app.infrastructure.adapters.ai.llm.strategy import LLMStrategy
from app.infrastructure.adapters.ai.llm.deepinfra import DeepInfraStrategy
from app.infrastructure.adapters.ai.llm.vertex import VertexStrategy
# from app.infrastructure.adapters.ai.llm.bedrock import BedrockStrategy (Future)

class LLMProviderFactory:
    """
    Factory for creating LLM Strategies.
    See: Factory Pattern (python-patterns package)
    
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
            project_id = self._config.get("VERTEX_AI_PROJECT_ID", "")
            if not project_id:
                raise ValueError("VERTEX_AI_PROJECT_ID is required for Vertex AI")
            
            strategy = VertexStrategy(
                project_id=project_id,
                location=self._config.get("VERTEX_AI_LOCATION", "us-central1"),
                api_key=self._config.get("VERTEX_AI_API_KEY", None),
                credentials_path=self._config.get("VERTEX_AI_CREDENTIALS_PATH", None),
            )
            self._strategies[provider] = strategy
            return strategy
        
        # Fallback: DeepInfra
        if provider == LLMProvider.DEEPINFRA:
            strategy = DeepInfraStrategy(api_key=self._config.get("DEEPINFRA_API_KEY", ""))
            self._strategies[provider] = strategy
            return strategy
            
        # Fallback for unimplemented providers in this phase
        raise NotImplementedError(f"Provider {provider} not implemented yet")
