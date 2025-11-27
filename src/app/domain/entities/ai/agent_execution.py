"""
Agent Execution entity.
"""
from dataclasses import dataclass
from typing import Optional, Any
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.entities.ai.llm_conversation import LLMConversationId
from app.domain.enums.ai.agent_execution_status import AgentExecutionStatus
from app.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, repr=False)
class AgentExecutionId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class AgentExecution(Entity[AgentExecutionId]):
    user_id: UserId
    conversation_id: Optional[LLMConversationId]
    agent_type: str
    workflow_type: str
    status: AgentExecutionStatus
    input_params: Optional[dict[str, Any]]
    output_result: Optional[dict[str, Any]]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_cost_usd: Decimal
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: CreatedAt
