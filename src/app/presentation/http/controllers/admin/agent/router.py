from typing import List
from fastapi import APIRouter
from app.presentation.http.schemas.admin.agent import AgentRead
from app.domain.enums.agent_type import AgentType

def create_admin_agent_router() -> APIRouter:
    router = APIRouter(prefix="/admin/agents", tags=["admin"])

    @router.get("/", response_model=List[AgentRead])
    async def list_agents():
        return [
            AgentRead(
                type=AgentType.TRADING,
                name="Trading Agent",
                description="Analyzes market trends",
                is_active=True
            ),
            AgentRead(
                type=AgentType.RESEARCH,
                name="Research Agent",
                description="Deep dive into protocols",
                is_active=True
            )
        ]
    return router
