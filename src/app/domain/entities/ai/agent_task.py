"""
Agent Task entity.
"""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.base import ValueObject
from app.domain.entities.ai.agent_execution import AgentExecutionId
from app.domain.enums.ai.agent_task_status import AgentTaskStatus
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class AgentTaskId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class AgentTask(Entity[AgentTaskId]):
    execution_id: AgentExecutionId
    task_name: str
    task_type: str
    status: AgentTaskStatus
    input_data: Optional[dict[str, Any]]
    output_data: Optional[dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    retry_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: CreatedAt
