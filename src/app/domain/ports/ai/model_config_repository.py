from typing import Protocol
from typing import List

from app.domain.entities.ai.model_config import ModelConfig
from app.domain.entities.ai.llm_conversation import ModelId
from app.domain.enums.ai.llm_provider import LLMProvider

class ModelConfigRepository(Protocol):
    async def get_available_models(self) -> List[ModelConfig]:
        ...

    async def get_by_provider_and_name(self, provider: LLMProvider, name: str) -> ModelConfig | None:
        ...
        
    async def get_default_model(self, provider: LLMProvider) -> ModelConfig | None:
        ...
