from typing import List
from pydantic import BaseModel


class AgentUsage(BaseModel):
    agent_type: str
    count: int


class AdminStats(BaseModel):
    active_conversations: int
    total_messages: int
    active_agents: int
    agent_usage: List[AgentUsage]
