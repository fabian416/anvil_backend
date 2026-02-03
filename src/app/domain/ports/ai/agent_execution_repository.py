from typing import Protocol
from typing import Optional

from app.domain.entities.ai.agent_execution import AgentExecution, AgentExecutionId
from app.domain.entities.ai.agent_task import AgentTask
from app.domain.entities.ai.agent_tool_usage import AgentToolUsage


class AgentExecutionRepository(Protocol):
    async def save_execution(self, execution: AgentExecution) -> None: ...

    async def get_execution_by_id(
        self, id: AgentExecutionId
    ) -> AgentExecution | None: ...

    async def save_task(self, task: AgentTask) -> None: ...

    async def save_tool_usage(self, tool_usage: AgentToolUsage) -> None: ...
