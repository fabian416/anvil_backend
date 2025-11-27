from sqlalchemy import select
from app.domain.ports.ai.agent_execution_repository import AgentExecutionRepository
from app.domain.entities.ai.agent_execution import AgentExecution, AgentExecutionId
from app.domain.entities.ai.agent_task import AgentTask
from app.domain.entities.ai.agent_tool_usage import AgentToolUsage
from app.infrastructure.adapters.types import MainAsyncSession

class AgentExecutionRepositorySqla(AgentExecutionRepository):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def save_execution(self, execution: AgentExecution) -> None:
        self._session.add(execution)
        await self._session.flush()

    async def get_execution_by_id(self, id: AgentExecutionId) -> AgentExecution | None:
        # Placeholder for actual implementation
        return await self._session.get(AgentExecution, id.value)

    async def save_task(self, task: AgentTask) -> None:
        self._session.add(task)
        await self._session.flush()

    async def save_tool_usage(self, tool_usage: AgentToolUsage) -> None:
        self._session.add(tool_usage)
        await self._session.flush()
