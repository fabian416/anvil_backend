from typing import Optional, Tuple, Dict, Any
from app.infrastructure.adapters.ai.llm.strategy import LLMStrategy

class RetryHandler:
    """
    Chain of Responsibility Handler for LLM Retries.
    See: Chain of Responsibility Pattern (python-patterns package)
    """
    def __init__(self, strategy: LLMStrategy, next_handler: Optional['RetryHandler'] = None):
        self._strategy = strategy
        self._next_handler = next_handler

    async def handle(self, model_name: str, messages: list, **kwargs) -> Tuple[str, Dict[str, Any]]:
        try:
            return await self._strategy.generate(model_name, messages, **kwargs)
        except Exception as e:
            print(f"Handler failed: {e}")
            if self._next_handler:
                return await self._next_handler.handle(model_name, messages, **kwargs)
            raise e
