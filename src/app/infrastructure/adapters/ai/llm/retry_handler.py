from typing import Optional, Tuple, Dict, Any
from app.infrastructure.adapters.ai.llm.strategy import LLMStrategy

# Vertex AI to DeepInfra model mapping (for fallback)
VERTEX_TO_DEEPINFRA_MODEL_MAP = {
    "gemini-2.0-flash": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gemini-2.0-flash-exp": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gemini-1.5-flash": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gemini-1.5-pro": "meta-llama/Meta-Llama-3.1-405B-Instruct",
    "gemini-2.0-pro": "meta-llama/Meta-Llama-3.1-405B-Instruct",
}

def _map_model_for_fallback(model_name: str, is_fallback_to_deepinfra: bool = False) -> str:
    """
    Map Vertex AI model names to DeepInfra model names when falling back.
    
    Args:
        model_name: Original model name
        is_fallback_to_deepinfra: Whether this is a fallback to DeepInfra
        
    Returns:
        Mapped model name if fallback, original otherwise
    """
    if is_fallback_to_deepinfra and model_name in VERTEX_TO_DEEPINFRA_MODEL_MAP:
        mapped = VERTEX_TO_DEEPINFRA_MODEL_MAP[model_name]
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 Mapping Vertex AI model '{model_name}' → DeepInfra model '{mapped}' for fallback")
        return mapped
    
    # If already a DeepInfra model or not a Vertex AI model, return as-is
    return model_name

class RetryHandler:
    """
    Chain of Responsibility Handler for LLM Retries.
    See: Chain of Responsibility Pattern (python-patterns package)
    """
    def __init__(self, strategy: LLMStrategy, next_handler: Optional['RetryHandler'] = None):
        self._strategy = strategy
        self._next_handler = next_handler
        # Detect if next handler is DeepInfra (for model mapping)
        self._is_deepinfra_fallback = False
        if next_handler is not None:
            try:
                strategy_class_name = next_handler._strategy.__class__.__name__
                self._is_deepinfra_fallback = 'DeepInfra' in strategy_class_name
            except Exception:
                # If we can't detect, assume it might be DeepInfra if current is Vertex AI
                current_strategy_name = self._strategy.__class__.__name__
                if 'Vertex' in current_strategy_name:
                    self._is_deepinfra_fallback = True

    async def handle(self, model_name: str, messages: list, **kwargs) -> Tuple[str, Dict[str, Any]]:
        try:
            return await self._strategy.generate(model_name, messages, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            error_str = str(e)
            is_rate_limit = (
                "429" in error_str or
                "rate limit" in error_str.lower() or
                "resource exhausted" in error_str.lower() or
                "RESOURCE_EXHAUSTED" in error_str
            )
            
            if is_rate_limit:
                logger.warning(f"⚠️ Rate limit (429) detected, falling back to DeepInfra...")
            else:
                logger.warning(f"LLM provider failed: {e}, trying fallback...")
            
            if self._next_handler:
                # Map model if falling back to DeepInfra
                fallback_model = _map_model_for_fallback(
                    model_name, 
                    is_fallback_to_deepinfra=self._is_deepinfra_fallback
                )
                return await self._next_handler.handle(fallback_model, messages, **kwargs)
            raise e
