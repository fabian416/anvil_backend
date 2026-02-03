"""Agno Agent IoC Providers.

Provides dependency injection for Agno agents and router.
"""

from dishka import Provider, Scope, provide

from app.infrastructure.agno import AgentRouter
from app.setup.config.agno import AgnoConfig


class AgnoProvider(Provider):
    """Provider for Agno agents."""

    @provide(scope=Scope.APP)
    def get_agno_config(self) -> AgnoConfig:
        """
        Provide Agno configuration.

        Returns:
            AgnoConfig instance
        """
        # TODO: Load from settings/environment
        return AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
            mcp_portfolio_url="http://localhost:8081",
            mcp_oneinch_url="http://localhost:8082",
            mcp_aave_url="http://localhost:8083",
            mcp_defillama_url="http://localhost:8084",
            mcp_manager_url="http://localhost:8080",
        )

    @provide(scope=Scope.APP)
    async def get_agent_router(self, config: AgnoConfig) -> AgentRouter:
        """
        Provide initialized AgentRouter.

        Args:
            config: Agno configuration

        Returns:
            Initialized AgentRouter instance
        """
        router = AgentRouter(config, debug_mode=True)
        await router.initialize()
        return router
