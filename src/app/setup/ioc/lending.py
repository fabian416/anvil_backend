"""
Lending Providers for Dependency Injection.

Provides configured lending services following hexagonal architecture:
- Ports → Adapters (Repository, Position Provider)
- Health check monitoring
- Alert generation
- Position tracking
"""

from dishka import Provider, Scope, provide

from app.application.lending.tasks import (
    LendingRepository,
    PositionProvider,
)
from app.infrastructure.adapters.lending.lending_repository_adapter_sqla import (
    LendingRepositoryAdapterSqla,
)
from app.infrastructure.adapters.lending.position_provider_adapter import (
    PositionProviderAdapter,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.mcp.mcp_client import MCPClient


class LendingProvider(Provider):
    """
    Provider for lending operations and monitoring.

    Configures dependency injection for:
    - Lending repository (health checks, alerts, preferences)
    - Position provider (Aave/Morpho position fetching via MCP)
    - MCP client (HTTP client for calling MCP servers)

    Scopes:
    - Repository adapter: REQUEST scope (per-request with AsyncSession)
    - Position provider: APP scope (shared MCP client)
    - MCP client: APP scope (shared HTTP client)

    Architecture:
    - Follows hexagonal architecture (ports → adapters)
    - All methods return protocol interfaces, not concrete types
    - SQLAlchemy adapters injected with AsyncSession from Dishka
    - MCP client injected for protocol position fetching
    """

    # ===== INFRASTRUCTURE LAYER (Ports → Adapters) =====

    @provide(scope=Scope.APP)
    def provide_mcp_client(self) -> MCPClient:
        """
        Provide MCP client for calling MCP servers.

        Creates a shared HTTP client for making requests to MCP servers
        (Aave, Morpho, etc.) running on different ports.

        Returns:
            MCPClient instance configured with default timeout (30s)

        Scope:
            APP scope - shared across all requests for efficiency
        """
        return MCPClient(timeout=30.0)

    @provide(scope=Scope.REQUEST)
    def provide_lending_repository(
        self,
        session: MainAsyncSession,
    ) -> LendingRepository:
        """
        Provide lending repository for health checks, alerts, and preferences.

        Implements LendingRepository protocol using SQLAlchemy
        for PostgreSQL persistence of lending operations.

        Args:
            session: MainAsyncSession from Dishka (injected automatically)

        Returns:
            LendingRepositoryAdapterSqla implementing LendingRepository protocol

        Features:
        - Health check snapshots (lending_health_checks table)
        - Alert management (lending_alerts table)
        - User preferences (user_lending_preferences table)
        - Active position tracking (lending_positions table)
        """
        return LendingRepositoryAdapterSqla(session=session)

    @provide(scope=Scope.APP)
    def provide_position_provider(
        self,
        mcp_client: MCPClient,
    ) -> PositionProvider:
        """
        Provide position provider for fetching positions from protocols.

        Implements PositionProvider protocol using MCP clients
        to fetch positions from Aave (port 8085) and Morpho (port 8088).

        Args:
            mcp_client: MCPClient from Dishka (injected automatically)

        Returns:
            PositionProviderAdapter implementing PositionProvider protocol

        Features:
        - Aave position fetching (supplies, borrows, health factor)
        - Morpho position fetching (supplies only, no borrows)
        - Multi-chain support (Ethereum, Polygon, Arbitrum, etc.)
        - Automatic protocol detection and routing
        """
        return PositionProviderAdapter(
            mcp_client=mcp_client,
            aave_base_url="http://localhost:8085",
            morpho_base_url="http://localhost:8088",
        )
