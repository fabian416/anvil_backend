"""
Agent Tools Usage entity.
"""
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.base import ValueObject
from app.domain.entities.ai.agent_execution import AgentExecutionId
from app.domain.entities.ai.agent_task import AgentTaskId
from app.domain.enums.ai.agent_tool_status import AgentToolStatus
from app.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, repr=False)
class AgentToolUsageId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class AgentToolUsage(Entity[AgentToolUsageId]):
    execution_id: AgentExecutionId
    task_id: Optional[AgentTaskId]
    tool_name: str
    input_params: Optional[dict[str, Any]]
    output_result: Optional[dict[str, Any]]
    status: AgentToolStatus
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    created_at: CreatedAt
