from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class LLMStrategy(ABC):
    """
    Abstract Strategy for LLM Providers.
    See: Strategy Pattern (python-patterns package)
    """

    @abstractmethod
    async def generate(
        self, model_name: str, messages: List[Dict[str, str]], **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Returns (response_text, metadata)
        Metadata must include: input_tokens, output_tokens, latency_ms, cost_usd
        """
        pass
