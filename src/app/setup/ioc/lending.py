"""
Lending Providers for Dependency Injection.

Provides configured lending services following hexagonal architecture:
- Domain services (HealthFactorValidator)
- Application services (Interactors, Query Handlers)
- Ports → Adapters (BalanceChecker, Repository)
"""

from dishka import Provider, Scope, provide

from app.application.lending.interactors.supply_interactor import SupplyInteractor
from app.application.lending.interactors.borrow_interactor import BorrowInteractor
from app.application.lending.query_handlers.health_check_handler import (
    HealthCheckQueryHandler,
)
from app.application.lending.services.health_factor_validator_service import (
    HealthFactorValidatorService,
)
from app.domain.ports.balance_checker import IBalanceChecker
from app.domain.ports.lending_repository import ILendingRepository
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.services.lending.health_factor_validator import HealthFactorValidator
from app.infrastructure.adapters.balance.portfolio_balance_checker import (
    PortfolioBalanceChecker,
)
from app.application.portfolio.portfolio_service import PortfolioService


class LendingProvider(Provider):
    """
    Provider for lending use cases and services.

    Configures dependency injection for:
    - Domain services (pure business logic)
    - Application interactors (use case orchestration)
    - Query handlers (CQRS read operations)
    - Ports → Adapters (infrastructure abstractions)

    Scopes:
    - Domain services: APP scope (singleton)
    - Application services: REQUEST scope (per-request)
    - Infrastructure adapters: APP scope (singleton with caching)
    """

    # ===== DOMAIN LAYER =====

    @provide(scope=Scope.APP)
    def provide_health_factor_validator(self) -> HealthFactorValidator:
        """
        Provide domain service for health factor validation.

        This is pure business logic with NO infrastructure dependencies.
        Safe to use APP scope (singleton) as it's stateless.

        Returns:
            HealthFactorValidator domain service
        """
        return HealthFactorValidator()

    # ===== APPLICATION LAYER =====

    @provide(scope=Scope.REQUEST)
    def provide_health_factor_validator_service(
        self,
        domain_validator: HealthFactorValidator,
        aave_gateway: AaveGateway,
        # price_provider: IPriceProvider,  # TODO: Add when price provider exists
    ) -> HealthFactorValidatorService:
        """
        Provide application service for health factor validation.

        Orchestrates domain validation with infrastructure calls.
        Uses REQUEST scope as it may depend on request-scoped resources.

        Args:
            domain_validator: Domain service for calculations
            aave_gateway: Infrastructure adapter for Aave data

        Returns:
            HealthFactorValidatorService application service
        """
        # TODO: Replace mock price provider with real implementation
        from app.application.lending.services.health_factor_validator_service import IPriceProvider
        from decimal import Decimal

        class MockPriceProvider:
            """Mock price provider until real implementation exists."""

            async def get_price_usd(self, asset: str, chain: str = "ethereum") -> Decimal:
                """Return mock prices for common assets."""
                MOCK_PRICES = {
                    "ETH": Decimal("3700.00"),
                    "WETH": Decimal("3700.00"),
                    "USDC": Decimal("1.00"),
                    "USDT": Decimal("1.00"),
                    "DAI": Decimal("1.00"),
                    "WBTC": Decimal("98000.00"),
                }
                return MOCK_PRICES.get(asset.upper(), Decimal("1.00"))

        # NOTE: This will be replaced with real IPriceProvider implementation
        mock_price_provider = MockPriceProvider()

        return HealthFactorValidatorService(
            domain_validator=domain_validator,
            aave_provider=aave_gateway,
            price_provider=mock_price_provider,  # type: ignore
        )

    @provide(scope=Scope.REQUEST)
    def provide_supply_interactor(
        self,
        balance_checker: IBalanceChecker,
        aave_gateway: AaveGateway,
        morpho_gateway: MorphoGateway,
        repository: ILendingRepository,
    ) -> SupplyInteractor:
        """
        Provide supply interactor for supply operations.

        Orchestrates supply use case with balance validation, protocol
        selection, and position persistence.

        Args:
            balance_checker: Port for checking wallet balances
            aave_gateway: Port for Aave operations
            morpho_gateway: Port for Morpho operations
            repository: Port for position persistence

        Returns:
            SupplyInteractor application service
        """
        return SupplyInteractor(
            balance_checker=balance_checker,
            aave_gateway=aave_gateway,
            morpho_gateway=morpho_gateway,
            repository=repository,
        )

    @provide(scope=Scope.REQUEST)
    def provide_borrow_interactor(
        self,
        hf_validator: HealthFactorValidatorService,
        balance_checker: IBalanceChecker,
        aave_gateway: AaveGateway,
        repository: ILendingRepository,
    ) -> BorrowInteractor:
        """
        Provide borrow interactor for borrow operations.

        Orchestrates borrow use case with health factor validation,
        collateral checks, and position persistence.

        Args:
            hf_validator: Service for health factor validation
            balance_checker: Port for checking wallet balances
            aave_gateway: Port for Aave operations
            repository: Port for position persistence

        Returns:
            BorrowInteractor application service
        """
        return BorrowInteractor(
            hf_validator=hf_validator,
            balance_checker=balance_checker,
            aave_gateway=aave_gateway,
            repository=repository,
        )

    @provide(scope=Scope.REQUEST)
    def provide_health_check_handler(
        self,
        aave_gateway: AaveGateway,
        hf_validator: HealthFactorValidator,
    ) -> HealthCheckQueryHandler:
        """
        Provide query handler for health check queries.

        Handles read-only health factor monitoring queries following CQRS.

        Args:
            aave_gateway: Port for Aave operations
            hf_validator: Domain service for health factor calculations

        Returns:
            HealthCheckQueryHandler query handler
        """
        return HealthCheckQueryHandler(
            aave_gateway=aave_gateway,
            hf_validator=hf_validator,
        )

    # ===== INFRASTRUCTURE LAYER =====

    @provide(scope=Scope.APP)
    def provide_balance_checker(
        self,
        portfolio_service: PortfolioService,
    ) -> IBalanceChecker:
        """
        Provide balance checker adapter.

        Implements IBalanceChecker port using PortfolioService for
        on-chain balance verification.

        Args:
            portfolio_service: Service for fetching on-chain balances

        Returns:
            PortfolioBalanceChecker adapter implementing IBalanceChecker
        """
        return PortfolioBalanceChecker(portfolio_service=portfolio_service)

    @provide(scope=Scope.REQUEST)
    async def provide_lending_repository(
        self,
        session,  # AsyncSession injected by Dishka
    ) -> ILendingRepository:
        """
        Provide lending repository adapter.

        Implements ILendingRepository port using SQLAlchemy for PostgreSQL persistence.
        Uses REQUEST scope to ensure one session per request lifecycle.

        Args:
            session: AsyncSession from Dishka (injected automatically)

        Returns:
            SQLAlchemyLendingRepository adapter implementing ILendingRepository
        """
        from app.infrastructure.persistence_sqla.repositories.lending_repository import (
            SQLAlchemyLendingRepository,
        )

        return SQLAlchemyLendingRepository(session=session)
