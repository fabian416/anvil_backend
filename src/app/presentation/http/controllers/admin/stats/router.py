from fastapi import APIRouter
from app.presentation.http.schemas.admin.stats import AdminStats, AgentUsage


def create_admin_stats_router() -> APIRouter:
    router = APIRouter(prefix="/admin/stats", tags=["admin"])

    @router.get("/", response_model=AdminStats)
    async def get_stats():
        return AdminStats(
            active_conversations=10,
            total_messages=150,
            active_agents=5,
            agent_usage=[
                AgentUsage(agent_type="trading", count=50),
                AgentUsage(agent_type="research", count=30),
            ],
        )

    return router
