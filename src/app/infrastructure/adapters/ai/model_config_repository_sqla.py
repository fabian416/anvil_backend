from typing import List
from sqlalchemy import select

from app.domain.ports.ai.model_config_repository import ModelConfigRepository
from app.domain.entities.ai.model_config import ModelConfig
from app.domain.enums.ai.llm_provider import LLMProvider
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.adapters.types import MainAsyncSession

class ModelConfigRepositorySqla(ModelConfigRepository):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def get_available_models(self) -> List[ModelConfig]:
        ModelsTable = mapping_registry.metadata.tables["models"] # type: ignore
        stmt = select(ModelsTable).where(ModelsTable.c.is_available == True)
        result = await self._session.execute(stmt)
        # Transform rows to entities (omitted for brevity)
        return [] 

    async def get_by_provider_and_name(self, provider: LLMProvider, name: str) -> ModelConfig | None:
        ModelsTable = mapping_registry.metadata.tables["models"] # type: ignore
        stmt = select(ModelsTable).where(
            ModelsTable.c.provider == provider.value,
            ModelsTable.c.model_name == name
        )
        return await self._session.scalar(stmt)

    async def get_default_model(self, provider: LLMProvider) -> ModelConfig | None:
        ModelsTable = mapping_registry.metadata.tables["models"] # type: ignore
        stmt = select(ModelsTable).where(
            ModelsTable.c.provider == provider.value,
            ModelsTable.c.is_default == True
        )
        return await self._session.scalar(stmt)
