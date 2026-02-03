from typing import List, Optional
from pydantic import BaseModel

from app.domain.enums.agent_type import AgentType


class AgentRead(BaseModel):
    type: AgentType
    name: str
    description: str
    is_active: bool
